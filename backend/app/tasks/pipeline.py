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
    import asyncio
    import logging
    import httpx
    from bs4 import BeautifulSoup
    from app.services.llm.service import LLMService

    logger = logging.getLogger(__name__)
    task = Task(type=TaskType.JOB_INGESTION, status=TaskStatus.PROCESSING, result={})
    
    with SyncSessionLocal() as db:
        db.add(task)
        db.commit()
        db.refresh(task)

        users = db.execute(select(UserProfile)).scalars().all()
        if not users:
            logger.warning("No users found for job ingestion.")
            task.status = TaskStatus.COMPLETED
            db.commit()
            return {"inserted": 0}

        # Collect unique search queries from users
        search_queries = set()
        llm = LLMService()
        
        for user in users:
            # Construct a context for the LLM to generate a search query
            context = {
                "roles": user.desired_roles,
                "domains": user.desired_domains,
                "experience_level": user.experience_blocks.get("experience_level", ""),
                "skills": user.skills_matrix,
                "top_experience": user.experience_blocks.get("experience", [{}])[0].get("title", ""),
                "coursework": user.experience_blocks.get("coursework", []),
                "tech": user.experience_blocks.get("projects", [{}])[0].get("tech", "")
            }
            
            prompt = f"""
            Based on the following user profile context, generate exactly ONE highly optimized job search query string (2-4 words) that would return the most relevant job results on a job board.
            Return ONLY the query string, nothing else.
            
            Context: {context}
            """
            try:
                # Use sync wrapper for LLM call
                result = asyncio.run(llm.generate(prompt))
                if result["status"] == "success":
                    query = result["text"].strip().replace('"', '')
                    if query:
                        search_queries.add(query)
                else:
                    # Fallback to desired roles
                    for role in user.desired_roles:
                        search_queries.add(role)
            except Exception as e:
                logger.error(f"LLM query generation failed for user {user.id}: {e}")
                for role in user.desired_roles:
                    search_queries.add(role)

        if not search_queries:
            search_queries.add("Software Engineer")

        total_inserted = 0
        fetched_job_ids = set()

        for query in search_queries:
            logger.info(f"Searching jobs for query: {query}")
            url = f"https://www.themuse.com/api/public/jobs?category=Software%20Engineer&page=1&level={query}" 
            # Note: TheMuse API level filter is specific, but we'll use query as a generic search term if possible.
            # Since TheMuse API is limited, let's just use it as a keyword in the URL if supported, or just log it.
            # For this demo, we'll try to use it as a category or similar.
            
            # Re-fetch with query
            encoded_query = query.replace(" ", "%20")
            search_url = f"https://www.themuse.com/api/public/jobs?category={encoded_query}&page=1"
            
            try:
                with httpx.Client() as client:
                    response = client.get(search_url, timeout=15.0)
                    if response.status_code == 404:
                        # Try generic search if category fails
                        search_url = f"https://www.themuse.com/api/public/jobs?page=1&category=Software%20Engineer"
                        response = client.get(search_url, timeout=15.0)
                    
                    response.raise_for_status()
                    data = response.json()
                
                for item in data.get("results", []):
                    ext_id = str(item.get("id"))
                    if ext_id in fetched_job_ids:
                        continue
                        
                    raw_html = item.get("contents", "")
                    soup = BeautifulSoup(raw_html, "html.parser")
                    raw_text = soup.get_text(separator="\n", strip=True)
                    
                    locations = item.get("locations", [])
                    location_name = locations[0].get("name") if locations else "Remote"
                    
                    payload = {
                        "external_job_id": ext_id,
                        "title": item.get("name", "Software Engineer"),
                        "company": item.get("company", {}).get("name", "Unknown"),
                        "location": location_name,
                        "raw_text_jd": raw_text,
                        "parsed_requirements": {"skills": []},
                        "source": "TheMuse",
                        "source_url": item.get("refs", {}).get("landing_page", ""),
                    }
                    
                    existing = db.execute(
                        select(Job).where(
                            Job.external_job_id == payload["external_job_id"],
                            Job.source == payload["source"],
                        )
                    ).scalar_one_or_none()
                    
                    if not existing:
                        db.add(Job(**payload))
                        total_inserted += 1
                        fetched_job_ids.add(ext_id)
                        
            except Exception as e:
                logger.error(f"Failed to fetch jobs for query '{query}': {e}")

        db.commit()
        task.status = TaskStatus.COMPLETED
        task.result = {"inserted": total_inserted, "queries_ran": list(search_queries)}
        db.commit()

    match_and_queue.delay()
    return {"inserted": total_inserted}


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
