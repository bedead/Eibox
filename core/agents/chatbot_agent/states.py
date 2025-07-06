from typing import Any, Dict, Literal, Optional, TypedDict, Annotated
from langgraph.graph.message import add_messages


class ChatbotState(TypedDict):
    """
    Represents the state of a main agent in a graph message history.
    """

    messages: Annotated[list, add_messages]  # Tracking workflow message history
    current_model_name: str
    current_model_provider: str
