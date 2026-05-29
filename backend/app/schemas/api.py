from datetime import datetime
from uuid import UUID

from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.models import ApplicationStatus, TaskStatus, TaskType, UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserCreateRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str | None = None
    location: str | None = None
    experience_years: float | None = None
    desired_roles: list[str] = []
    desired_domains: list[str] = []
    salary_expectation: float | None = None
    experience_blocks: dict = {}
    skills_matrix: dict = {}
    role: UserRole = UserRole.USER


class UserUpdateRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    location: str | None = None
    experience_years: float | None = None
    desired_roles: list[str] | None = None
    desired_domains: list[str] | None = None
    salary_expectation: float | None = None
    experience_blocks: dict | None = None
    skills_matrix: dict | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    role: UserRole
    phone: str | None
    location: str | None
    experience_years: float | None
    desired_roles: list[str]
    desired_domains: list[str]
    salary_expectation: float | None
    experience_blocks: dict
    skills_matrix: dict
    created_at: datetime


class JobCreate(BaseModel):
    external_job_id: str
    title: str
    company: str
    location: str | None = None
    raw_text_jd: str
    parsed_requirements: dict = {}
    source: str
    source_url: str | None = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_job_id: str
    title: str
    company: str
    location: str | None
    raw_text_jd: str
    parsed_requirements: dict
    source: str
    source_url: str | None
    created_at: datetime

    @field_validator("parsed_requirements", mode="before")
    @classmethod
    def validate_requirements(cls, v: Any) -> dict:
        if isinstance(v, list):
            return {}
        if v is None:
            return {}
        return v


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    job_id: UUID
    latex_source: str
    pdf_path: str
    created_at: datetime


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    job_id: UUID
    status: ApplicationStatus
    match_score: float
    resume_version_id: UUID | None
    cover_letter_text: str | None
    email_draft: str | None
    recruiter_email: str | None
    applied_at: datetime | None
    last_updated: datetime
    follow_up_required: bool
    advisor_feedback: dict
    job: JobResponse | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: TaskType
    status: TaskStatus
    result: dict
    created_at: datetime


class MatchInsightResponse(BaseModel):
    score: float
    reason: str
    advisor: dict = {}


class WebhookJobsPayload(BaseModel):
    jobs: list[JobCreate]


class WebhookEmailPayload(BaseModel):
    thread_id: str | None = None
    from_email: str
    subject: str
    body: str
    received_at: datetime | None = None


class ApproveRejectResponse(BaseModel):
    application_id: UUID
    status: ApplicationStatus


class RegenerationRequest(BaseModel):
    approved_skills: list[str] = []
    approved_critique: list[str] = []
