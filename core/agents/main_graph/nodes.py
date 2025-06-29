from langchain.chat_models import init_chat_model

from .states import MainState
from .tools import human_assistance

llm_model = init_chat_model(model="gemini-1.5-flash", model_provider="google_genai")
llm_model = llm_model.bind_tools([human_assistance])


def llm(state: MainState):
    """
    Generate a response from the LLM based state messages.
    """
    msg = state["messages"]
    response = llm_model.invoke(msg)
    return {"messages": response}
