from textwrap import dedent
from typing import List, Dict, Any
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition, InjectedState
from core.agents.chatbot_agent.states import ChatbotState
from langgraph.types import Command
from langgraph.store.base import BaseStore
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model
from core.storage.setup import db_store
from core.agents.chatbot_agent.tools import all_tools

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
llm = init_chat_model(model="google_genai:gemini-2.5-pro", temperature=0.45)
model_with_tools = llm.bind_tools(all_tools)


def chatbot(state: ChatbotState, store: BaseStore) -> Command:
    namespace: tuple = state["namespace_for_memory"]
    new_element = ("emails",)
    updated_namespace = namespace + new_element
    # fetching data from storage if available
    mail_data_list = store.get(namespace=updated_namespace, key="data")
    unread_mails = store.get(namespace=updated_namespace, key="unread_mails")

    # Extract values or set defaults
    mail_data_list: List[Dict[str, Any]] = (
        mail_data_list.value if mail_data_list else []
    )
    unread_mails: int = unread_mails.value if unread_mails else 0

    # Debug: printing the data fetched from storage
    # print(f"Mail data list from store: {mail_data_list}")
    # print(f"Unread mails from store: {unread_mails}")

    unread_mail_data_list = []
    for i in mail_data_list:
        if i.get("unread"):
            # print(f"Skipping read mail: {i.get('unread')}")
            unread_mail_data_list.append(i)
    print(f"Unread mail data list: {unread_mail_data_list}")

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

        unread_mails: {unread_mails}
        all_mails_data: {mail_data_list}
        </mail_data>
        """
    ).format(
        unread_mails=unread_mails,
        mail_data_list=unread_mail_data_list,
    )

    messages = [
        SystemMessage(content=system_instruction),
    ] + state["messages"]
    # message = llm_with_tools.invoke(
    #     input=messages,
    #     config={
    #         "configurable": {
    #             "model": state["current_model_name"],
    #             "model_provider": state["current_model_provider"],
    #         }
    #     },
    # )
    message = model_with_tools.invoke(messages)
    # print(f"messages: {messages}")
    if isinstance(message, dict):
        message = message.get("messages")
        message = message[-1] if message else None
    return Command(update={"messages": [message]})


def set_initial_model(state: ChatbotState, store: BaseStore, config: RunnableConfig):
    user_id = config["configurable"].get("user_id", "satyam")
    thread_id = config["configurable"].get("thread_id", "test_thread")
    namespace_for_memory = (user_id, thread_id)

    return {
        "namespace_for_memory": namespace_for_memory,
    }


graph_builder.add_node("set_model", set_initial_model)
graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=all_tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "set_model")
graph_builder.add_edge("set_model", "chatbot")
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")

graph = graph_builder.compile(checkpointer=MemorySaver(), store=db_store)
