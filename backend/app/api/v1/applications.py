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


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
) -> ApplicationResponse:
    """Get a single application with all its generated content for review."""
    application = await db.get(Application, application_id)
    if not application or application.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return ApplicationResponse.model_validate(application)


@router.delete("/{application_id}", status_code=status.HTTP_200_OK)
async def discard_application(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Discard (permanently delete) a generated application the user doesn't want."""
    application = await db.get(Application, application_id)
    if not application or application.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if application.status not in (ApplicationStatus.PENDING_APPROVAL, ApplicationStatus.DRAFT):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending/draft applications can be discarded",
        )

    await db.delete(application)
    await db.commit()
    return {"detail": "Application discarded successfully", "application_id": str(application_id)}


@router.get("/{application_id}/preview-resume")
async def preview_resume(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Preview the generated resume LaTeX source and PDF path before approving."""
    from app.models import ResumeVersion

    application = await db.get(Application, application_id)
    if not application or application.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if not application.resume_version_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No resume generated yet")

    resume = await db.get(ResumeVersion, application.resume_version_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found")

    return {
        "application_id": str(application.id),
        "status": application.status.value,
        "match_score": application.match_score,
        "cover_letter_text": application.cover_letter_text,
        "email_draft": application.email_draft,
        "resume_latex_source": resume.latex_source,
        "resume_pdf_path": resume.pdf_path,
    }
