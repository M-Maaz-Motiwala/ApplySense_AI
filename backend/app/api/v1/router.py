from fastapi import APIRouter

from app.api.v1.applications import router as applications_router
from app.api.v1.auth import router as auth_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.resumes import router as resumes_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.webhooks import router as webhooks_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(jobs_router)
api_router.include_router(applications_router)
api_router.include_router(resumes_router)
api_router.include_router(webhooks_router)
api_router.include_router(tasks_router)
