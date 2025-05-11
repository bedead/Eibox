from typing import Literal
from .states import SequenceState
from langgraph.graph import END
from langgraph.types import Command


def importance_router(
    state: SequenceState,
) -> Command:
    return (
        Command(goto="summarize_email")
        if state.is_mail_important
        else Command(goto=END)
    )
