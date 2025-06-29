from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from .nodes import llm
from .states import MainState
from .tools import human_assistance


def create_graph():
    """
    Create a state graph for the main agent.
    """
    graph = StateGraph(
        state_schema=MainState,
    )

    human_tool_node = ToolNode(tools=[human_assistance])
    graph.add_node(node="llm_node", action=llm)
    graph.add_node(node="tools", action=human_tool_node)

    graph.add_edge(START, "llm_node")
    graph.add_conditional_edges(
        "llm_node",
        tools_condition,
    )
    graph.add_edge("tools", "llm_node")

    return graph


graph = create_graph().compile(checkpointer=InMemorySaver(), debug=True)
