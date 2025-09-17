from typing import Any, Dict, Literal, Optional, Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel


class ChatbotState(BaseModel):
    """
    Represents the state of a main agent in a graph.
    """

    memory_update_counter: int = 3

    # contextual information
    semantic_memory: Optional[str] = ""
    episodic_memory: Optional[str] = ""

    # Tracking workflow message history
    messages: Annotated[list, add_messages]
