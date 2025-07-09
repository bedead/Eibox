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


with RedisStore.from_conn_string("redis://localhost:6379") as store:
    store.setup()

user_id = "1"
thread_id = "test"
namespace_for_memory = (user_id, thread_id)


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
def show_available_models(
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> ToolMessage:
    """Returns all the llm models currently available to use after switching."""
    return ToolMessage(content=[available_models], tool_call_id=tool_call_id)


@tool
def switch_current_model(
    model_name: str, tool_call_id: Annotated[str, InjectedToolCallId]
) -> str:
    """Tool used to switch between various models to new model_name and model_provider"""
    model_provider = available_models[model_name]["provider"]

    if model_provider:
        return Command(
            update={
                "current_model_name": model_name,
                "current_model_provider": model_provider,
                "messages": [
                    ToolMessage(
                        f"Success switching to {model_name} with provider {model_provider}.",
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )
    else:
        return ToolMessage(f"{model_name} is not available.")


@tool
def get_current_model(
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> str:
    """Returns the current llm model being used."""
    return ToolMessage(
        content={
            "current_model_name": state["current_model_name"],
            "current_model_provider": state["current_model_provider"],
        },
        tool_call_id=tool_call_id,
    )


llm = init_chat_model()
tools = [show_available_models, switch_current_model, get_current_model]
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: ChatbotState, store: BaseStore) -> Command:
    mail = store.get(namespace=namespace_for_memory, key="mail").value
    draft_response = store.get(
        namespace=namespace_for_memory, key="draft_response"
    ).value

    system_instruction = dedent(
        """
            <instructions>
            You are a Expert Assistent, who helps user manage their gmail accounts.
            By reminding user if they have any new important mails to attend, or and asking for apporval on sending draft response to some mail.
            Your tone of speech should be like jarvis from iron man, when informing about the new mail.
            If no mail data is provided, then you will funtion normally and assist user on there queies.
            </instructions>
            
            <mail_data>
            This gmail data is recieved from a background task, and user does not know about this.
            Received Mail data: 
            Mail sender : {mail_sender}
            Mail subject : {mail_subject}
            Mail body : {mail_body}
            Mail date : {mail_date}
            Draft response: {draft_response}
            </mail_data>
            """
    ).format(
        mail_sender=mail.get("sender"),
        mail_subject=mail.get("subject"),
        mail_body=mail.get("body"),
        mail_date=mail.get("date"),
        draft_response=draft_response,
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


def set_initial_model(state: ChatbotState, store: BaseStore):
    return {
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
