from typing import Annotated

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, ConfigDict


class ChatbotState(BaseModel):
    """
    Represents the state of a main agent in a graph.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )  # allows Job, WebSocket, GmailToolKit

    # contextual information
    semantic_memory: str = ""
    episodic_memory: str = ""

    # Tracking workflow message history
    messages: Annotated[list[BaseMessage], add_messages]
