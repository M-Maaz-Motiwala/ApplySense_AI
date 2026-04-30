from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.llm.service import LLMService

router = APIRouter(prefix="/llm", tags=["llm"])

class PromptRequest(BaseModel):
    prompt: str

@router.post("/test")
async def test_llm(payload: PromptRequest):
    service = LLMService()
    result = await service.generate(payload.prompt)
    if result["status"] == "failed":
        raise HTTPException(status_code=500, detail="LLM generation failed for both Gemini and Groq.")
    return result

@router.get("/sample-prompt")
async def sample_prompt():
    sample_jd = "Looking for a Senior Python Developer with 5+ years of experience in FastAPI and microservices."
    sample_experience = "Developed a scalable backend service using Flask and Docker."
    
    prompt = f"""Given the following Job Description:
{sample_jd}

Rewrite the following experience point into a high-impact, results-driven resume bullet:
"{sample_experience}"
"""
    return {"prompt": prompt.strip()}
