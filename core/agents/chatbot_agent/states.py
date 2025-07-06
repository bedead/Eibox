from typing import Any, Dict, Literal, Optional, TypedDict, Annotated
from langgraph.graph.message import add_messages


class ChatbotState(TypedDict):
    """
    Represents the state of a main agent in a graph message history.
    """

    messages: Annotated[list, add_messages]  # Tracking workflow message history
    current_model_name: str
    current_model_provider: str

    email: Dict[str, Any]  # Email data read from JSON file (One at a time)
    is_mail_important: Optional[bool]
    email_summary: Optional[str]
    is_response_needed: Optional[bool]
    response_format: Optional[str]
    response_email_draft: Optional[str]  # Initial Draft response
    draft_manual_edit_mode: Optional[Literal[0, 1, 2]]
    response_approved: Optional[bool]
    response_sent: Optional[bool]
    response_edited: Optional[str]  # Edited draft response (Manually or Auto)
