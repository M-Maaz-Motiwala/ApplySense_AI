from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ResumeVersion, UserProfile
from app.schemas.api import ResumeResponse

router = APIRouter(prefix="/resumes", tags=["resumes"])


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

from fastapi import UploadFile, File
import json
from app.services.llm.service import LLMService

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
        raise HTTPException(status_code=500, detail="Failed to parse resume via LLM.")
    
    try:
        # Clean up potential markdown formatting from LLM
        clean_json = result["response"].strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:-3]
        elif clean_json.startswith("```"):
            clean_json = clean_json[3:-3]
            
        parsed_data = json.loads(clean_json)
        return parsed_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM returned invalid JSON.")
