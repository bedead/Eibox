from typing import Any, Dict, Literal, Optional, TypedDict


class EmailState(TypedDict):
    """
    A class to represent the state of a sequence agent in a graph.
    """

    pending_email: bool
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
