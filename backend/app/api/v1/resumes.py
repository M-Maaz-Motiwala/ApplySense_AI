from uuid import UUID
import json
import re
import io
from pypdf import PdfReader

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
        "desired_roles": [],
        "desired_domains": [],
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
    text_content = ""
    
    if file.filename.lower().endswith('.pdf'):
        try:
            pdf_reader = PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_content += extracted + "\n"
        except Exception as e:
            text_content = f"Error extracting PDF: {str(e)}"
    else:
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            text_content = "Binary content (non-PDF) that could not be decoded as UTF-8."

    if not text_content.strip():
        text_content = "No text content could be extracted from the uploaded file."

    service = LLMService()
    prompt = f"""
You are an advanced resume parsing and information extraction system.

Your task is to extract and transform resume data into a STRICT predefined JSON schema.

⚠️ IMPORTANT:
- The resume may contain inconsistent, missing, or unconventional section names
- DO NOT rely on headings like "Skills", "Experience", etc.
- Use semantic understanding to infer meaning
- Extract ALL relevant information even if scattered across the document

----------------------------------------

🎯 OBJECTIVE:

1. Extract all meaningful data from the resume
2. Normalize and map it into the given schema
3. Infer categories (education, projects, experience, etc.) from content
4. Extract skills from the ENTIRE resume (not just a skills section)
5. Ensure clean, deduplicated, structured output

----------------------------------------

📦 OUTPUT FORMAT (STRICT JSON):

{{
  "name": "",
  "email": "",
  "phone": "",
  "location": "",
  "desired_roles": [],
  "desired_domains": [],

  "experience_blocks": {{
    "education": [
      {{
        "school": "",
        "degree": "",
        "dates": "",
        "location": "",
        "CGPA": ""
      }}
    ],
    "coursework": [],

    "experience_level": "",

    "experience": [
      {{
        "company": "",
        "title": "",
        "dates": "",
        "location": "",
        "bullets": []
      }}
    ],

    "projects": [
      {{
        "name": "",
        "tech": "",
        "date": "",
        "bullets": []
      }}
    ],

    "leadership": [
      {{
        "org": "",
        "dates": "",
        "title": "",
        "location": "",
        "bullets": []
      }}
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

----------------------------------------

🧠 EXTRACTION RULES (VERY IMPORTANT):

1. 🔍 SEMANTIC SECTION DETECTION eg:
- "Work History", "Internships", or unlabeled paragraphs → experience
- "Academic Background" → education
- "Projects", "Academic Work", "Personal Work" → projects
- "Positions of Responsibility", "Volunteer Work" → leadership

2. 💡 SKILL EXTRACTION (CRITICAL)
- Extract skills from:
  - project descriptions
  - experience bullets
  - coursework
  - achievements
- DO NOT rely only on a "skills" section

Example:
"Built a MERN stack application using React, Node.js, Express, MongoDB"
→ languages: ["JavaScript"]
→ frameworks: ["React", "Express"]
→ tools: ["Node.js", "MongoDB"]

3. 🧩 SKILL CLASSIFICATION
- Languages: Python, C++, JavaScript, Java, etc.
- Frameworks: React, Next.js, Django, Flask, Express, etc.
- Tools: Git, Docker, MongoDB, PostgreSQL, Firebase, etc.

4. 📊 EXPERIENCE LEVEL INFERENCE
- No experience → "Entry Level"
- Internships/projects → "Entry Level"
- 1–3 years → "Junior"
- 3+ years → "Mid/Senior"

5. 🎯 TARGET ROLE/DOMAIN INFERENCE
- Extract "Desired Roles" and "Desired Domains" based on:
  - Resume summary or objective statement
  - Pattern of experience (e.g. all roles in Fintech → Fintech domain)
  - Explicit mentions of target positions

6. 📅 DATE FORMATTING (STRICT)
- Dates MUST be in the format: `MMM YYYY -- MMM YYYY` or `MMM YYYY -- Present`
- For single dates: `MMM YYYY`
- Example: `Jan 2020 -- Mar 2022`, `Oct 2021 -- Present`, `Dec 2023`
- DO NOT use relative dates like "3 years" or "current" (use "Present")
- DO NOT use numeric month formats like "01/2020"

7. 🧾 BULLET NORMALIZATION
- Convert all descriptions into concise bullet points
- Each bullet should be action-oriented

8. 🧹 CLEANING
- Remove duplicates (especially in skills)
- Keep formatting consistent

7. 🔗 LINKS
- Extract LinkedIn and GitHub from anywhere in resume

8. 🚫 NO HALLUCINATION
- Do NOT invent data
- If missing, leave empty string ""

9. 📦 STRICT OUTPUT
- Return ONLY valid JSON
- No explanations, no comments

----------------------------------------

📥 INPUT:
{text_content[:4000]}

📤 OUTPUT:
(STRICT JSON matching schema)
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
