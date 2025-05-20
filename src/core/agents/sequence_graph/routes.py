from typing import Literal
from .states import SequenceState
from langgraph.graph import END
from langgraph.types import Command


def check_read_email_router(state: SequenceState):
    return "read_email_json_node" if not state.email else "pause_gmail_toolkit_node"


def email_importance_router(
    state: SequenceState,
):
    return (
        Command(goto="summarize_email_node")
        if state.is_mail_important
        else "resume_gmail_toolkit_node"
    )


def is_response_needed_router(
    state: SequenceState,
) -> Command[Literal["mail_response_format_node", "resume_gmail_toolkit_node"]]:
    return (
        Command(goto="mail_response_format_node")
        if state.is_response_needed
        else Command(goto="resume_gmail_toolkit_node")
    )


def get_response_approval_router(
    state: SequenceState,
) -> Command[Literal["send_email_response_node", "get_draft_edit_mode_node"]]:
    return (
        Command(goto="send_email_response_node")
        if state.response_approved
        else Command(goto="get_draft_edit_mode_node")
    )


def get_draft_edit_mode_router(
    state: SequenceState,
) -> Command[
    Literal[
        "get_edited_response_node",
        "auto_edit_response_node",
        "resume_gmail_toolkit_node",
    ]
]:
    if state.draft_manual_edit_mode == 0:
        return Command(goto="get_edited_response_node")
    elif state.draft_manual_edit_mode == 1:
        return Command(goto="auto_edit_response_node")
    elif state.draft_manual_edit_mode == 2:
        return Command(goto="resume_gmail_toolkit_node")
    else:
        return Command(goto=END)
