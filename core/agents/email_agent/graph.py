from langgraph.graph import StateGraph, START, END

from core.agents.email_agent.nodes import (
    analyze_importance,
    generate_draft_response,
    is_response_needed,
    mail_response_format,
    get_gmail_toolkit,
    summarize_email,
    store,
)
from core.agents.email_agent.routes import (
    check_read_email_router,
    email_importance_router,
    is_response_needed_router,
)
from core.agents.email_agent.states import EmailState


def create_sequence_graph() -> StateGraph:
    # Create the State Graph
    sequence_graph = StateGraph(
        state_schema=EmailState,
    )

    # Add nodes to the graph
    sequence_graph.add_node(
        node="get_gmail_toolkit_node",
        action=get_gmail_toolkit,
    )
    sequence_graph.add_node(
        node="analyze_mail_importance_node",
        action=analyze_importance,
    )
    sequence_graph.add_node(node="summarize_email_node", action=summarize_email)
    sequence_graph.add_node(
        node="is_response_needed_node",
        action=is_response_needed,
    )
    sequence_graph.add_node(
        node="mail_response_format_node",
        action=mail_response_format,
    )
    sequence_graph.add_node(
        node="generate_draft_response_node",
        action=generate_draft_response,
    )

    # Add edges to the graph
    sequence_graph.add_edge(START, "get_gmail_toolkit_node")
    sequence_graph.add_conditional_edges(
        source="get_gmail_toolkit_node",
        path=check_read_email_router,
        path_map={
            "get_gmail_toolkit_node": "get_gmail_toolkit_node",
            "analyze_mail_importance_node": "analyze_mail_importance_node",
        },
    )
    sequence_graph.add_conditional_edges(
        source="analyze_mail_importance_node",
        path=email_importance_router,
        path_map={
            "summarize_email_node": "summarize_email_node",
            "get_gmail_toolkit_node": "get_gmail_toolkit_node",
        },
    )
    sequence_graph.add_edge("summarize_email_node", "is_response_needed_node")
    sequence_graph.add_conditional_edges(
        source="is_response_needed_node",
        path=is_response_needed_router,
        path_map={
            "mail_response_format_node": "mail_response_format_node",
            "get_gmail_toolkit_node": "get_gmail_toolkit_node",
        },
    )

    sequence_graph.add_edge("mail_response_format_node", "generate_draft_response_node")
    sequence_graph.add_edge("generate_draft_response_node", END)

    return sequence_graph


graph = create_sequence_graph().compile(store=store)
# print(graph.get_graph().draw_mermaid())
