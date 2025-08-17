from fastapi import APIRouter, WebSocket
from langgraph.config import RunnableConfig
from langchain_core.messages import AIMessageChunk
from app.services.agents.chatbot_agent import ChatAgent, ChatbotState
from app.services.job_scheduler.jobs import (
    start_email_scheduler_job,
    delete_email_scheduler_job,
)
from ....utils._api_helper import _to_async_gen

router = APIRouter()


@router.websocket("/test/chatbot/v1/{username}/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, username: str, thread_id: str):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"AI : {message} - from {username}")

    except Exception as e:
        await websocket.send_text(f"[ERROR] {str(e)}")
    finally:
        await websocket.close()


def call_graph(user_input: str, username: str, thread_id: str):
    # print(type(user_input))
    for chunk in ChatAgent.stream(
        input={
            "messages": [{"role": "user", "content": user_input}],
        },
        config={"configurable": {"thread_id": thread_id, "user_id": username}},
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


@router.websocket("/chatbot/v1/{username}/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, username: str, thread_id: str):
    await websocket.accept()
    # job = start_email_scheduler_job(user_id=user_id, thread_id=thread_id, interval=30)
    try:
        while True:
            message = await websocket.receive_text()
            ai_message_gen = call_graph(
                user_input=message, username=username, thread_id=thread_id
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
