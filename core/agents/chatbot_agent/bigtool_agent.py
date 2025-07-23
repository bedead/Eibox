from langchain.chat_models import init_chat_model
from langgraph_bigtool import create_agent
from core.storage.setup import db_store
from core.agents.chatbot_agent.tools import all_tools
from core.storage.vector_store.custom_tools_retriever import retrieve_tools

# Register tools with IDs
tool_registry = {tool.name: tool for tool in all_tools}

llm = init_chat_model("google_genai:gemini-2.0-flash")
builder = create_agent(
    llm=llm, tool_registry=tool_registry, retrieve_tools_function=retrieve_tools
)
agent = builder.compile(store=db_store)
