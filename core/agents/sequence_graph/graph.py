from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from core.utils.utils import display_graph
from .nodes import (
    analyze_importance,
    auto_edit_response,
    generate_draft_response,
    get_draft_edit_mode,
    get_edited_response,
    get_response_approval,
    is_response_needed,
    mail_response_format,
    pasue_gmail_toolkit,
    read_emails_json,
    send_email_response,
    start_gmail_toolkit,
    resume_gmail_toolkit,
    stop_gmail_toolkit,
    restart_gmail_toolkit,
    summarize_email,
)
from .routes import (
    check_read_email_router,
    get_draft_edit_mode_router,
    get_response_approval_router,
    email_importance_router,
    is_response_needed_router,
)
from .states import SequenceState


def create_sequence_graph() -> StateGraph:
    # Create the State Graph
    sequence_graph = StateGraph(
        state_schema=SequenceState,
    )

    # Add nodes to the graph
    sequence_graph.add_node(
        node="start_gmail_toolkit_node",
        action=start_gmail_toolkit,
    )
    sequence_graph.add_node(
        node="pause_gmail_toolkit_node",
        action=pasue_gmail_toolkit,
    )
    sequence_graph.add_node(
        node="resume_gmail_toolkit_node",
        action=resume_gmail_toolkit,
    )
    sequence_graph.add_node(
        node="stop_gmail_toolkit_node",
        action=stop_gmail_toolkit,
    )
    sequence_graph.add_node(
        node="restart_gmail_toolkit_node",
        action=restart_gmail_toolkit,
    )
    sequence_graph.add_node(node="read_email_json_node", action=read_emails_json)
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
    sequence_graph.add_node(
        node="get_response_approval_node",
        action=get_response_approval,
    )
    sequence_graph.add_node(node="get_draft_edit_mode_node", action=get_draft_edit_mode)
    sequence_graph.add_node(
        node="get_edited_response_node",
        action=get_edited_response,
    )
    sequence_graph.add_node(
        node="auto_edit_response_node",
        action=auto_edit_response,
    )
    sequence_graph.add_node(
        node="send_email_response_node",
        action=send_email_response,
    )

    # Add edges to the graph
    sequence_graph.add_edge(START, "start_gmail_toolkit_node")
    sequence_graph.add_edge("start_gmail_toolkit_node", "read_email_json_node")
    sequence_graph.add_conditional_edges(
        source="read_email_json_node",
        path=check_read_email_router,
        path_map={
            "read_email_json_node": "read_email_json_node",
            "pause_gmail_toolkit_node": "pause_gmail_toolkit_node",
        },
    )
    sequence_graph.add_edge("pause_gmail_toolkit_node", "analyze_mail_importance_node")
    sequence_graph.add_conditional_edges(
        source="analyze_mail_importance_node",
        path=email_importance_router,
        path_map={
            "summarize_email_node": "summarize_email_node",
            "resume_gmail_toolkit_node": "resume_gmail_toolkit_node",
        },
    )
    sequence_graph.add_edge("resume_gmail_toolkit_node", "read_email_json_node")
    sequence_graph.add_edge("summarize_email_node", "is_response_needed_node")
    sequence_graph.add_conditional_edges(
        source="is_response_needed_node",
        path=is_response_needed_router,
        path_map={
            "mail_response_format_node": "mail_response_format_node",
            "resume_gmail_toolkit_node": "resume_gmail_toolkit_node",
        },
    )

    sequence_graph.add_edge("mail_response_format_node", "generate_draft_response_node")
    sequence_graph.add_edge(
        "generate_draft_response_node", "get_response_approval_node"
    )
    sequence_graph.add_conditional_edges(
        source="get_response_approval_node",
        path=get_response_approval_router,
        path_map={
            "send_email_response_node": "send_email_response_node",
            "get_draft_edit_mode_node": "get_draft_edit_mode_node",
        },
    )
    sequence_graph.add_conditional_edges(
        source="get_draft_edit_mode_node",
        path=get_draft_edit_mode_router,
        path_map={
            "get_edited_response_node": "get_edited_response_node",
            "auto_edit_response_node": "auto_edit_response_node",
            "resume_gmail_toolkit_node": "resume_gmail_toolkit_node",
        },
    )
    sequence_graph.add_edge("auto_edit_response_node", "get_response_approval_node")
    sequence_graph.add_edge("get_edited_response_node", "get_response_approval_node")

    sequence_graph.add_edge("send_email_response_node", END)

    return sequence_graph




initial_state = SequenceState()
checkpointer = InMemorySaver()
graph = create_sequence_graph().compile(checkpointer=checkpointer, debug=True)
# display_graph(graph, use_mermaid=True, use_api=True)
