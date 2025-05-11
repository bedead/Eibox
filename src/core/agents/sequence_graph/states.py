from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from core.gmail.gmail_toolkit import GmailToolKit
from core.gmail.status import GmailToolKitRunningStatus
from core.llm.providers.types.model_selector import ModelSelector
from core.llm.providers.types.models_google import GoogleModel
from core.llm.providers.types.providers import BaseProvider
from core.llm.ai_toolkit import AIToolkit, get_ai_toolkit


class SequenceState(BaseModel):
    """
    A class to represent the state of a sequence agent in a graph.
    """

    # Attributes
    # id: str
    email_list: Dict[str, Any]
    email: dict
    is_mail_important: bool = False
    email_summary: Optional[str]
    is_response_needed: bool = False
    response_format: Optional[str]
    response_email_draft: Optional[str]
    response_approved: Optional[bool]
    response_sent: Optional[bool]
    response_edited: Optional[str]

    # tracking gmail_toolkit running status
    gmail_tool = GmailToolKit(interval=10, max_results=1)
    gmail_toolkit_status: GmailToolKitRunningStatus = GmailToolKitRunningStatus.STOPED

    # Model selection
    selected_model = ModelSelector(
        provider=BaseProvider.GOOGLE, model=GoogleModel.GEMINI_1_5_FLASH
    )
    # AI Toolkit
    ai_toolkit: Optional[AIToolkit] = get_ai_toolkit(model=selected_model)

    # tracking workflow message history
    messages: List[Dict[str, Any]]
