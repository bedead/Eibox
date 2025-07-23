from textwrap import dedent
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition, InjectedState
from core.agents.chatbot_agent.states import ChatbotState
from langgraph.types import Command
from langgraph.store.base import BaseStore
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from core.storage.setup import db_store
from core.agents.chatbot_agent.bigtool_agent import agent

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
    message = agent.invoke({"messages": messages})
    # print(f"messages: {messages}")
    if isinstance(message, dict):
        message = message.get("messages")
        message = message[-1] if message else None
    print(f"message: {message}")
    return Command(update={"messages": [message]})


def set_initial_model(state: ChatbotState, store: BaseStore, config: RunnableConfig):
    user_id = config["configurable"].get("user_id", "1")
    thread_id = config["configurable"].get("thread_id", "test")
    namespace_for_memory = (user_id, thread_id)

    return {
        "namespace_for_memory": namespace_for_memory,
    }


graph_builder.add_node("set_model", set_initial_model)
graph_builder.add_node("chatbot", chatbot)

# tool_node = ToolNode(tools=tool_registry)
# graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "set_model")
graph_builder.add_edge("set_model", "chatbot")
# graph_builder.add_conditional_edges(
#     "chatbot",
#     tools_condition,
# )
# graph_builder.add_edge("tools", "chatbot")

graph = graph_builder.compile(checkpointer=MemorySaver(), store=db_store)
