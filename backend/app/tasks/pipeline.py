from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.db.sync_session import SyncSessionLocal
from app.models import (
    Application,
    ApplicationStatus,
    Job,
    ResumeVersion,
    Task,
    TaskStatus,
    TaskType,
    UserProfile,
)
from app.services.langgraph.cover_email_graph import cover_email_graph
from app.services.langgraph.resume_graph import resume_graph
from app.services.latex.renderer import latex_renderer
from app.services.matching.engine import match_scoring_engine
from app.workers.celery_app import celery_app


@celery_app.task(name="app.tasks.pipeline.job_ingestion")
def job_ingestion() -> dict:
    task = Task(type=TaskType.JOB_INGESTION, status=TaskStatus.PROCESSING, result={})
    with SyncSessionLocal() as db:
        db.add(task)
        db.commit()
        db.refresh(task)

        import httpx
        from bs4 import BeautifulSoup
        import logging
        logger = logging.getLogger(__name__)

        url = "https://www.themuse.com/api/public/jobs?category=Software%20Engineer&page=1"
        fetched_jobs = []
        try:
            with httpx.Client() as client:
                response = client.get(url, timeout=15.0)
                response.raise_for_status()
                data = response.json()
            
            for item in data.get("results", []):
                raw_html = item.get("contents", "")
                soup = BeautifulSoup(raw_html, "html.parser")
                raw_text = soup.get_text(separator="\n", strip=True)
                
                locations = item.get("locations", [])
                location_name = locations[0].get("name") if locations else "Remote"
                
                fetched_jobs.append({
                    "external_job_id": str(item.get("id")),
                    "title": item.get("name", "Software Engineer"),
                    "company": item.get("company", {}).get("name", "Unknown"),
                    "location": location_name,
                    "raw_text_jd": raw_text,
                    "parsed_requirements": {"skills": []}, # Let LangGraph handle parsing later
                    "source": "TheMuse",
                    "source_url": item.get("refs", {}).get("landing_page", ""),
                })
        except Exception as e:
            logger.error(f"Failed to fetch jobs from The Muse API: {e}")
            fetched_jobs = [
                {
                    "external_job_id": "li-001",
                    "title": "Senior Python Backend Engineer",
                    "company": "Acme AI",
                    "location": "Remote",
                    "raw_text_jd": "Looking for 5+ years Python, FastAPI, PostgreSQL, ML systems.",
                    "parsed_requirements": {"skills": ["Python", "FastAPI", "PostgreSQL", "ML"]},
                    "source": "LinkedIn",
                    "source_url": "https://linkedin.example/job/li-001",
                }
            ]

        inserted = 0
        for payload in fetched_jobs:
            existing = db.execute(
                select(Job).where(
                    Job.external_job_id == payload["external_job_id"],
                    Job.source == payload["source"],
                )
            ).scalar_one_or_none()
            if existing:
                continue
            db.add(Job(**payload))
            inserted += 1

        db.commit()

        task.status = TaskStatus.COMPLETED
        task.result = {"inserted": inserted}
        db.commit()

    match_and_queue.delay()
    return {"inserted": inserted}


@celery_app.task(name="app.tasks.pipeline.match_and_queue")
def match_and_queue() -> dict:
    task = Task(type=TaskType.MATCHING, status=TaskStatus.PROCESSING, result={})
    with SyncSessionLocal() as db:
        db.add(task)
        db.commit()
        db.refresh(task)

        users = db.execute(select(UserProfile)).scalars().all()
        jobs = db.execute(select(Job)).scalars().all()

        queued = 0
        for user in users:
            for job in jobs:
                insight = _sync_calculate_match(user, job)
                if insight["score"] >= 70:
                    generate_application.delay(str(job.id), str(user.id), insight["score"])
                    queued += 1

        task.status = TaskStatus.COMPLETED
        task.result = {"queued": queued}
        db.commit()
    return {"queued": queued}


def _sync_calculate_match(user: UserProfile, job: Job) -> dict:
    import asyncio

    return asyncio.run(match_scoring_engine.calculate(user, job))


