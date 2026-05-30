import asyncio
import json
import logging
import re
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.services.llm.service import LLMService

logger = logging.getLogger(__name__)

def clean_json_text(text: str) -> str:
    """Extract and clean JSON content from potentially messy LLM responses."""
    text = text.strip()
    # Handle markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    # Final cleanup of common artifacts
    text = text.strip()
    return text


class ResumeGraphState(TypedDict, total=False):
    user_profile: dict[str, Any]
    job_description: str
    selected_experiences: list[dict[str, Any]]
    selected_projects: list[dict[str, Any]]
    optimized_json: dict[str, Any]
    latex_code: str
    analysis: dict[str, Any]
    rewritten_bullets: list[str]
    rewritten_summary: str
    rewritten_experience: list[dict[str, Any]]
    rewritten_projects: list[dict[str, Any]]
    quality_score: int
    critique: list[dict[str, Any]]
    approved_skills: list[str]
    approved_critique: list[str]
    attempts: int


def analyzer_node(state: ResumeGraphState) -> ResumeGraphState:
    """Analyze JD to extract core skills and requirements using LLM for accuracy."""
    state["attempts"] = 0
    jd = state.get("job_description", "")
    
    prompt = f"""You are a Job Market Analyst. Analyze the following Job Description to extract requirements.

DOs:
- Extract up to 10 core technical skills (Tools, Languages, Frameworks).
- Identify the Experience Level based on this mapping:
    * Entry Level: Internships or fresh grad (0 years).
    * Junior: 0-2 years of experience.
    * Mid: 2-5 years of experience.
    * Senior: 5-8 years of experience.
    * Lead: 8+ years of experience.
- If years are mentioned (e.g., "3+ years"), use the mapping above to set the label.
- Return ONLY valid JSON.

JOB DESCRIPTION:
{jd}

Return JSON:
{{
  "required_skills": ["Python", "Docker", ...],
  "experience_level": "Mid",
  "years_required": 3
}}"""

    try:
        from app.services.llm.service import LLMService
        llm = LLMService()
        result = asyncio.run(llm.generate(prompt))
        if result["status"] == "success":
            raw_text = clean_json_text(result["text"])
            analysis = json.loads(raw_text)
            state["analysis"] = analysis
            return state
    except Exception as e:
        logger.error(f"Analyzer LLM failed: {e}")
    
    # Simple regex fallback if LLM fails
    tokens = re.findall(r'\b\w+\b', jd)
    keywords = list(dict.fromkeys([t for t in tokens if len(t) > 2]))[:20]
    state["analysis"] = {"required_skills": keywords[:10], "experience_level": "unknown"}
    return state


def selector_node(state: ResumeGraphState) -> ResumeGraphState:
    """Select the most relevant experiences and projects based on analyzed skills."""
    profile = state.get("user_profile", {})
    experience_blocks = profile.get("experience_blocks", {})
    experiences = experience_blocks.get("experience", [])
    projects = experience_blocks.get("projects", [])
    
    # Use the skills extracted by the Analyzer
    analysis = state.get("analysis", {})
    target_skills = [s.lower() for s in analysis.get("required_skills", [])]
    
    logger.info(f"Selector Node: Target Skills identified: {target_skills}")

    def score_item(item: dict[str, Any]) -> int:
        blob = " ".join(str(v) for v in item.values()).lower()
        return sum(2 if s in blob else 0 for s in target_skills) # Weight target skills higher

    # 1. Rank and Select Experiences
    scored_exp = sorted(
        [(exp, score_item(exp)) for exp in experiences], 
        key=lambda x: x[1], 
        reverse=True
    )
    
    # Take items with any match, up to 3 to ensure we fill the page but don't overflow
    selected_exp = [x[0] for x in scored_exp if x[1] > 0][:3]
    
    # If no matches, fallback to the 2 most recent experiences
    if not selected_exp and experiences:
        logger.info("No experience matches found. Falling back to most recent 2.")
        selected_exp = experiences[:2]
    else:
        logger.info(f"Selected {len(selected_exp)} matching experiences. Top score: {scored_exp[0][1] if scored_exp else 0}")

    # 2. Rank and Select Projects
    scored_proj = sorted(
        [(proj, score_item(proj)) for proj in projects], 
        key=lambda x: x[1], 
        reverse=True
    )
    
    # Take top projects with matches, up to 2
    selected_proj = [x[0] for x in scored_proj if x[1] > 0][:2]
    
    # If no matches, fallback to the most recent project
    if not selected_proj and projects:
        logger.info("No project matches found. Falling back to most recent 1.")
        selected_proj = projects[:1]
    else:
        logger.info(f"Selected {len(selected_proj)} matching projects. Top score: {scored_proj[0][1] if scored_proj else 0}")

    state["selected_experiences"] = selected_exp
    state["selected_projects"] = selected_proj
    return state


