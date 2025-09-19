from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

# from langchain_community.llms.gpt4all import GPT4All


from app.db.redis import db_store
from app.services.agents.chatbot_agent.states import ChatbotState
from app.services.agents.chatbot_agent.tools import all_tools
from app.services.agents.chatbot_agent.nodes import context_update, chatbot

graph_builder = StateGraph(ChatbotState)

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
