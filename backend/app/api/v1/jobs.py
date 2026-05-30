from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Job, UserProfile
from app.schemas.api import JobResponse, MatchInsightResponse
from app.services.matching.engine import match_scoring_engine
from app.tasks.pipeline import generate_application, job_ingestion

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/refresh")
async def trigger_job_refresh(
    db: AsyncSession = Depends(get_db),
    _: UserProfile = Depends(get_current_user),
) -> dict:
    """Manually trigger the background job ingestion task."""
    from app.models.entities import Task, TaskType, TaskStatus
    
    # Create database task record
    task_db = Task(type=TaskType.JOB_INGESTION, status=TaskStatus.PROCESSING, result={})
    db.add(task_db)
    await db.commit()
    await db.refresh(task_db)
    
    # Trigger Celery task with the DB task ID as the Celery task ID
    from app.tasks.pipeline import job_ingestion_v2
    job_ingestion_v2.apply_async(
        kwargs={"task_id": str(task_db.id)},
        task_id=str(task_db.id)
    )
    return {"status": "success", "task_id": str(task_db.id)}


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    recommended: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
) -> list[JobResponse]:
    """List jobs with an optional 'recommended' filter based on user profile."""
    import logging
    from datetime import datetime, timedelta, timezone
    logger = logging.getLogger(__name__)
    
    one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)
    stmt = select(Job).where(Job.created_at >= one_month_ago).order_by(Job.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    
    candidate_jobs = rows
    if recommended:
        candidate_jobs = []
        for job in rows:
            # 1. Role Match (Strict)
            role_match = any(role.lower() in job.title.lower() for role in current_user.desired_roles)
            
            # 2. Location/Domain Match (Context)
            location_match = (current_user.location and job.location and 
                             (current_user.location.lower() in job.location.lower() or 
                              job.location.lower() in current_user.location.lower()))
            
            domain_match = any(domain.lower() in (job.raw_text_jd or "").lower() for domain in current_user.desired_domains)
            
            # 3. Experience Match
            requirements = job.parsed_requirements if isinstance(job.parsed_requirements, dict) else {}
            job_exp = requirements.get("experience_years")
            exp_match = True
            if job_exp is not None and current_user.experience_years is not None:
                try:
                    # Match if user has at least (job_required - 2) years of experience
                    exp_match = (float(current_user.experience_years) >= float(job_exp) - 2)
                except (ValueError, TypeError):
                    exp_match = True # Fallback to permissive match on parse error
            
            # To be "Relevant", it MUST match the role and experience, and ideally the location or domain
            if role_match and exp_match and (location_match or domain_match or not current_user.location):
                logger.info(f"MATCH: '{job.title}' for {current_user.email} (Role: {role_match}, Exp: {exp_match})")
                candidate_jobs.append(job)
            else:
                logger.debug(f"SKIP: '{job.title}' for {current_user.email}")
            
    results = []
    for job in candidate_jobs:
        insight = await match_scoring_engine.calculate(current_user, job)
        job_res = JobResponse.model_validate(job)
        job_res.match_score = insight["score"]
        job_res.advisor = insight.get("advisor")
        results.append(job_res)
        
    results.sort(key=lambda x: x.match_score or 0.0, reverse=True)
    return results


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UserProfile = Depends(get_current_user),
) -> JobResponse:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse.model_validate(job)


@router.get("/{job_id}/match", response_model=MatchInsightResponse)
async def job_match_insight(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
) -> MatchInsightResponse:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    insight = await match_scoring_engine.calculate(current_user, job)
    return MatchInsightResponse(**insight)


@router.post("/{job_id}/generate-application")
async def trigger_application_generation(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    insight = await match_scoring_engine.calculate(current_user, job)
    celery_task = generate_application.delay(str(job_id), str(current_user.id), insight["score"])
    return {"task_id": celery_task.id, "score": insight["score"]}
