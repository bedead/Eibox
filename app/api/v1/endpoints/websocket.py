from typing import Dict, Tuple
from fastapi import APIRouter, HTTPException, WebSocket
from langgraph.config import RunnableConfig
from langchain_core.messages import AIMessageChunk
from app.schemas.chat_session import ChatSession
from app.services.agents.chatbot_agent import ChatAgent, ChatbotState
from app.services.gmail.gmail_toolkit import GmailToolKit
from app.utils._api_helper import _to_async_gen
from app.core.logging import logger

router = APIRouter()
# Global session registry
active_sessions: Dict[Tuple[str, str], ChatSession] = {}


def call_graph(user_input: str, username: str, thread_id: str):
    for chunk in ChatAgent.stream(
        input={
            "messages": [{"role": "user", "content": user_input}],
        },
        config={
            "configurable": {
                "thread_id": thread_id,
                "username": username,
            }
        },
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
    logger.info(f"Websocket connection of user - {username} is opened.")

    # job = start_email_scheduler_job(
    #     username=username, user_id=user_id, thread_id=thread_id, interval=30
    # )
    connection_key = (username, thread_id)

    # TODO: #14 update GmailToolkit to use access_token to fetch gmail data
    # Create session object, can also add job=job
    session = ChatSession(
        websocket=websocket,
        username=username,
        thread_id=thread_id,
        # toolkit=GmailToolKit(),
        # job=job,
    )

    active_sessions[connection_key] = session

    try:
        while True:
            message = await websocket.receive_text()
            ai_message_gen = call_graph(
                user_input=message,
                username=username,
                thread_id=thread_id,
            )
            sent = False
            async for chunk in _to_async_gen(ai_message_gen):
                if chunk:
                    await websocket.send_text(chunk)
                    sent = True
            if not sent:
                await websocket.send_text("[ERROR] No response from AI")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        try:
            await websocket.send_text(f"Error: {str(e)}")
        except:
            pass
    finally:
        if connection_key in active_sessions:
            del active_sessions[connection_key]
            logger.info(f"Websocket connection of user - {username} is closed.")
        await websocket.close()


@router.post("/chatbot/v1/close/{username}/{thread_id}")
async def close_websocket(username: str, thread_id: str):
    connection_key = (username, thread_id)
    chat_session = active_sessions.get(connection_key)
    websocket = chat_session.websocket
    if websocket:
        try:
            await websocket.close(code=1000)  # Normal closure
            del active_sessions[connection_key]
            return {
                "status": "closed",
                "username": username,
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to close websocket: {str(e)}"
            )
    else:
        raise HTTPException(status_code=404, detail="WebSocket connection not found")
