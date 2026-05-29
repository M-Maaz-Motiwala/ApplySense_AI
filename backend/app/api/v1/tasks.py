from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import UserProfile
from app.models.entities import Task
from app.schemas.api import TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
) -> TaskResponse:
    """Get the status of a background task."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    # In a real app, we might check if the task belongs to the user
    # For JOB_INGESTION, it's global or admin, but let's allow users to check tasks they triggered
    return TaskResponse.model_validate(task)
