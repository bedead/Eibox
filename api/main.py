from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from langgraph.config import RunnableConfig
from core import *

app = FastAPI()


class StartAgent(BaseModel):
    thread_id: int
    running: bool


def initialize_graph(config: RunnableConfig):
    # Initialize the graph with a default thread_id
    initial_state = SequenceState()
    result = graph.ainvoke(initial_state, config=config)
    return result


@app.post("/chat")
async def chat(input: StartAgent):
    if input.running:
        config = RunnableConfig(
            recursion_limit=150, configurable={"thread_id": input.thread_id}
        )
        print(f"Input Thread ID: {input.thread_id}")
        result = initialize_graph(config=config)

    print(f"Chat result: {result}")

    return result
