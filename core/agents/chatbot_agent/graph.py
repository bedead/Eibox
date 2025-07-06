from textwrap import dedent
from typing_extensions import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition, InjectedState
from langchain.chat_models import init_chat_model
from core.agents.chatbot_agent.states import ChatbotState
from langgraph.types import Command

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


def chatbot(state: ChatbotState) -> Command:
    message = llm_with_tools.invoke(
        input=state["messages"][-1].content,
        config={
            "configurable": {
                "model": state["current_model_name"],
                "model_provider": state["current_model_provider"],
            }
        },
    )

    # assert len(message.tool_calls) <= 1
    return Command(update={"messages": [message]})


def set_initial_model(state: ChatbotState):
    return {
        "current_model_name": available_models["qwen2.5:0.5b"]["model_name"],
        "current_model_provider": available_models["qwen2.5:0.5b"]["provider"],
    }


def get_gmail(state: ChatbotState):
    ## procesing

    if state.get("pending_mail_read", False):
        print(f"Email summary: {state['email_summary']}")
        state["pending_mail_read"] = False

    if state.get("pending_response_send", False):
        print(f"Draft response : {state['response_email_draft']}")

        state["pending_response_send"] = False

    return state


graph_builder.add_node("set_model", set_initial_model)
graph_builder.add_node("get_gmail", get_gmail)
graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "set_model")
graph_builder.add_edge("set_model", "get_gmail")
graph_builder.add_edge("get_gmail", "chatbot")
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")

graph = graph_builder.compile(checkpointer=MemorySaver())
