from textwrap import dedent
from typing import List, Dict, Any
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition, InjectedState
from app.services.agents.chatbot_agent.states import ChatbotState
from langgraph.types import Command
from langgraph.store.base import BaseStore
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model
from app.db.redis import db_store
from app.services.agents.chatbot_agent.tools import all_tools
from app.utils._prompts import (
    CHATBOT_SYSTEM_INSTRUCTION,
    EPISODIC_MEMORY_PROMPT,
    SEMANTIC_MEMORY_PROMPT,
)
from app.utils.common import clean_and_parse_ai_output

graph_builder = StateGraph(ChatbotState)
llm = init_chat_model(model="google_genai:gemini-2.0-flash", temperature=0.45)
model_with_tools = llm.bind_tools(all_tools)


def context_update(
    state: ChatbotState, store: BaseStore, config: RunnableConfig
) -> Command:
    # Data extraction from config
    username = config["configurable"].get("user_id", "satyam")
    thread_id = config["configurable"].get("thread_id", "test_thread")

    namespace_for_memory = (username.lower(), thread_id)
    namespace_for_user_info = ("auth", "user")

    semantic_memory_key = f"user-semantic-memory:{username.lower()}"
    episodic_memory_key = f"user-episodic-memory:{username.lower()}"

    # Get past memory
    semantic_memory = store.get(
        namespace=namespace_for_user_info, key=semantic_memory_key
    )
    episodic_memory = store.get(
        namespace=namespace_for_user_info, key=episodic_memory_key
    )

    llm = init_chat_model(model="google_genai:gemini-2.0-flash", temperature=0.45)
    # Call LLM if semantic memory is available
    # update data
    updated_semantic_memory = llm.invoke(
        SEMANTIC_MEMORY_PROMPT.replace(
            "{data}",
            semantic_memory.value if semantic_memory else "",
        ).replace(
            "{context}", state["messages"][-1].content if state["messages"] else ""
        )
    )

    # updated_semantic_memory = clean_and_parse_ai_output(updated_semantic_memory.content)
    # print("Updated Semantic Memory:", updated_semantic_memory)

    # store updated semantic memory
    store.put(
        namespace=namespace_for_user_info,
        key=semantic_memory_key,
        value=updated_semantic_memory.content,
    )

    updated_episodic_memory = llm.invoke(
        EPISODIC_MEMORY_PROMPT.replace(
            "{data}",
            episodic_memory.value if episodic_memory else "",
        ).replace(
            "{context}",
            state["messages"][-1].content if state["messages"] else "",
        )
    )

    # store updated episodic memory
    store.put(
        namespace=namespace_for_user_info,
        key=episodic_memory_key,
        value=updated_episodic_memory.content,
    )

    return Command(
        update={
            "semantic_memory": (
                updated_semantic_memory if updated_semantic_memory else ""
            ),
            "episodic_memory": (
                updated_episodic_memory if updated_episodic_memory else ""
            ),
            "namespace_for_gmail": namespace_for_memory,
        }
    )


def chatbot(state: ChatbotState, store: BaseStore) -> Command:
    namespace: tuple = state["namespace_for_gmail"]
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
    semantic_memory = state["semantic_memory"]
    episodic_memory = state["episodic_memory"]

    # # Debugging print statements
    # print(f"Semantic memory: {semantic_memory}")
    # print(f"Episodic memory: {episodic_memory}")

    unread_mail_data_list = []
    for i in mail_data_list:
        if i.get("unread"):
            # print(f"Skipping read mail: {i.get('unread')}")
            unread_mail_data_list.append(i)
    print(f"Unread mail data list: {unread_mail_data_list}")
    print(f"Unread mails: {unread_mails}")

    system_instruction = CHATBOT_SYSTEM_INSTRUCTION.format(
        unread_mails=unread_mails,
        mail_data_list=unread_mail_data_list,
        semantic_memory=semantic_memory if semantic_memory else "",
        episodic_memory=episodic_memory if episodic_memory else "",
    )

    messages = [
        SystemMessage(content=system_instruction),
    ] + state["messages"]

    message = model_with_tools.invoke(messages)
    if isinstance(message, dict):
        message = message.get("messages")
        message = message[-1] if message else None
    return Command(update={"messages": [message]})


graph_builder.add_node("context_update", context_update)
graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=all_tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "context_update")
graph_builder.add_edge("context_update", "chatbot")
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")

graph = graph_builder.compile(checkpointer=MemorySaver(), store=db_store)
