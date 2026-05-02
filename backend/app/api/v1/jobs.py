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
    _: UserProfile = Depends(get_current_user),
) -> dict:
    """Manually trigger the background job ingestion task."""
    task = job_ingestion.delay()
    return {"status": "success", "task_id": task.id}


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    _: UserProfile = Depends(get_current_user),
) -> list[JobResponse]:
    rows = (await db.execute(select(Job).order_by(Job.created_at.desc()))).scalars().all()
    return [JobResponse.model_validate(row) for row in rows]


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
