from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    human_response = interrupt({"question": query})
    return human_response["data"]
