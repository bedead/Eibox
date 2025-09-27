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

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel
from dotenv import load_dotenv

from app.core.config import settings
from app.db.repos.auth.get_user_data import get_user_data
from app.services.jobs import start_email_scheduler_job
from app.services.session.session_utils import (
    close_websocket_session,
    init_or_get_session,
)

load_dotenv()

from app.core.logging import logger
from app.db.repos.gmail.accounts import get_gmail_account
from app.schemas.chat_session import ChatSession
from app.services.session.get_session import get_session
from app.services.session.delete_session import delete_session


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
    # pylint: disable=duplicate-code
    # Test endpoint shares logic with REST close route, intentional duplication

    await websocket.accept()
    logger.debug(f"Websocket connection of user - {username} is opened.")

    user_data: Dict[str, Any] = get_user_data(username, namespace_for_memory)
    auto_email_monitoring: bool = user_data.get("app_settings", {}).get(
        "auto_email_monitoring", False
    )

    # Run email fetch scheduler job if enabled fron configs
    job = None  # Empty job to avoid reference before assignment error
    if settings.RUN_JOB_SCHEDULER and auto_email_monitoring:
        logger.debug("Starting auto email fetch scheduler job...")
        job = start_email_scheduler_job(
            username=username, thread_id=thread_id, interval=1800
        )

    session = init_or_get_session(
        username=username,
        thread_id=thread_id,
        websocket=websocket,
        namespace_for_memory=namespace_for_memory,
        session_job=job,
        extra_data=user_data,
    )

    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"AI : {message} - from {username}")

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        try:
            await websocket.send_text(f"Error: {str(e)}")
        except Exception as e:
            logger.error(f"Websocket Error: {str(e)}", exc_info=True)
    finally:
        delete_session(username=username, thread_id=thread_id)
        logger.debug(f"Websocket connection of user - {username} is closed.")
        await websocket.close()


@router.post("/chatbot/close/{username}/{thread_id}")
async def close_chat_websocket(username: str, thread_id: str):
    session: ChatSession = get_session(username, thread_id)
    websocket: Optional[WebSocket | None] = session.websocket

    return await close_websocket_session(
        username=username, thread_id=thread_id, websocket=websocket
    )


@router.get("/health")
def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "ok", "message": "Auth service is running"}
