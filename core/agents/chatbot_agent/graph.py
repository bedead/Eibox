from textwrap import dedent
from typing_extensions import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition, InjectedState
from langchain.chat_models import init_chat_model
from core.agents.chatbot_agent.states import ChatbotState
from langgraph.types import Command
from langgraph.store.redis import RedisStore
from langgraph.store.base import BaseStore
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from apscheduler.job import Job
from core.gmail.gmail_toolkit import GmailToolKit
from core.job_scheduler.jobs import (
    delete_email_scheduler_job,
    start_email_scheduler_job,
)


with RedisStore.from_conn_string("redis://localhost:6379") as store:
    store.setup()


graph_builder = StateGraph(ChatbotState)
available_models: dict = {
    "qwen2.5:0.5b": {"model_name": "qwen2.5:0.5b", "provider": "ollama"},
    "gemini-1.5-flash": {
        "model_name": "gemini-1.5-flash",
        "provider": "google_genai",
    },
    "gemini-2.0-flash": {
        "model_name": "gemini-2.0-flash",
        "provider": "google_genai",
    },
    "gemini-1.5-flash-8b": {
        "model_name": "gemini-1.5-flash-8b",
        "provider": "google_genai",
    },
    "gemini-1.5-Pro": {
        "model_name": "gemini-1.5-Pro",
        "provider": "google_genai",
    },
    "gemini-2.0-flash-lite": {
        "model_name": "gemini-2.0-flash-lite",
        "provider": "google_genai",
    },
    "gemini-2.0-flash-preview-image-generation": {
        "model_name": "gemini-2.0-flash-preview-image-generation",
        "provider": "google_genai",
    },
    "gemini-2.5-flash-lite-preview-06-17": {
        "model_name": "gemini-2.5-flash-lite-preview-06-17",
        "provider": "google_genai",
    },
    "gemini-2.5-flash": {
        "model_name": "gemini-2.5-flash",
        "provider": "google_genai",
    },
    "gemini-2.5-pro": {
        "model_name": "gemini-2.5-pro",
        "provider": "google_genai",
    },
}


@tool
def get_userid_tool(config: RunnableConfig):
    """
    Retrieves the user ID and thread ID from the AI agent's runtime configuration.

    This tool is typically used to identify the current user and their associated chat thread

    Returns:
        dict: A dictionary containing:
            - "user_id" (str): The ID or username of the user.
            - "thread_id" (str): The ID representing the current conversation or chat instance.
    """

    return {
        "user_id": config["configurable"].get("user_id"),
        "thread_id": config["configurable"].get("thread_id"),
    }


@tool
def start_email_scheduler_job_tool(user_id: str, thread_id: str, interval: int):
    """
    Starts a scheduled background job that periodically checks or processes emails
    related to a specific user and thread.

    Args:
        user_id (str): The unique identifier for the user.
        thread_id (str): The unique identifier of the email thread to track.
        interval (int): The frequency (in seconds) at which the job should run.

    Returns:
        Job: The background job instance that was started.
    """
    job: Job = start_email_scheduler_job(
        user_id=user_id, thread_id=thread_id, interval=interval
    )
    return job


@tool
def delete_email_scheduler_job_tool(user_id: str, thread_id: str):
    """
    Deletes or stops an existing scheduled job that was set to process or monitor
    emails for a specific user and thread.

    Args:
        user_id (str): The unique identifier for the user.
        thread_id (str): The unique identifier of the thread whose job should be deleted.

    Returns:
        Dict['status':]: status is "success" if job removed, and Exception e is returned in status.
    """
    result = delete_email_scheduler_job(user_id, thread_id)
    return result


# TODO: add tool for fetching gmails with specific conditions
# like from date, to date, how many mails, with search query, read mails, unread mails, spam mails, *
@tool
def search_gmails():
    """
    Tool to search Gmail messages based on filters.

    This function is intended to support search features such as:
    - Filtering by date range (from, to)
    - Limiting the number of emails returned
    - Applying search queries (subject, sender, keywords)
    - Filtering by read/unread status
    - Including or excluding spam folder

    Args:
        None

    Returns:
        None
    """
    toolkit = GmailToolKit()


llm = init_chat_model()
tools = [
    start_email_scheduler_job_tool,
    delete_email_scheduler_job_tool,
    get_userid_tool,
]
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: ChatbotState, store: BaseStore) -> Command:

    mail = store.get(namespace=state["namespace_for_memory"], key="mail")
    draft_response = store.get(
        namespace=state["namespace_for_memory"], key="draft_response"
    )

    system_instruction = dedent(
        """
        <instructions>
        You are an expert assistant designed to help users manage their Gmail accounts efficiently.

        Your responsibilities include:
        - Notifying the user about any new important emails in a formal, concise tone — similar to JARVIS from Iron Man.
        - Seeking the user's approval before sending a pre-generated draft reply to any email.
        - Answering the user's queries normally if no email data is available.

        Tool Usage:
        - If additional context is required (e.g., user identity, thread details, etc), use available relevant tools.
        - If the user requests mail filtering, summaries, or specific content, use search or query tools accordingly.

        Always behave with professionalism, clarity, and a touch of JARVIS-like wit when appropriate.

        </instructions>

        <mail_data>
        This email data has been received via a background task — the user is not yet aware of it.

        New Email Details:
        - Sender: {mail_sender}
        - Subject: {mail_subject}
        - Body: {mail_body}
        - Date: {mail_date}
        - Draft Response Prepared: {draft_response}
        </mail_data>
        """
    ).format(
        mail_sender=mail.value.get("sender") if mail else None,
        mail_subject=mail.value.get("subject") if mail else None,
        mail_body=mail.value.get("body") if mail else None,
        mail_date=mail.value.get("date") if mail else None,
        draft_response=draft_response.value if draft_response else None,
    )

    messages = [
        {"role": "system", "content": system_instruction},
    ] + state["messages"]
    message = llm_with_tools.invoke(
        input=messages,
        config={
            "configurable": {
                "model": state["current_model_name"],
                "model_provider": state["current_model_provider"],
            }
        },
    )

    # assert len(message.tool_calls) <= 1
    return Command(update={"messages": [message]})


def set_initial_model(state: ChatbotState, store: BaseStore, config: RunnableConfig):
    user_id = config["configurable"].get("user_id", "1")
    thread_id = config["configurable"].get("thread_id", "test")
    namespace_for_memory = (user_id, thread_id)

    return {
        "namespace_for_memory": namespace_for_memory,
        "current_model_name": available_models["gemini-1.5-flash"]["model_name"],
        "current_model_provider": available_models["gemini-1.5-flash"]["provider"],
    }


graph_builder.add_node("set_model", set_initial_model)
graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "set_model")
graph_builder.add_edge("set_model", "chatbot")
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")

graph = graph_builder.compile(checkpointer=MemorySaver(), store=store)
