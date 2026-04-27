from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import Job, UserProfile
from app.schemas.api import WebhookEmailPayload, WebhookJobsPayload
from app.tasks.pipeline import match_and_queue

router = APIRouter(prefix="/webhook", tags=["webhooks"])


@router.post("/jobs")
async def webhook_jobs(
    payload: WebhookJobsPayload,
    db: AsyncSession = Depends(get_db),
    _: UserProfile = Depends(require_admin),
) -> dict:
    inserted = 0
    for item in payload.jobs:
        existing = await db.scalar(
            select(Job).where(Job.external_job_id == item.external_job_id, Job.source == item.source)
        )
        if existing:
            continue
        db.add(Job(**item.model_dump()))
        inserted += 1

    await db.commit()
    celery_task = match_and_queue.delay()
    return {"inserted": inserted, "queued_task_id": celery_task.id}


@router.post("/emails")
async def webhook_emails(
    payload: WebhookEmailPayload,
    _: UserProfile = Depends(require_admin),
) -> dict:
    # Placeholder for inbound email parsing and application status updates.
    return {"status": "received", "subject": payload.subject}
