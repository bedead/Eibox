"""
API endpoints for testing and managing Google account sessions and chatbot websocket connections.
This module provides the following endpoints:
- POST /get_google_account/: Retrieve Google account information for a given username.
- WebSocket /chatbot/{username}/{thread_id}: Open a websocket connection for chatbot interaction, managing user sessions.
- POST /chatbot/close/{username}/{thread_id}: Close an active chatbot websocket session and clean up resources.
- GET /health: Health check endpoint to verify the service status.
Author: Satyam Mishra
Date: 14-09-2025
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from app.core.logging import logger
from app.db.repos.gmail.get_gmail_accounts import get_gmail_account
from app.schemas.gmail_account import GmailAccount
from app.schemas.chat_session import ChatSession
from app.services.gmail.gmail_toolkit import GmailToolKit
from app.services.session.get_session import get_session
from app.services.session.delete_session import delete_session
from app.services.session.store_session import store_session


router = APIRouter()
namespace_for_memory = ("auth", "user")


class GoogleAccountRequest(BaseModel):
    username: str


@router.post("/get_google_account/")
def get_google_account(token: GoogleAccountRequest):
    try:
        return get_gmail_account(
            username=token.username,
            namespace_for_memory=namespace_for_memory,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save tokens: {str(e)}")


@router.websocket("/chatbot/{username}/{thread_id}")
async def open_chat_websocket(websocket: WebSocket, username: str, thread_id: str):
    await websocket.accept()
    logger.debug(f"Websocket connection of user - {username} is opened.")
    # job = start_email_scheduler_job(
    #     username=username, user_id=user_id, thread_id=thread_id, interval=30
    # )
    session = get_session(username=username, thread_id=thread_id)
    if not session:
        logger.debug(
            f"Session object not found creating new session for {username} with thread_id {thread_id}"
        )
        data: List[GmailAccount] = get_gmail_account(
            username=username, namespace_for_memory=namespace_for_memory
        )
        # print(f"Gmail_accounts : {data}")
        gmail_toolkit: Optional[GmailToolKit] = None
        if data and len(data) > 0:
            gmail_toolkit = GmailToolKit(
                gmail_account=data[0],
            )

        # store session
        store_session(
            websocket=websocket,
            username=username,
            thread_id=thread_id,
            gmail_toolkit=gmail_toolkit,
        )

    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"AI : {message} - from {username}")

    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        delete_session(username=username, thread_id=thread_id)
        logger.debug(f"Websocket connection of user - {username} is closed.")
        await websocket.close()


@router.post("/chatbot/close/{username}/{thread_id}")
async def close_chat_websocket(username: str, thread_id: str):
    session: ChatSession = get_session(username, thread_id)
    websocket: Optional[WebSocket | None] = session.websocket

    try:
        delete_session(username, thread_id)
        # Making sure that websocket object is not None and session has returned websocket object
        if websocket != None:
            # Already closed?
            if websocket.client_state.name == "DISCONNECTED":
                # cleanup stale session
                return {
                    "status": "websocket already closed",
                    "username": username,
                    "thread_id": thread_id,
                }
            else:
                await websocket.close(
                    code=1000, reason="user disconnected"
                )  # Normal closure
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


@router.get("/health")
def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "ok", "message": "Auth service is running"}
