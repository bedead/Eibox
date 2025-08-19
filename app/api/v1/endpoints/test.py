from typing import Dict, List, Tuple
from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel
from app.db.repos.gmail.get_gmail_accounts import get_gmail_account
from dotenv import load_dotenv

from app.schemas.chat_session import ChatSession
from app.schemas.gmail_account import GmailAccount
from app.services.gmail.gmail_toolkit import GmailToolKit
from app.services.job_scheduler.jobs import start_email_scheduler_job
from app.core.logging import logger

load_dotenv()


router = APIRouter()
namespace_for_memory = ("auth", "user")
active_sessions: Dict[Tuple[str, str], ChatSession] = {}


class GoogleAccountRequest(BaseModel):
    username: str


@router.post("/get_google_account/v1")
def get_google_account(token: GoogleAccountRequest):
    try:
        return get_gmail_account(
            username=token.username,
            namespace_for_memory=namespace_for_memory,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save tokens: {str(e)}")


@router.websocket("/chatbot/v1/{username}/{thread_id}")
async def open_chat_websocket(websocket: WebSocket, username: str, thread_id: str):
    await websocket.accept()
    logger.info(f"Websocket connection of user - {username} is opened.")
    # job = start_email_scheduler_job(
    #     username=username, user_id=user_id, thread_id=thread_id, interval=30
    # )
    data: List[GmailAccount] = get_gmail_account(
        username=username, namespace_for_memory=namespace_for_memory
    )
    gmail_toolkit = GmailToolKit(gmail_account=data[0])

    connection_key = (username, thread_id)

    # TODO: #14 update GmailToolkit to use access_token to fetch gmail data
    # Create session object, can also add job=job
    session = ChatSession(
        websocket=websocket,
        username=username,
        thread_id=thread_id,
        toolkit=gmail_toolkit,
    )

    active_sessions[connection_key] = session

    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"AI : {message} - from {username}")

    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        if connection_key in active_sessions:
            del active_sessions[connection_key]
            logger.info(f"Websocket connection of user - {username} is closed.")
        await websocket.close()


@router.post("/chatbot/v1/close/{username}/{thread_id}")
async def close_chat_websocket(username: str, thread_id: str):
    connection_key = (username, thread_id)
    chat_session = active_sessions.get(connection_key)

    if not chat_session:
        logger.error(f"404: WebSocket connection session not found")
        raise HTTPException(
            status_code=404, detail="WebSocket connection session not found"
        )

    websocket = chat_session.websocket

    # Already closed?
    if websocket.client_state.name == "DISCONNECTED":
        # cleanup stale session
        if connection_key in active_sessions:
            del active_sessions[connection_key]
        return {
            "status": "already closed",
            "username": username,
            "thread_id": thread_id,
        }

    try:
        await websocket.close(code=1000)  # Normal closure
        if connection_key in active_sessions:
            del active_sessions[connection_key]
        return {
            "status": "closed",
            "username": username,
            "thread_id": thread_id,
        }
    except Exception as e:
        logger.error(f"500: Failed to close websocket: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to close websocket: {str(e)}"
        )
