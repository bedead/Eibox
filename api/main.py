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

app.debug = True

# from langgraph.types import Interrupt


@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: int):
    await websocket.accept()

    try:
        # Initial state
        input = SequenceState()
        config = RunnableConfig(
            recursion_limit=150, configurable={"thread_id": thread_id}
        )

        # Stream the graph
        while True:
            async for chunk in graph.astream(
                input=input, config=config, stream_mode="values"
            ):
                for node_id, value in chunk.items():
                    if node_id == "__interrupt__":
                        # Assume interrupt value contains a "question" key
                        question = value[0].value.get(
                            "question", "Human input required"
                        )
                        await websocket.send_text(f"[HUMAN_NEEDED] {question}")

                        # Wait for response from the user
                        response = await websocket.receive_text()

                        # Resume the graph with human input
                        command = Command(resume=response)
                        resumed_output = await graph.ainvoke(command, config=config)

                        # You could send the final result if you want:
                        await websocket.send_text(
                            f"[RESUMED_OUTPUT] {str(resumed_output)}"
                        )
                        # Stop after one resume; or continue if loop is needed

                    else:
                        await websocket.send_text(f"[STEP] {node_id}: {value}")

    except Exception as e:
        await websocket.send_text(f"[ERROR] {str(e)}")
    finally:
        await websocket.close()
