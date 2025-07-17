from typing import Any, Dict, Literal, Optional, TypedDict, Annotated
from langgraph.graph.message import add_messages


class ChatbotState(TypedDict):
    """
    Represents the state of a main agent in a graph.
    """

    # User/Session management attribute
    namespace_for_memory: tuple

    # Current model management
    current_model_name: str
    current_model_provider: str

    # Tracking workflow message history
    messages: Annotated[list, add_messages]
