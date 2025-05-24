from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from src.core.gmail import GmailToolKit
from src.core.gmail.status import GmailToolKitRunningStatus
from src.core.llm.providers.types.model_selector import ModelSelector
from src.core.llm.providers.types.models_google import GoogleModel
from src.core.llm.providers.types.providers import BaseProvider
from src.core.llm.ai_toolkit import AIToolkit, get_ai_toolkit


class SequenceState(BaseModel):
    """
    A class to represent the state of a sequence agent in a graph.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

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

    # tracking gmail_toolkit running status
    gmail_tool: Optional[GmailToolKit] = GmailToolKit(
        max_results=1
    )  # Max results to 1, meaning only one email will be read at a time from google api
    gmail_toolkit_status: Optional[GmailToolKitRunningStatus] = (
        GmailToolKitRunningStatus.STOPED
    )

    # Model selection
    selected_model: Optional[ModelSelector] = ModelSelector(
        provider=BaseProvider.GOOGLE, model=GoogleModel.GEMINI_1_5_FLASH
    )
    # AI Toolkit
    ai_toolkit: Optional[AIToolkit] = get_ai_toolkit(model=selected_model)

    # tracking workflow message history
    messages: List[Dict[str, Any]] = Field(default=None)