def rewriter_node(state: ResumeGraphState) -> ResumeGraphState:
    """Use the LLM to rewrite experience bullets and generate a tailored summary."""
    jd = state.get("job_description", "")
    profile = state.get("user_profile", {})
    experiences = state.get("selected_experiences", [])
    projects = state.get("selected_projects", [])
    critique = state.get("critique", [])
    
    state["attempts"] = state.get("attempts", 0) + 1

    # Build prompt for the LLM
    exp_text = json.dumps(experiences, indent=2) if experiences else "No experience provided."
    proj_text = json.dumps(projects, indent=2) if projects else "No projects provided."
    skills = profile.get("skills_matrix", {})

    feedback_context = ""
    approved_critique = state.get("approved_critique", [])
    if approved_critique:
        feedback_context = f"\n\nUSER-APPROVED CRITIQUE TO ADDRESS:\n- " + "\n- ".join(approved_critique) + "\nPlease address these points specifically in this version."
    elif critique:
        # Fallback to general critique if user didn't specify, but only for first attempt or if not provided
        feedback_context = f"\n\nPREVIOUS CRITIQUE FOR IMPROVEMENT:\n- " + "\n- ".join([c.get("text", c) if isinstance(c, dict) else c for c in critique]) + "\nPlease address these points."

    approved_skills = state.get("approved_skills", [])
    if approved_skills:
        skills["approved_by_user"] = approved_skills

    version_context = "THIS IS THE FIRST VERSION. Stay strictly within the bounds of the provided profile data."
    if feedback_context:
        version_context = f"THIS IS A REVISION. {feedback_context}"

    prompt = f"""You are a professional resume writer.
{version_context}
    
Your task is to rewrite the candidate's experience and project bullet points to align with the job requirements.

JOB DESCRIPTION:
{jd}

CANDIDATE EXPERIENCES:
{exp_text}

CANDIDATE PROJECTS:
{proj_text}

CANDIDATE SKILLS:
{json.dumps(skills, indent=2)}

Return a JSON object with EXACTLY this structure (no markdown, no code fences, raw JSON only):
{{
  "summary": "A concise 2-3 sentence professional summary highlighting how the candidate's skills align with the specific job description.",
  "experience": [
    {{
      "company": "Company Name",
      "dates": "Start -- End",
      "title": "Job Title",
      "location": "City, State",
      "bullets": ["Achievement-focused bullet 1", "Achievement-focused bullet 2"]
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "tech": "Tech1, Tech2, Tech3",
      "date": "Month Year",
      "bullets": ["What you built and the impact"]
    }}
  ]
}}

RULES:
- STRICT GUARDRAILS (DO NOT VIOLATE):
  * DONT: DO NOT add extra hallucinated info. If it's not in the profile, it doesn't exist.
  * DONT: DO NOT exaggerate context out of available knowledge. Structure for impact, but stay grounded.
  * DO: Use ONLY the available info of the candidate profile.
  * DO: Use all selected experiences to fill the page effectively.
  * DO: Consider that the candidate will be interviewed on this. FAKE DETAILS ARE STRICTLY FORBIDDEN.
  * DONT: DO NOT invent metrics (%, $) or technical scope that is not in the source text.
- FORMATTING:
  * Start bullets with strong action verbs.
  * Keep bullets concise (1-2 lines).
  * Target exactly 3-4 bullets per item.
- Return ONLY raw JSON, no markdown code fences.
"""

    try:
        llm = LLMService()
        result = asyncio.run(llm.generate(prompt))
        if result["status"] == "success":
            raw_text = clean_json_text(result["text"])
            parsed = json.loads(raw_text)
            state["rewritten_summary"] = parsed.get("summary", "")
            state["rewritten_experience"] = parsed.get("experience") or experiences
            state["rewritten_projects"] = parsed.get("projects") or projects
            logger.info(f"LLM rewriter produced optimized content (Attempt {state['attempts']}).")
            return state
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"LLM rewriter failed, using original data: {e}")

    # Fallback: use original data as-is
    state["rewritten_summary"] = "Results-focused engineer aligned to target role requirements."
    state["rewritten_experience"] = experiences
    state["rewritten_projects"] = projects
    return state


