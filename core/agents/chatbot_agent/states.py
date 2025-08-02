from typing import Any, Dict, Literal, Optional, TypedDict, Annotated
from langgraph.graph.message import add_messages


class ChatbotState(TypedDict):
    """
    Represents the state of a main agent in a graph.
    """

    # User/Session management attribute
    namespace_for_gmail: tuple

    # contextual information
    semantic_memory: Optional[str]
    episodic_memory: Optional[str]

    # Tracking workflow message history
    messages: Annotated[list, add_messages]
