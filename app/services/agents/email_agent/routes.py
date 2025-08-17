from app.services.agents.email_agent.states import EmailState
from langgraph.graph import END


def check_read_email_router(state: EmailState):
    return (
        "get_gmail_toolkit_node"
        if not state["email"]
        else "analyze_mail_importance_node"
    )


def email_importance_router(
    state: EmailState,
):
    return (
        "is_response_needed_node" if state["is_mail_important"] else "get_gmail_toolkit_node"
    )


def is_response_needed_router(
    state: EmailState,
):
    return (
        "mail_response_format_node"
        if state["is_response_needed"]
        else "get_gmail_toolkit_node"
    )
