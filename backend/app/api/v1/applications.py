from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Application, ApplicationStatus, UserProfile, Job
from app.schemas.api import ApplicationResponse, ApproveRejectResponse, RegenerationRequest
from app.tasks.pipeline import generate_application

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
) -> list[ApplicationResponse]:
    from sqlalchemy.orm import selectinload
    rows = (
        await db.execute(
            select(Application)
            .where(Application.user_id == current_user.id)
            .options(selectinload(Application.job))
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

    from sqlalchemy.orm import selectinload
    stmt = (
        select(Application)
        .where(Application.id == application_id)
        .options(selectinload(Application.job))
    )
    application = (await db.execute(stmt)).scalar_one_or_none()
    
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
        "advisor_feedback": application.advisor_feedback,
        "job_title": application.job.title,
        "company": application.job.company,
        "job_url": application.job.source_url,
    }


@router.get("/{application_id}/resume.pdf")
async def get_resume_pdf(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Serve the generated resume PDF file."""
    from app.models import ResumeVersion
    import os

    application = await db.get(Application, application_id)
    if not application or application.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if not application.resume_version_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No resume generated yet")

    resume = await db.get(ResumeVersion, application.resume_version_id)
    if not resume or not resume.pdf_path or not os.path.exists(resume.pdf_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF file not found")

    return FileResponse(
        resume.pdf_path,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"}
    )


@router.post("/{application_id}/regenerate")
async def regenerate_application(
    application_id: UUID,
    request: RegenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Regenerate an application with user-approved skills from the critique."""
    application = await db.get(Application, application_id)
    if not application or application.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    job = await db.get(Job, application.job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Trigger regeneration task
    # We pass the approved skills so the AI knows it can use them
    celery_task = generate_application.delay(
        str(job.id), 
        str(current_user.id), 
        application.match_score,
        approved_skills=request.approved_skills,
        approved_critique=request.approved_critique
    )
    
    return {"task_id": celery_task.id, "status": "processing"}
