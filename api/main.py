from fastapi import FastAPI, WebSocket
from langgraph.config import RunnableConfig
from core import *
from fastapi.middleware.cors import CORSMiddleware
from langgraph.types import Command

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # can alter with time
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from langgraph.types import Interrupt


@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(thread_id: int, websocket: WebSocket):
    await websocket.accept()

    while True:
        input = SequenceState()
        config = RunnableConfig(
            recursion_limit=150, configurable={"thread_id": thread_id}
        )
        async for chunk in graph.astream(
            input=input, config=config, stream_mode="values"
        ):
            for id, value in chunk.items():
                if id == "__interrupt__":
                    print(value)
                    # Send the received data to the other user
                    question = value[0].value["question"]
                    await websocket.send_text(question)
                    response = await websocket.receive_text()
                    await graph.ainvoke(
                        Command(resume={id: response}), config=config, debug=True
                    )
