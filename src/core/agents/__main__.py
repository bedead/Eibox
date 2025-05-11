from langgraph.graph import StateGraph, START, END

from core.agents.sequence_graph.nodes import (
    analyze_importance,
    auto_edit_response,
    generate_draft_response,
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
from core.agents.sequence_graph.states import SequenceState
from langchain_google_genai import GoogleGenAI


# Create the State Graph
sequence_graph = StateGraph(
    name="Sequence Graph",
    description="A graph to represent the sequence of states in an agent.",
    state_schema=SequenceState,
    start=START,
    end=END,
)

# Add nodes to the graph
sequence_graph.add_node(
    name="start_gmail_toolkit",
    node=start_gmail_toolkit,
    description="Start the Gmail toolkit",
)
sequence_graph.add_node(
    name="pause_gmail_toolkit",
    node=pasue_gmail_toolkit,
    description="Pause the Gmail toolkit",
)
sequence_graph.add_node(
    name="resume_gmail_toolkit",
    node=resume_gmail_toolkit,
    description="Resume the Gmail toolkit",
)
sequence_graph.add_node(
    name="stop_gmail_toolkit",
    node=stop_gmail_toolkit,
    description="Stop the Gmail toolkit",
)
sequence_graph.add_node(
    name="restart_gmail_toolkit",
    node=restart_gmail_toolkit,
    description="Restart the Gmail toolkit",
)
sequence_graph.add_node(
    name="read_email_json", node=read_emails_json, description="Read email from JSON"
)
sequence_graph.add_node(
    name="analyze_mail_importance",
    node=analyze_importance,
    description="Analyze the importance of the email",
)
sequence_graph.add_node(
    name="summarize_email", node=summarize_email, description="Summarize the email"
)
sequence_graph.add_node(
    name="is_response_needed",
    node=is_response_needed,
    description="Check if a response is needed for the email",
)
sequence_graph.add_node(
    name="mail_response_format",
    node=mail_response_format,
    description="Get the response format to the email",
)
sequence_graph.add_node(
    name="generate_draft_response",
    node=generate_draft_response,
    description="Generate a draft response to the email",
)
sequence_graph.add_node(
    name="get_response_approval",
    node=get_response_approval,
    description="Get approval for the response",
)
sequence_graph.add_node(
    name="get_edited_response",
    node=get_edited_response,
    description="Get the edited response",
)
sequence_graph.add_node(
    name="auto_edit_response",
    node=auto_edit_response,
    description="Auto edit the response draft",
)
sequence_graph.add_node(
    name="send_email_response",
    node=send_email_response,
    description="Send the email response",
)

# Add edges to the graph
