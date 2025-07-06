from fastapi import APIRouter, WebSocket
from langgraph.config import RunnableConfig
from langgraph.types import Command
from langchain_core.messages import AIMessageChunk
from core import ChatAgent, ChatbotState
from core.job_scheduler.jobs import (
    start_email_scheduler_job,
    delete_email_scheduler_job,
)
from .._helper import job_to_str

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


async def call_graph(user_input, config: RunnableConfig):
    # print(type(user_input))
    async for chunk in ChatAgent.astream(
        input={"messages": [{"role": "user", "content": user_input}]},
        config={"configurable": {"thread_id": "test"}},
        stream_mode="messages",
    ):
        if isinstance(chunk, tuple):
            message_chunk, metadata = chunk
            if isinstance(message_chunk, AIMessageChunk):
                return message_chunk.content


@router.websocket("/chatbot/v1/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    await websocket.accept()
    job = start_email_scheduler_job(thread_id=thread_id)
    try:
        config = RunnableConfig(configurable={"thread_id": thread_id})
        await websocket.send_text(job_to_str(job=job))
        while True:
            message = await websocket.receive_text()
            ai_message = await call_graph(user_input=message, config=config)
            print(f"AI response: {ai_message}")
            if ai_message:
                await websocket.send_text(f"{ai_message}")
            else:
                await websocket.send_text("[ERROR] No response from AI")

    except Exception as e:
        await websocket.send_text(f"[ERROR] {str(e)}")
    finally:
        await websocket.close()
