from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class CoverEmailState(TypedDict, total=False):
    user_profile: dict[str, Any]
    job_description: str
    company_info: dict[str, Any]
    cover_letter_text: str
    recruiter_email_draft: str


import asyncio
import logging
from app.api.v1.llm import LLMService

logger = logging.getLogger(__name__)

def personalization_node(state: CoverEmailState) -> CoverEmailState:
    profile = state.get("user_profile", {})
    company = state.get("company_info", {})
    job_desc = state.get("job_description", "")

    company_name = company.get("name", "your company")
    role_name = company.get("role", "this role")
    user_name = profile.get("name", "Candidate")
    
    prompt = f"""You are an expert career coach and professional copywriter.
Write a highly professional, detailed, and compelling cover letter for the candidate '{user_name}' applying for the role '{role_name}' at '{company_name}'.

Candidate Profile Context:
{profile}

Job Description Context:
{job_desc}

Instructions:
1. Make the cover letter detailed, engaging, and professional (around 300-400 words).
2. Directly reference specific keywords, requirements, and challenges mentioned in the Job Description.
3. Highlight the candidate's most relevant skills and past experiences that prove they are a perfect fit.
4. Output ONLY the raw text of the cover letter. Do not include any surrounding markdown or commentary.
"""
    try:
        llm = LLMService()
        result = asyncio.run(llm.generate(prompt))
        if result["status"] == "success":
            state["cover_letter_text"] = result["text"].strip()
            logger.info("LLM generated detailed cover letter successfully.")
            return state
    except Exception as e:
        logger.warning(f"Cover letter generation failed: {e}")

    # Fallback to simple template
    state["cover_letter_text"] = (
        f"Dear Hiring Team at {company_name},\n\n"
        f"I am excited to apply for {role_name}. My background aligns strongly "
        f"with your needs. In prior roles, I delivered measurable outcomes by building robust solutions.\n\n"
        f"I am particularly drawn to this opportunity because of the challenges highlighted in your description: {job_desc[:300]}...\n\n"
        f"Sincerely,\n{user_name}"
    )
    return state


def email_node(state: CoverEmailState) -> CoverEmailState:
    profile = state.get("user_profile", {})
    company = state.get("company_info", {})
    user_name = profile.get("name", "Candidate")
    role_name = company.get("role", "the role")
    company_name = company.get("name", "your company")

    state["recruiter_email_draft"] = (
        f"Subject: Application for {role_name} - {user_name}\n\n"
        f"Hi {company.get('recruiter_name', 'Recruiter')},\n\n"
        f"I have submitted my application for {role_name} at {company_name}. "
        f"I would appreciate the opportunity to discuss how my experience can support your team.\n\n"
        f"Best regards,\n{user_name}"
    )
    return state


def build_cover_email_graph():
    graph = StateGraph(CoverEmailState)
    graph.add_node("personalize", personalization_node)
    graph.add_node("email", email_node)

    graph.add_edge(START, "personalize")
    graph.add_edge("personalize", "email")
    graph.add_edge("email", END)

    return graph.compile()


cover_email_graph = build_cover_email_graph()