def evaluator_node(state: ResumeGraphState) -> ResumeGraphState:
    """Use the LLM as an ATS Judge to score and critique the rewritten content."""
    jd = state.get("job_description", "")
    summary = state.get("rewritten_summary", "")
    experiences = state.get("rewritten_experience", [])
    projects = state.get("rewritten_projects", [])

    prompt = f"""You are a Senior Technical Recruiter and ATS Optimization Expert.
Evaluate the following resume content against the provided Job Description.

JOB DESCRIPTION:
{jd}

REWRITTEN RESUME CONTENT:
Summary: {summary}
Experience: {json.dumps(experiences, indent=2)}
Projects: {json.dumps(projects, indent=2)}

Score the content from 0 to 100 based on:
1. Keyword Alignment (Does it use the tools/langs from the JD?)
2. Impact & Metrics (Are there quantifiable achievements?)
3. Concise Formatting (Does it look like it fits on 1 page?)

Return a JSON object with EXACTLY this structure (raw JSON only):
{{
  "score": 85,
  "critique": [
    {{"text": "Strong match for Python", "type": "positive"}},
    {{"text": "Missing Kubernetes - suggest adding if you have this skill", "type": "skill_suggestion", "skill": "Kubernetes"}},
    {{"text": "Quantify results in bullet 1", "type": "improvement"}}
  ],
  "is_fit": true
}}

RULES:
- Be an uncompromising ATS gatekeeper.
- DONT: DO NOT approve if the resume has skills not found in the JD unless they are highly relevant.
- DO: Identify every missing core skill from the JD and list it as a "skill_suggestion".
- DO: Flag any bullet points that seem generic or lack impact.
- CRITICAL: If a skill is required by the JD but missing from the resume, you MUST add it as a "skill_suggestion" in the critique array.
- For each "skill_suggestion", include a "skill" key with the exact tool name.
- Return ONLY valid JSON."""

    try:
        llm = LLMService()
        result = asyncio.run(llm.generate(prompt))
        if result["status"] == "success":
            raw_text = clean_json_text(result["text"])
            parsed = json.loads(raw_text)
            state["quality_score"] = parsed.get("score", 0)
            state["critique"] = parsed.get("critique", [])
            logger.info(f"Evaluator Score: {state['quality_score']}/100")
            return state
    except Exception as e:
        logger.error(f"Evaluator failed: {e}")
        state["quality_score"] = 75 # Safe fallback
        state["critique"] = ["Evaluator service unavailable, using baseline."]

    return state


