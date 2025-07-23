import math, types, uuid
from langchain.chat_models import init_chat_model
from langchain.embeddings import init_embeddings
from langgraph.store.memory import InMemoryStore
from langgraph_bigtool import create_agent
from core.agents.chatbot_agent.tools import all_tools
from core.storage.setup import vector_store

# Register tools with IDs
tool_registry = {str(uuid.uuid4()): t for t in all_tools}

llm = init_chat_model("google_genai:gemini-2.0-flash")
builder = create_agent(llm, tool_registry)
agent = builder.compile(store=vector_store)
