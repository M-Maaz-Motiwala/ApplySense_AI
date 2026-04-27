from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class CoverEmailState(TypedDict, total=False):
    user_profile: dict[str, Any]
    job_description: str
    company_info: dict[str, Any]
    cover_letter_text: str
    recruiter_email_draft: str


def personalization_node(state: CoverEmailState) -> CoverEmailState:
    profile = state.get("user_profile", {})
    company = state.get("company_info", {})
    job_desc = state.get("job_description", "")

    company_name = company.get("name", "your company")
    role_name = company.get("role", "this role")
    user_name = profile.get("name", "Candidate")

    state["cover_letter_text"] = (
        f"Dear Hiring Team at {company_name},\n\n"
        f"I am excited to apply for {role_name}. My background in backend engineering and applied AI aligns strongly "
        f"with your needs. In prior roles, I delivered measurable outcomes by building robust APIs and intelligent "
        f"automation pipelines.\n\n"
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
