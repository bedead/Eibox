from .states import ManagerState
from ..chatbot_agent import ChatbotState, ChatAgent
from ..email_agent import EmailState, EmailAgent


from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command


def set_state(state: ManagerState) -> Command:
    return Command(update={"pending_email": False})


def call_chatbotAgent(state: ManagerState) -> Command:
    response = ChatAgent.invoke(input={"messages": state["messages"]})
    msgs = response.get("messages")

    if isinstance(msgs, list) and all(hasattr(m, "type") for m in msgs):
        return Command(update={"messages": msgs})
    else:
        raise ValueError("Invalid message format in chatbot agent response")


async def call_emailAgent(state: ManagerState) -> Command:
    pending_email = state.get("pending_email")
    if not pending_email:
        response = await EmailAgent.ainvoke(input={"pending_email": pending_email})

        email_data = response.get("email", {})

        return Command(
            update={
                "pending_email": response.get("is_response_needed", False),
                "email_summary": response.get("email_summary", None),
                "response_draft": response.get("response_email_draft", None),
            }
        )
    return Command(goto=END)


graph_builder = StateGraph(state_schema=ManagerState)

# graph_builder.add_node("set_state", set_state)
graph_builder.add_node("chatbotAgent", call_chatbotAgent)
graph_builder.add_node("emailAgent", call_emailAgent)

graph_builder.add_edge(START, "chatbotAgent")
graph_builder.add_edge(START, "emailAgent")

graph = graph_builder.compile(checkpointer=MemorySaver())
