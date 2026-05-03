from uuid import UUID
import json
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ResumeVersion, UserProfile
from app.schemas.api import ResumeResponse
from app.services.llm.service import LLMService

router = APIRouter(prefix="/resumes", tags=["resumes"])


def _fallback_resume_data(text_content: str) -> dict:
    lines = [line.strip() for line in text_content.splitlines() if line.strip()]
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text_content)
    phone_match = re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", text_content)

    name = lines[0] if lines else ""
    location = lines[1] if len(lines) > 1 and len(lines[1]) < 80 else ""

    return {
        "name": name,
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0) if phone_match else "",
        "location": location,
        "experience_blocks": {
            "education": [{"school": "", "degree": "", "dates": "", "location": "", "CGPA": ""}],
            "coursework": [],
            "experience_level": "Entry Level",
            "experience": [{"company": "", "title": "", "dates": "", "location": "", "bullets": []}],
            "projects": [{"name": "", "tech": "", "date": "", "bullets": []}],
            "leadership": [{"org": "", "dates": "", "title": "", "location": "", "bullets": []}],
            "linkedin": "",
            "github": "",
        },
        "skills_matrix": {
            "languages": [],
            "tools": [],
            "frameworks": [],
        },
    }


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
) -> ResumeResponse:
    resume = await db.get(ResumeVersion, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return ResumeResponse.model_validate(resume)

from fastapi import File, UploadFile

@router.post("/parse")
async def parse_resume(
    file: UploadFile = File(...),
    current_user: UserProfile = Depends(get_current_user)
):
    # In a real scenario, we'd use PyPDF2 or pdfplumber. 
    # For now, we'll read it as string (assuming txt) or just pass a generic prompt if binary.
    content = await file.read()
    try:
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
        text_content = "Binary PDF content (requires PyPDF2 to extract text in production). Simulating extracted text: John Doe, Software Engineer, Python, React."

    service = LLMService()
    prompt = f"""
Parse the following resume text and extract the information into the exact JSON schema provided.
Resume Text: {text_content[:2000]}

Return ONLY valid JSON matching this structure:
{{
  "name": "",
  "email": "",
  "phone": "",
  "location": "",
  "experience_blocks": {{
    "education": [
      {{ "school": "", "degree": "", "dates": "", "location": "", "CGPA": "" }}
    ],
    "coursework": [],
    "experience": [
      {{ "company": "", "title": "", "dates": "", "location": "", "bullets": [] }}
    ],
    "projects": [
      {{ "name": "", "tech": "", "date": "", "bullets": [] }}
    ],
    "linkedin": "",
    "github": ""
  }},
  "skills_matrix": {{
    "languages": [],
    "tools": [],
    "frameworks": []
  }}
}}
"""
    result = await service.generate(prompt)
    if result["status"] == "failed":
        return _fallback_resume_data(text_content)
    
    try:
        # Clean up potential markdown formatting from LLM
        clean_json = (result.get("text") or "").strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:-3]
        elif clean_json.startswith("```"):
            clean_json = clean_json[3:-3]
        clean_json = clean_json.strip()
        if not clean_json:
            raise ValueError("LLM returned empty content.")
            
        parsed_data = json.loads(clean_json)
        return parsed_data
    except (json.JSONDecodeError, ValueError):
        return _fallback_resume_data(text_content)
