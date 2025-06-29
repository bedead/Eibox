from fastapi import APIRouter, WebSocket
from langgraph.config import RunnableConfig
from langgraph.types import Command
from core import sequence_graph, SequenceState, main_graph

router = APIRouter()


@router.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: int):
    await websocket.accept()
    try:
        input = SequenceState()
        config = RunnableConfig(
            recursion_limit=150, configurable={"thread_id": thread_id}
        )
        while True:
            async for chunk in sequence_graph.astream(
                input=input, config=config, stream_mode="updates"
            ):
                for node_id, value in chunk.items():
                    if node_id == "__interrupt__":
                        question = value[0].value.get(
                            "question", "Human input required"
                        )
                        await websocket.send_text(f"[HUMAN_NEEDED] {question}")
                        response = await websocket.receive_text()
                        command = Command(resume=response)
                        resumed_output = await sequence_graph.ainvoke(
                            command, config=config
                        )
                        await websocket.send_text(
                            f"[RESUMED_OUTPUT] {str(resumed_output)}"
                        )
                    else:
                        await websocket.send_text(f"[STEP] {node_id}: {value}")
    except Exception as e:
        await websocket.send_text(f"[ERROR] {str(e)}")
    finally:
        await websocket.close()


def call_graph(user_input, config: RunnableConfig):
    # print(type(user_input))
    events = main_graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
    )
    for event in events:
        if event["llm_node"]["messages"]:
            return event["llm_node"]["messages"].content


@router.websocket("/ws-chatbot/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    await websocket.accept()
    try:
        config = RunnableConfig(
            recursion_limit=150, configurable={"thread_id": thread_id}
        )
        while True:
            message = await websocket.receive_text()
            ai_message = call_graph(user_input=message, config=config)
            print(f"AI response: {ai_message}")
            if ai_message:
                await websocket.send_text(f"{ai_message}")
            else:
                await websocket.send_text("[ERROR] No response from AI")

    except Exception as e:
        await websocket.send_text(f"[ERROR] {str(e)}")
    finally:
        await websocket.close()