@celery_app.task(name="app.tasks.pipeline.generate_application")
def generate_application(job_id: str, user_id: str, match_score: float) -> dict:
    task = Task(type=TaskType.RESUME_GENERATION, status=TaskStatus.PROCESSING, result={})

    with SyncSessionLocal() as db:
        db.add(task)
        db.commit()
        db.refresh(task)

        job = db.get(Job, UUID(job_id))
        user = db.get(UserProfile, UUID(user_id))
        if not job or not user:
            task.status = TaskStatus.FAILED
            task.result = {"error": "job or user not found"}
            db.commit()
            return {"status": "failed"}

        from app.core.encryption import decrypt_value
        decrypted_phone = decrypt_value(user.phone) if user.phone else ""

        resume_state = resume_graph.invoke(
            {
                "user_profile": {
                    "name": user.name,
                    "email": user.email,
                    "phone": decrypted_phone,
                    "location": user.location or "",
                    "linkedin": user.experience_blocks.get("linkedin", ""),
                    "github": user.experience_blocks.get("github", ""),
                    "experience_blocks": user.experience_blocks,
                    "skills_matrix": user.skills_matrix,
                },
                "job_description": job.raw_text_jd,
            }
        )
        latex_result = latex_renderer.render_and_compile(resume_state["optimized_json"], user_id=str(user.id), job_id=str(job.id))
        resume_version = ResumeVersion(
            user_id=user.id,
            job_id=job.id,
            latex_source=latex_result["latex_source"],
            pdf_path=latex_result["pdf_path"],
        )
        db.add(resume_version)
        db.commit()
        db.refresh(resume_version)

        email_state = cover_email_graph.invoke(
            {
                "user_profile": {
                    "name": user.name,
                    "email": user.email,
                },
                "job_description": job.raw_text_jd,
                "company_info": {"name": job.company, "role": job.title},
            }
        )

        from pathlib import Path
        output_dir = Path(latex_result["output_dir"])
        cover_letter_file = output_dir / "coverletter.txt"
        cover_letter_file.write_text(email_state["cover_letter_text"], encoding="utf-8")

        application = Application(
            user_id=user.id,
            job_id=job.id,
            status=ApplicationStatus.PENDING_APPROVAL,
            match_score=match_score,
            resume_version_id=resume_version.id,
            cover_letter_text=email_state["cover_letter_text"],
            email_draft=email_state["recruiter_email_draft"],
            recruiter_email=None,
            follow_up_required=False,
        )
        db.add(application)
        db.flush()

        task.status = TaskStatus.COMPLETED
        task.result = {
            "application_id": str(application.id),
            "resume_version_id": str(resume_version.id),
            "status": ApplicationStatus.PENDING_APPROVAL.value,
        }
        db.commit()

    return {"status": "created"}


@celery_app.task(name="app.tasks.pipeline.email_monitoring")
def email_monitoring() -> dict:
    task = Task(type=TaskType.EMAIL_MONITORING, status=TaskStatus.PROCESSING, result={})
    with SyncSessionLocal() as db:
        db.add(task)
        db.commit()
        db.refresh(task)

        import logging
        import os.path
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from app.core.config import get_settings

        logger = logging.getLogger(__name__)
        settings = get_settings()

        SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
        creds = None
        
        # In a real app, you would load these securely or manage tokens per-user.
        # This implementation scans the system admin's mailbox for configured credentials.
        token_path = "token.json"
        
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh Gmail token: {e}")
                    creds = None
            
            if not creds and settings.gmail_credentials_json and os.path.exists(settings.gmail_credentials_json):
                # NOTE: This requires user interaction on first run, which doesn't work in Celery.
                # In production, the token.json should be pre-generated.
                logger.warning("No valid Gmail token found. Need manual OAuth flow.")
        
        emails_found = 0
        if creds:
            try:
                service = build("gmail", "v1", credentials=creds)
                
                # Fetch pending applications to look for replies
                pending_apps = db.execute(
                    select(Application).where(Application.status == ApplicationStatus.SUBMITTED)
                ).scalars().all()
                
                # Simple logic: query for unread messages
                results = service.users().messages().list(userId="me", labelIds=["UNREAD"], maxResults=10).execute()
                messages = results.get("messages", [])
                
                emails_found = len(messages)
                
                for message in messages:
                    msg = service.users().messages().get(userId="me", id=message["id"]).execute()
                    # In a fully built system, we would parse headers, match with application emails,
                    # and use LLM to classify if it's an INTERVIEW or REJECTION.
                    logger.info(f"Found unread email: {msg['snippet']}")
                    
            except Exception as e:
                logger.error(f"Gmail API error: {e}")

        task.status = TaskStatus.COMPLETED
        task.result = {"polled_at": datetime.now(tz=timezone.utc).isoformat(), "emails_found": emails_found}
        db.commit()

    return {"emails_found": emails_found}
