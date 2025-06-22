from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator, PrivateAttr


class SequenceState(BaseModel):
    """
    A class to represent the state of a sequence agent in a graph.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")

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
    messages: List[Dict[str, Any]] = Field(default=None)

    # @model_validator(mode="after")
    # def init_runtime_fields(self) -> "SequenceState":
    #     if not self.gmail_tool:
    #         self.gmail_tool = GmailToolKit(
    #             max_results=1
    #         )  # Max results to 1, meaning only one email will be read at a time from google api
    #     if not self.gmail_toolkit_status:
    #         self.gmail_toolkit_status = Status.STOPED
    #     if not self.ai_toolkit and self.selected_model:
    #         self.ai_toolkit = get_ai_toolkit(model=self.selected_model)
    #     return self
