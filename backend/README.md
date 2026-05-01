# ApplySense AI - Phase 1 MVP (Backend)

Production-minded MVP backend for agent-assisted job applications.

## Stack
- FastAPI (async APIs)
- PostgreSQL + SQLAlchemy 2.0 (typed models)
- LangGraph (resume + cover/email agents)
- Celery + Redis (async processing + scheduling)

## Quick Start
1. Copy `.env.example` to `.env` and fill secrets.
2. Start infra:
   - `docker compose up -d postgres redis`
   - If `docker compose` is unavailable, use `docker-compose up -d postgres redis`.
3. Install backend:
   - `pip install -e .`
4. Run API:
   - `uvicorn app.main:app --reload`
5. Run worker and beat:
   - `celery -A app.workers.celery_app worker -l info`
   - `celery -A app.workers.celery_app beat -l info`

## Key Endpoints
- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{id}`
- `GET /api/v1/jobs/{id}/match`
- `POST /api/v1/jobs/{id}/generate-application`
- `GET /api/v1/applications`
- `POST /api/v1/applications/{id}/approve`
- `POST /api/v1/applications/{id}/reject`
- `GET /api/v1/resumes/{id}`
- `POST /api/v1/webhook/jobs`
- `POST /api/v1/webhook/emails`
- `GET /api/v1/tasks/{id}`

## Notes
- Human-in-the-loop is enforced through `PENDING_APPROVAL` status before submit/send actions.
- Sensitive PII fields support AES-256 encryption utility for field-level protection.
- LaTeX rendering uses Jinja2 and `pdflatex`; output path is configurable.
- Webhooks are provider-agnostic; n8n is optional and not required.

## Docker
- Backend containerization is available via `backend/docker-compose.yml`.
- Full-stack containerization (backend + worker + beat + frontend + postgres + redis) is available at workspace root `docker-compose.yml`.
- After changing Python dependencies, rebuild images: `docker-compose build --no-cache backend worker beat`.
