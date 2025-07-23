from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore
from typing_extensions import Annotated


def retrieve_tools(
    query: str,
    store: Annotated[BaseStore, InjectedStore],
) -> list[str]:
    """Retrieve a tool to use, given a search query."""
    results = store.search(("tools",), query=query, limit=5)
    # print(f"Tool search results :{results}")
    tool_ids = [result.key for result in results]
    return tool_ids
