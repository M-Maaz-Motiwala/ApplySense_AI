# ApplySense AI - Phase 1 MVP (Backend)

Production-minded MVP backend for agent-assisted job applications.

## Stack
- **FastAPI**: Async APIs for frontend interaction.
- **PostgreSQL + SQLAlchemy 2.0**: Typed models and persistent storage.
- **LangGraph**: Sophisticated agent orchestration for resume and email generation.
- **Celery + Redis**: Distributed task queue for long-running ingestion and processing.
- **Ollama Cloud**: LLM provider for web search, scraping, and matching.

## Architecture & Workflows

### 1. Job Ingestion Workflow
This multi-phase pipeline finds and imports relevant jobs from the web using LLMs and stealth search techniques.
- **Trigger**: Celery Beat (cron) or Manual via `POST /api/v1/jobs/refresh`.
- **Flow Phases**:
    1.  **Query Generation (LLM)**: `LLMService` analyzes the User Profile (role, location, skills) and generates 5+ high-intent search queries.
    2.  **Link Gathering (Search Engine)**: `JobSearcher` uses **DuckDuckGo Lite** with randomized delays and User-Agent rotation to find job links on LinkedIn, Indeed, Naukri, etc.
    3.  **Scraping (Web Scraper)**: `JobScraper` visits each gathered URL, handling protocol-relative links and extracting clean markdown/text content.
    4.  **Parsing (LLM Orchestration)**: `LLMService` parses the raw scraped text into a structured `Job` schema (extracting title, company, skills, etc.).
    5.  **Persistence**: The structured job is saved to the `jobs` table in PostgreSQL, preventing duplicates via external job IDs.

### 2. Matching & Queueing Workflow
Pairs users with newly ingested jobs based on relevance.
- **Trigger**: Automatically after Job Ingestion completes.
- **Flow**:
    1. `app.tasks.pipeline:match_and_queue` scans all users and jobs.
    2. `app.services.matching.engine:match_scoring_engine.calculate` uses LLM embeddings/analysis to generate a match score.
    3. If score >= `MATCH_THRESHOLD`, it triggers `generate_application.delay()`.

### 3. Application Generation Workflow
Generates tailored resumes and cover letters for a specific job.
- **Trigger**: Matching engine or Manual via `POST /api/v1/jobs/{id}/generate-application`.
- **Flow**:
    1. `app.tasks.pipeline:generate_application` is invoked.
    2. `app.services.langgraph.resume_graph:resume_graph.invoke` optimizes the resume JSON for the job description.
    3. `app.services.latex.renderer:latex_renderer.render_and_compile` generates a PDF using Jinja2 templates and `pdflatex`.
    4. `app.services.langgraph.cover_email_graph:cover_email_graph.invoke` generates a personalized cover letter and recruiter email.
    5. An `Application` record is created with `PENDING_APPROVAL` status.

### 4. Email Monitoring Workflow
Tracks recruiter responses via Gmail.
- **Trigger**: Celery Beat (cron).
- **Flow**:
    1. `app.tasks.pipeline:email_monitoring` connects to Gmail API.
    2. Scans for unread messages from recruiters.
    3. Updates `Application` status if responses are found (e.g., to `INTERVIEW`).

## Quick Start
1. Copy `.env.example` to `.env` and fill secrets.
2. Start infra:
   - `docker compose up -d postgres redis`
3. Install backend:
   - `pip install -e .`
4. Seed test data:
   - `export PYTHONPATH=$PYTHONPATH:.`
   - `python scripts/seed_john_doe.py`
   - `python scripts/seed_jane_smith.py`
5. Run API:
   - `uvicorn app.main:app --reload`
6. Run worker and beat:
   - `celery -A app.workers.celery_app worker -l info`
   - `celery -A app.workers.celery_app beat -l info`

## Key Endpoints
- `GET /api/v1/jobs`: List ingested jobs.
- `POST /api/v1/jobs/refresh`: Manually trigger job ingestion.
- `GET /api/v1/jobs/{id}/match`: Get real-time match insight for current user.
- `POST /api/v1/jobs/{id}/generate-application`: Trigger resume/cover letter generation.
- `POST /api/v1/applications/{id}/approve`: Approve a generated application for submission.
- `GET /api/v1/tasks/{id}`: Track status of background tasks.

## Notes
- **Human-in-the-loop**: All applications require manual approval before final submission.
- **Security**: PII fields (phone, etc.) are AES-256 encrypted in the database.
- **LaTeX**: Ensure `texlive-full` or equivalent is installed for PDF generation.

## Testing the Workflow

### Automated Integration Test
A comprehensive test script is provided to verify the complete flow (Login -> Ingest -> Match).
```bash
docker exec -it appliesense_ai-backend-1 python scripts/test_ingestion_workflow.py
```

### Manual Testing with CURL

**1. Login as Jane Smith**
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "jane@example.com", "password": "password123"}' | jq -r .access_token)
```

**2. Trigger Job Refresh**
```bash
TASK_ID=$(curl -s -X POST http://localhost:8000/api/v1/jobs/refresh \
  -H "Authorization: Bearer $TOKEN" | jq -r .task_id)
```

**3. Monitor Task Status**
```bash
curl -s -X GET http://localhost:8000/api/v1/tasks/$TASK_ID \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**4. View Results & Matching**
```bash
# List jobs
curl -s -X GET http://localhost:8000/api/v1/jobs -H "Authorization: Bearer $TOKEN" | jq .

# Get match score for the first job
JOB_ID=$(curl -s -X GET http://localhost:8000/api/v1/jobs -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')
curl -s -X GET http://localhost:8000/api/v1/jobs/$JOB_ID/match -H "Authorization: Bearer $TOKEN" | jq .
```

## Docker
- Backend containerization is available via `backend/Dockerfile`.
- Full-stack containerization (backend + worker + beat + frontend + postgres + redis) is available at workspace root `docker-compose.yml`.
