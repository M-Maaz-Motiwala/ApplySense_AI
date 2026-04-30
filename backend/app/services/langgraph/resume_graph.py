import asyncio
import json
import logging
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.services.llm.service import LLMService

logger = logging.getLogger(__name__)


class ResumeGraphState(TypedDict, total=False):
    user_profile: dict[str, Any]
    job_description: str
    selected_experiences: list[dict[str, Any]]
    optimized_json: dict[str, Any]
    latex_code: str
    analysis: dict[str, Any]
    rewritten_bullets: list[str]


def analyzer_node(state: ResumeGraphState) -> ResumeGraphState:
    jd = state.get("job_description", "")
    tokens = [t.strip(".,") for t in jd.split() if len(t) > 3]
    keywords = list(dict.fromkeys([t for t in tokens if t[0].isalpha()]))[:20]
    required_skills = [k for k in keywords if k.lower() in {"python", "fastapi", "sql", "ml", "ai", "docker", "postgresql", "react", "java", "kubernetes", "aws", "flask", "django", "typescript", "javascript", "node", "go", "rust", "c++", "redis", "mongodb", "graphql", "terraform", "ci/cd"}]
    analysis = {
        "keywords": keywords,
        "required_skills": required_skills,
        "experience_level": "mid" if "3" in jd or "4" in jd else "senior" if "7" in jd else "unknown",
    }
    state["analysis"] = analysis
    return state


def selector_node(state: ResumeGraphState) -> ResumeGraphState:
    profile = state.get("user_profile", {})
    experience_blocks = profile.get("experience_blocks", {})
    experiences = experience_blocks.get("experience", [])
    projects = experience_blocks.get("projects", [])
    keywords = set(k.lower() for k in state.get("analysis", {}).get("keywords", []))

    def score_item(item: dict[str, Any]) -> int:
        blob = " ".join(str(v) for v in item.values()).lower()
        return sum(1 for k in keywords if k in blob)

    selected_exp = sorted(experiences, key=score_item, reverse=True)
    selected_proj = sorted(projects, key=score_item, reverse=True)[:3]

    state["selected_experiences"] = selected_exp
    state["selected_projects"] = selected_proj
    return state


def rewriter_node(state: ResumeGraphState) -> ResumeGraphState:
    """Use the LLM to rewrite experience bullets and generate a tailored summary."""
    jd = state.get("job_description", "")
    profile = state.get("user_profile", {})
    experiences = state.get("selected_experiences", [])
    projects = state.get("selected_projects", [])

    # Build prompt for the LLM
    exp_text = json.dumps(experiences, indent=2) if experiences else "No experience provided."
    proj_text = json.dumps(projects, indent=2) if projects else "No projects provided."
    skills = profile.get("skills_matrix", {})

    prompt = f"""You are a professional resume writer. Given a job description and a candidate's background,
rewrite their experience and projects into high-impact, ATS-optimized resume bullets.

JOB DESCRIPTION:
{jd}

CANDIDATE EXPERIENCE:
{exp_text}

CANDIDATE PROJECTS:
{proj_text}

CANDIDATE SKILLS:
{json.dumps(skills, indent=2)}

Return a JSON object with EXACTLY this structure (no markdown, no code fences, raw JSON only):
{{
  "summary": "A 2-3 sentence professional summary tailored to the job description",
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
- Each bullet MUST start with a strong action verb (Developed, Engineered, Architected, Implemented, etc.)
- Include metrics where possible (percentages, counts, time saved)
- Align keywords with the job description
- Keep bullets concise (1-2 lines max)
- If no experience/projects are provided, create reasonable entries based on the candidate's skills
- Return ONLY valid JSON, no other text"""

    try:
        llm = LLMService()
        result = asyncio.run(llm.generate(prompt))
        if result["status"] == "success":
            raw_text = result["text"].strip()
            # Strip markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

            parsed = json.loads(raw_text)
            state["rewritten_summary"] = parsed.get("summary", "")
            state["rewritten_experience"] = parsed.get("experience", [])
            state["rewritten_projects"] = parsed.get("projects", [])
            logger.info("LLM rewriter produced optimized content successfully.")
            return state
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"LLM rewriter failed, using original data: {e}")

    # Fallback: use original data as-is
    state["rewritten_summary"] = "Results-focused engineer aligned to target role requirements."
    state["rewritten_experience"] = experiences
    state["rewritten_projects"] = projects
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

        # Skills (structured)
        "skills_languages": ", ".join(skills.get("languages", skills.get("skills", []))),
        "skills_tools": ", ".join(skills.get("tools", [])),
        "skills_frameworks": ", ".join(skills.get("frameworks", [])),

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
    for exp in optimized.get("experience", []):
        if not isinstance(exp.get("bullets"), list):
            exp["bullets"] = []

    for proj in optimized.get("projects", []):
        if not isinstance(proj.get("bullets"), list):
            proj["bullets"] = []

    for lead in optimized.get("leadership", []):
        if not isinstance(lead.get("bullets"), list):
            lead["bullets"] = []

    state["optimized_json"] = optimized
    return state


def build_resume_graph():
    graph = StateGraph(ResumeGraphState)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("selector", selector_node)
    graph.add_node("rewriter", rewriter_node)
    graph.add_node("formatter", formatter_node)
    graph.add_node("validator", validator_node)

    graph.add_edge(START, "analyzer")
    graph.add_edge("analyzer", "selector")
    graph.add_edge("selector", "rewriter")
    graph.add_edge("rewriter", "formatter")
    graph.add_edge("formatter", "validator")
    graph.add_edge("validator", END)

    return graph.compile()


resume_graph = build_resume_graph()
