from typing import Optional, Annotated

from langgraph.graph.message import add_messages
from pydantic import BaseModel


class ChatbotState(BaseModel):
    """
    Represents the state of a main agent in a graph.
    """

    memory_update_counter: int = 3

    # contextual information
    semantic_memory: str = ""
    episodic_memory: str = ""
    
    # Tracking workflow message history
    messages: Annotated[list, add_messages]
