from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class SequenceState(BaseModel):
    """
    A class to represent the state of a sequence agent in a graph.
    """

    # model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")

    # Attributes
    # id: str
    email: Dict[str, Any] = Field(
        default=None
    )  # Email data read from JSON file (One at a time)
    is_mail_important: Optional[bool] = Field(default=None)
    email_summary: Optional[str] = Field(default=None)
    is_response_needed: Optional[bool] = Field(default=None)
    response_format: Optional[str] = Field(default=None)
    response_email_draft: Optional[str] = Field(default=None)  # Initial Draft response
    draft_manual_edit_mode: Optional[Literal[0, 1, 2]] = Field(default=None)
    response_approved: Optional[bool] = Field(default=None)
    response_sent: Optional[bool] = Field(default=None)
    response_edited: Optional[str] = Field(
        default=None
    )  # Edited draft response (Manually or Auto)

    # tracking workflow message history
    # messages: List[Dict[str, Any]] = Field(default=None)
