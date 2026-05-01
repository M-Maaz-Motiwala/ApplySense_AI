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

        # Placeholder ingestion source. Replace with real provider adapters.
        mock_jobs = [
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
        for payload in mock_jobs:
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

        # Stub for Gmail API polling integration.
        task.status = TaskStatus.COMPLETED
        task.result = {"polled_at": datetime.now(tz=timezone.utc).isoformat(), "emails_found": 0}
        db.commit()

    return {"emails_found": 0}
