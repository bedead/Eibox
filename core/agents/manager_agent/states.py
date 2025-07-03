from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class ManagerState(TypedDict):

    # checking attribute
    pending_email: bool = False

    # data attribute
    email_summary: str
    response_draft: str
    messages: Annotated[list, add_messages]
