from typing import TypedDict, Annotated
from pydantic import Field
from langgraph.graph.message import add_messages


class MainState(TypedDict):
    """
    A class to represent the state of a main agent in a graph.
    """

    # Attributes
    messages: Annotated[list, add_messages]  # Tracking workflow message history
