from typing import Any, Dict, Optional, TypedDict


class EmailState(TypedDict):
    """
    A class to represent the state of a sequence agent in a graph.
    """

    current_mail_id: str
    email: Dict[str, Any]  # Email data read from JSON file (One at a time)
    is_mail_important: Optional[bool]
    is_response_needed: Optional[bool]
    response_format: Optional[str]
    response_email_draft: Optional[str]  # Initial Draft response
