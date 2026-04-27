from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Application, ApplicationStatus, UserProfile
from app.schemas.api import ApplicationResponse, ApproveRejectResponse

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
) -> list[ApplicationResponse]:
    rows = (
        await db.execute(
            select(Application)
            .where(Application.user_id == current_user.id)
            .order_by(Application.last_updated.desc())
        )
    ).scalars().all()
    return [ApplicationResponse.model_validate(row) for row in rows]


@router.post("/{application_id}/approve", response_model=ApproveRejectResponse)
async def approve_application(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
) -> ApproveRejectResponse:
    application = await db.get(Application, application_id)
    if not application or application.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if application.status != ApplicationStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending applications can be approved")

    application.status = ApplicationStatus.APPROVED
    application.applied_at = datetime.now(tz=timezone.utc)
    await db.commit()
    return ApproveRejectResponse(application_id=application.id, status=application.status)


@router.post("/{application_id}/reject", response_model=ApproveRejectResponse)
async def reject_application(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
) -> ApproveRejectResponse:
    application = await db.get(Application, application_id)
    if not application or application.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if application.status != ApplicationStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending applications can be rejected")

    application.status = ApplicationStatus.REJECTED
    await db.commit()
    return ApproveRejectResponse(application_id=application.id, status=application.status)
