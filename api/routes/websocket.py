from fastapi import APIRouter, WebSocket
from langgraph.config import RunnableConfig
from langchain_core.messages import AIMessageChunk
from core import ChatAgent, ChatbotState
from core.job_scheduler.jobs import (
    start_email_scheduler_job,
    delete_email_scheduler_job,
)
from .._helper import _to_async_gen

router = APIRouter()


@router.websocket("/test/chatbot/v1/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"AI : {message}")

    except Exception as e:
        await websocket.send_text(f"[ERROR] {str(e)}")
    finally:
        await websocket.close()


def call_graph(user_input: str, user_id: str, thread_id: str):
    # print(type(user_input))
    for chunk in ChatAgent.stream(
        input={
            "messages": [{"role": "user", "content": user_input}],
        },
        config={"configurable": {"thread_id": thread_id, "user_id": user_id}},
        stream_mode="messages",
        debug=True,
    ):
        if isinstance(chunk, tuple):
            message_chunk, metadata = chunk
            if (
                isinstance(message_chunk, AIMessageChunk)
                and metadata["langgraph_node"] == "chatbot"
            ):
                yield message_chunk.content


@router.websocket("/chatbot/v1/{user_id}/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, thread_id: str):
    await websocket.accept()
    # job = start_email_scheduler_job(user_id=user_id, thread_id=thread_id, interval=30)
    try:
        while True:
            message = await websocket.receive_text()
            ai_message_gen = call_graph(
                user_input=message, user_id=user_id, thread_id=thread_id
            )
            sent = False
            async for chunk in _to_async_gen(ai_message_gen):
                if chunk:
                    await websocket.send_text(chunk)
                    sent = True
            if not sent:
                await websocket.send_text("[ERROR] No response from AI")

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        await websocket.send_text(f"[ERROR] {str(e)}")
    # finally:
    #     await websocket.close()