def formatter_node(state: ResumeGraphState) -> ResumeGraphState:
    profile = state.get("user_profile", {})
    experience_blocks = profile.get("experience_blocks", {})
    skills = profile.get("skills_matrix", {})

    # Build the optimized JSON for the Jinja2 template
    optimized_json = {
        # Heading
        "name": profile.get("name", "Candidate"),
        "email": profile.get("email", ""),
        "phone": profile.get("phone", ""),
        "location": profile.get("location", ""),
        "linkedin": profile.get("linkedin", ""),
        "linkedin_display": profile.get("linkedin", "").replace("https://", "").rstrip("/") if profile.get("linkedin") else "",
        "github": profile.get("github", ""),
        "github_display": profile.get("github", "").replace("https://", "").rstrip("/") if profile.get("github") else "",

        # Summary (LLM-generated)
        "summary": state.get("rewritten_summary", ""),

        # Education (pass-through from user profile)
        "education": experience_blocks.get("education", []),

        # Coursework (pass-through)
        "coursework": experience_blocks.get("coursework", []),

        # Experience (LLM-rewritten)
        "experience": state.get("rewritten_experience", []),

        # Projects (LLM-rewritten)
        "projects": state.get("rewritten_projects", []),

        # Skills (structured and filtered)
        "skills_languages": ", ".join(sorted(skills.get("languages", skills.get("skills", [])), key=lambda s: s.lower() not in set(k.lower() for k in state.get("analysis", {}).get("required_skills", [])))[:6]),
        "skills_tools": ", ".join(sorted(skills.get("tools", []), key=lambda s: s.lower() not in set(k.lower() for k in state.get("analysis", {}).get("required_skills", [])))[:6]),
        "skills_frameworks": ", ".join(sorted(skills.get("frameworks", []), key=lambda s: s.lower() not in set(k.lower() for k in state.get("analysis", {}).get("required_skills", [])))[:6]),

        # Leadership (pass-through)
        "leadership": experience_blocks.get("leadership", []),
    }

    state["optimized_json"] = optimized_json
    return state


def validator_node(state: ResumeGraphState) -> ResumeGraphState:
    optimized = state.get("optimized_json", {})

    # Ensure all list fields are actually lists
    for key in ["education", "coursework", "experience", "projects", "leadership"]:
        if not isinstance(optimized.get(key), list):
            optimized[key] = []

    # Ensure experience/project items have bullets as lists
    # Ensure experience/project items have bullets as lists and required fields
    for exp in optimized.get("experience", []) or []:
        if not isinstance(exp.get("bullets"), list):
            exp["bullets"] = []
        exp.setdefault("company", "Company")
        exp.setdefault("dates", "Start -- End")
        exp.setdefault("title", "Job Title")
        exp.setdefault("location", "City, State")

    for proj in optimized.get("projects", []) or []:
        if not isinstance(proj.get("bullets"), list):
            proj["bullets"] = []
        proj.setdefault("name", "Project")
        proj.setdefault("tech", "Technology Stack")
        proj.setdefault("date", "Month Year")

    for lead in optimized.get("leadership", []) or []:
        if not isinstance(lead.get("bullets"), list):
            lead["bullets"] = []
        lead.setdefault("org", "Organization")
        lead.setdefault("dates", "Start -- End")
        lead.setdefault("title", "Position")
        lead.setdefault("location", "City, State")

    # Ensure skill strings are safe with fallbacks
    optimized["skills_languages"] = str(optimized.get("skills_languages", "")).strip() or "Python, JavaScript"
    optimized["skills_tools"] = str(optimized.get("skills_tools", "")).strip() or "Git, Docker, AWS"
    optimized["skills_frameworks"] = str(optimized.get("skills_frameworks", "")).strip() or "FastAPI, React"

    state["optimized_json"] = optimized
    return state


def build_resume_graph():
    graph = StateGraph(ResumeGraphState)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("selector", selector_node)
    graph.add_node("rewriter", rewriter_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("formatter", formatter_node)
    graph.add_node("validator", validator_node)

    graph.add_edge(START, "analyzer")
    graph.add_edge("analyzer", "selector")
    graph.add_edge("selector", "rewriter")
    graph.add_edge("rewriter", "evaluator")

    # Conditional logic for self-correction
    def should_retry(state: ResumeGraphState):
        score = state.get("quality_score", 0)
        attempts = state.get("attempts", 0)
        if score < 80 and attempts < 3:
            logger.info(f"Quality score {score} < 80. Retrying (Attempt {attempts})...")
            return "retry"
        return "continue"

    graph.add_conditional_edges(
        "evaluator",
        should_retry,
        {
            "retry": "rewriter",
            "continue": "formatter"
        }
    )

    graph.add_edge("formatter", "validator")
    graph.add_edge("validator", END)

    return graph.compile()


resume_graph = build_resume_graph()
