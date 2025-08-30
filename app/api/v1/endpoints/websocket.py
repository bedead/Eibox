from typing import Dict, Tuple
from fastapi import APIRouter, HTTPException, WebSocket
from typing import List
from langgraph.config import RunnableConfig
from langchain_core.messages import AIMessageChunk
from app.core.config import settings
from app.db.repos.gmail.save_refreshed_tokens import save_refreshed_tokens
from app.db.repos.gmail.get_gmail_accounts import get_gmail_account
from app.schemas.gmail_account import GmailAccount
from app.services.agents.chatbot_agent import ChatAgent, ChatbotState
from app.services.gmail.gmail_toolkit import GmailToolKit
from app.services.job_scheduler.jobs import start_email_scheduler_job
from app.services.session.delete_session import delete_session
from app.services.session.get_session import get_session
from app.services.session.store_session import store_session
from app.utils._api_helper import _to_async_gen
from app.core.logging import logger

router = APIRouter()

namespace_for_memory = ("auth", "user")


def call_graph(user_input: str, username: str, thread_id: str):
    for chunk in ChatAgent.stream(
        input={
            "messages": [{"role": "user", "content": user_input}],
            "semantic_memory": "",
            "episodic_memory": "",
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
    logger.debug(f"Websocket connection of user - {username} is opened.")

    # Run email fetch scheduler job if enabled fron configs
    job = None  # Empty job to avoid reference before assignment error
    if settings.RUN_JOB_SCHEDULER:
        job = start_email_scheduler_job(
            username=username, thread_id=thread_id, interval=30
        )

    session = get_session(username=username, thread_id=thread_id)
    if not session:
        logger.debug(
            f"Session object not found creating new session for {username} with thread_id {thread_id}"
        )
        data: List[GmailAccount] = get_gmail_account(
            username=username, namespace_for_memory=namespace_for_memory
        )
        # print(f"Gmail_accounts : {data}")
        gmail_toolkit: GmailToolKit = None
        if data and len(data) > 0:
            gmail_toolkit = GmailToolKit(
                gmail_account=data[0],
                token_refresh_callback=save_refreshed_tokens,
                username=username,
            )

        # store session with whatever data is available
        store_session(
            websocket=websocket,
            username=username,
            thread_id=thread_id,
            gmail_toolkit=gmail_toolkit,
            session_job=job if job else None,
        )

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
        delete_session(username=username, thread_id=thread_id)
        logger.debug(f"Websocket connection of user - {username} is closed.")
        await websocket.close()


@router.post("/chatbot/v1/close/{username}/{thread_id}")
async def close_websocket(username: str, thread_id: str):
    session = get_session(username, thread_id)
    websocket = session.websocket

    try:
        delete_session(username, thread_id)
        # Already closed?
        if websocket.client_state.name == "DISCONNECTED":
            # cleanup stale session
            return {
                "status": "websocket already closed",
                "username": username,
                "thread_id": thread_id,
            }
        else:
            await websocket.close(code=1000)  # Normal closure
            return {
                "status": "websocket closed and cleared session",
                "username": username,
                "thread_id": thread_id,
            }

    except Exception as e:
        logger.error(f"500: Failed to close websocket: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to close websocket: {str(e)}"
        )
