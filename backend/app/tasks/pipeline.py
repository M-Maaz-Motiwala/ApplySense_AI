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
def job_ingestion(task_id: str | None = None) -> dict:
    import asyncio
    import logging
    from app.services.llm.service import LLMService
    from app.services.ingestion.search import job_searcher
    from app.services.ingestion.scraper import job_scraper
    from app.core.config import get_settings
    from uuid import UUID

    logger = logging.getLogger(__name__)
    settings = get_settings()
    
    with SyncSessionLocal() as db:
        if task_id:
            task = db.get(Task, UUID(task_id))
            if task:
                task.status = TaskStatus.PROCESSING
                db.commit()
        else:
            task = Task(type=TaskType.JOB_INGESTION, status=TaskStatus.PROCESSING, result={})
            db.add(task)
            db.commit()
            db.refresh(task)

        users = db.execute(select(UserProfile)).scalars().all()
        if not users:
            logger.warning("No users found for job ingestion.")
            task.status = TaskStatus.COMPLETED
            db.commit()
            return {"inserted": 0}

        llm = LLMService()
        total_inserted = 0
        all_job_links = set()
        
        # Step 1: Generate search queries for each user and gather links
        for user in users:
            user_context = {
                "name": user.name,
                "location": user.location,
                "experience_years": user.experience_years,
                "desired_roles": user.desired_roles,
                "desired_domains": user.desired_domains,
            }
            
            logger.info(f"Generating search queries for user: {user.email}")
            queries = asyncio.run(llm.generate_search_queries(
                user_context, 
                model=settings.ollama_model
            ))
            
            # Combine queries with country/location if not already present
            location_suffix = f" in {user.location}" if user.location else ""
            enhanced_queries = []
            
            # Cap at 3 queries to avoid long wait times
            for i, query in enumerate(queries[:3]):
                if not isinstance(query, str):
                    continue
                full_query = f"{query}{location_suffix}"
                
                # Only add site-specific variations for the top query to save time
                if i < 1 and "site:" not in full_query:
                    enhanced_queries.append(f"site:linkedin.com/jobs/view {full_query}")
                    enhanced_queries.append(f"site:naukrigulf.com {full_query}")
                
                enhanced_queries.append(full_query)
            
            logger.info(f"Searching jobs for {user.email} with {len(enhanced_queries)} optimized queries")
            user_links = asyncio.run(job_searcher.get_job_links(enhanced_queries))
            all_job_links.update(user_links)

        logger.info(f"Found {len(all_job_links)} unique job links to process")

        # Step 2: Scrape and parse each job link in parallel
        links_to_process = list(all_job_links)[:20]
        logger.info(f"Found {len(all_job_links)} unique job links. Processing top {len(links_to_process)} in parallel...")
        
        async def scrape_all():
            async def process_single_link(link_url):
                try:
                    return await job_scraper.process_job_link(link_url)
                except Exception as e:
                    logger.error(f"Failed to process {link_url}: {e}")
                    return None
            
            # Run with a safety timeout so one stuck link doesn't kill the whole ingestion
            try:
                return await asyncio.wait_for(
                    asyncio.gather(*[process_single_link(l) for l in links_to_process]),
                    timeout=60.0
                )
            except asyncio.TimeoutError:
                logger.warning("Parallel scraping timed out after 60s. Moving forward with available results.")
                return [] # Or we could try to get partial results, but [] is safer for now

        # Run the parallel scraper wrapper
        results = asyncio.run(scrape_all())
        
        total_inserted = 0
        processed_jobs = []
        for job_data in results:
            if not job_data or not job_data.get("title"):
                continue
            
            # 1. ROBUST FALLBACKS
            job_title = job_data.get("title", "Unknown Title")
            job_company = job_data.get("company") or "Unknown Company"
            job_location = job_data.get("location") or "Remote"
                
            try:
                # Step 3: Filter and save jobs
                # Check for existing
                existing = db.execute(
                    select(Job).where(
                        Job.external_job_id == job_data["external_job_id"],
                        Job.source == job_data["source"],
                    )
                ).scalar_one_or_none()
                
                if not existing:
                    # Step 3: Profile-based Filtering
                    is_relevant = False
                    for user in users:
                        # Fallback: if user has NO roles or domains specified, consider all jobs in their location relevant
                        user_roles = user.desired_roles or []
                        user_domains = user.desired_domains or []
                        
                        if not user_roles and not user_domains:
                            if user.location and user.location.lower() in job_location.lower():
                                is_relevant = True
                                logger.info(f"Job {job_title} accepted as location match for {user.email}")
                                break
                            elif not user.location:
                                is_relevant = True # Fully blank profile -> accept all
                                break

                        # 2. SEMANTIC KEYWORD EXPANSION
                        # Check if any user role is a substring of the job title or vice-versa
                        role_match = any(
                            role.lower() in job_title.lower() or job_title.lower() in role.lower() 
                            for role in user_roles
                        )
                        
                        # Skill match (check if job title mentions any of user's key skills)
                        # Extract all skill names from user's skills_matrix
                        all_user_skills = []
                        if isinstance(user.skills_matrix, dict):
                            # Recursively get all strings from the matrix values
                            def get_strings(d):
                                if isinstance(d, list):
                                    for item in d:
                                        if isinstance(item, str): all_user_skills.append(item.lower())
                                elif isinstance(d, dict):
                                    for v in d.values(): get_strings(v)
                            get_strings(user.skills_matrix)
                        
                        skill_match = any(
                            skill in job_title.lower() for skill in all_user_skills if len(skill) > 2
                        )

                        # Domain match (check title and summary)
                        domain_match = any(
                            domain.lower() in job_title.lower() or 
                            domain.lower() in (job_data.get("summary", "") or "").lower() 
                            for domain in user_domains
                        )
                        
                        if role_match or domain_match or skill_match:
                            is_relevant = True
                            logger.info(f"Job {job_title} matched for {user.email} (Role: {role_match}, Domain: {domain_match}, Skill: {skill_match})")
                            break
                    
                    if not is_relevant:
                        logger.info(f"Skipping job {job_title} at {job_company} - no match for any user profile")
                        continue

                    summary = job_data.get("summary") or ""
                    raw_text = job_data.get("raw_text") or job_title
                    
                    new_job = Job(
                        external_job_id=job_data["external_job_id"],
                        title=job_title,
                        company=job_company,
                        location=job_location,
                        raw_text_jd=f"{summary}\n\n{raw_text}",
                        parsed_requirements={
                            "skills": job_data.get("skills", []),
                            "experience_years": job_data.get("experience_years"),
                            "country": job_data.get("country"),
                            "domain": job_data.get("domain")
                        },
                        source=job_data["source"],
                        source_url=job_data["source_url"],
                    )
                    db.add(new_job)
                    total_inserted += 1
                    processed_jobs.append(job_title)

            except Exception as e:
                logger.error(f"Error saving job: {e}")

        db.commit()
        task.status = TaskStatus.COMPLETED
        task.result = {"inserted": total_inserted, "processed_titles": processed_jobs}
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
