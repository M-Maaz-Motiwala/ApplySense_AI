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

class SuggestSkillsRequest(BaseModel):
    role: str
    category: str

class GenerateBulletsRequest(BaseModel):
    description: str

@router.post("/suggest-skills")
async def suggest_skills(payload: SuggestSkillsRequest):
    service = LLMService()
    prompt = f"Suggest a list of exactly 10 highly relevant {payload.category} for a '{payload.role}'. Return only a comma-separated list."
    result = await service.generate(prompt)
    if result["status"] == "failed":
        raise HTTPException(status_code=500, detail="Failed to generate skills.")
    
    # Parse the comma-separated list
    skills = [s.strip() for s in result["text"].split(",")]
    return {"skills": skills}

@router.post("/generate-bullets")
async def generate_bullets(payload: GenerateBulletsRequest):
    service = LLMService()
    prompt = f"""
Convert the following experience description into 3 professional, high-impact resume bullet points.
Start each bullet with a strong action verb. Focus on impact, metrics if possible, and technologies used.
Do not include asterisks or numbering, just return each bullet on a new line.

Description:
"{payload.description}"
"""
    result = await service.generate(prompt)
    if result["status"] == "failed":
        raise HTTPException(status_code=500, detail="Failed to generate bullets.")
    
    # Parse new lines into a list
    bullets = [b.strip().lstrip('- ').strip() for b in result["text"].split("\n") if b.strip()]
    return {"bullets": bullets}
