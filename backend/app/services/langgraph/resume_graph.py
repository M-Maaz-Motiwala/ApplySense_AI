from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


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
    required_skills = [k for k in keywords if k.lower() in {"python", "fastapi", "sql", "ml", "ai", "docker"}]
    analysis = {
        "keywords": keywords,
        "required_skills": required_skills,
        "experience_level": "mid" if "3" in jd or "4" in jd else "senior" if "7" in jd else "unknown",
    }
    state["analysis"] = analysis
    return state


def selector_node(state: ResumeGraphState) -> ResumeGraphState:
    profile = state.get("user_profile", {})
    experiences = profile.get("experience_blocks", {}).get("projects", [])
    keywords = set(k.lower() for k in state.get("analysis", {}).get("keywords", []))

    def score_exp(exp: dict[str, Any]) -> int:
        blob = f"{exp.get('name', '')} {exp.get('description', '')}".lower()
        return sum(1 for k in keywords if k in blob)

    selected = sorted(experiences, key=score_exp, reverse=True)[:3]
    state["selected_experiences"] = selected
    return state


def rewriter_node(state: ResumeGraphState) -> ResumeGraphState:
    rewritten: list[str] = []
    keywords = state.get("analysis", {}).get("required_skills", [])
    for exp in state.get("selected_experiences", []):
        name = exp.get("name", "Project")
        desc = exp.get("description", "Built impactful system")
        kw = ", ".join(keywords[:3]) if keywords else "relevant technologies"
        rewritten.append(
            f"Led {name}; {desc}. Improved delivery speed by 35% using {kw} while coordinating cross-functional stakeholders."
        )
    state["rewritten_bullets"] = rewritten[:5]
    return state


def formatter_node(state: ResumeGraphState) -> ResumeGraphState:
    profile = state.get("user_profile", {})
    optimized_json = {
        "name": profile.get("name", "Candidate"),
        "email": profile.get("email", "candidate@example.com"),
        "phone": profile.get("phone", ""),
        "location": profile.get("location", ""),
        "skills": profile.get("skills_matrix", {}).get("skills", []),
        "summary": "Results-focused engineer aligned to target role requirements.",
        "experience_bullets": state.get("rewritten_bullets", []),
    }
    state["optimized_json"] = optimized_json
    return state


def validator_node(state: ResumeGraphState) -> ResumeGraphState:
    optimized = state.get("optimized_json", {})
    profile_skills = set(state.get("user_profile", {}).get("skills_matrix", {}).get("skills", []))
    safe_skills = [skill for skill in optimized.get("skills", []) if skill in profile_skills]
    optimized["skills"] = safe_skills

    latex_preview = "\\n".join([f"\\item {line}" for line in optimized.get("experience_bullets", [])])
    state["latex_code"] = "\\begin{itemize}\n" + latex_preview + "\\n\\end{itemize}"
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
