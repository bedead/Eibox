from .states import EmailState
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
        "summarize_email_node"
        if state["is_mail_important"]
        else "get_gmail_toolkit_node"
    )


def is_response_needed_router(
    state: EmailState,
):
    return (
        "mail_response_format_node"
        if state["is_response_needed"]
        else "get_gmail_toolkit_node"
    )


def get_response_approval_router(
    state: EmailState,
):
    return (
        "send_email_response_node"
        if state["response_approved"]
        else "get_draft_edit_mode_node"
    )


def get_draft_edit_mode_router(
    state: EmailState,
):
    if state["draft_manual_edit_mode"] == 0:
        return "get_edited_response_node"
    elif state["draft_manual_edit_mode"] == 1:
        return "auto_edit_response_node"
    elif state["draft_manual_edit_mode"] == 2:
        return "get_gmail_toolkit_node"
    else:
        return END
