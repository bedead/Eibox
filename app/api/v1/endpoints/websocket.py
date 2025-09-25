"""
WebSocket and API endpoints for managing user sessions and email interactions.
This module provides FastAPI routes for opening and closing WebSocket connections
associated with user sessions and Gmail accounts. It handles session creation,
email scheduler job initiation, message streaming, and session cleanup.
Endpoints:
    - /open/{username}/{thread_id} (WebSocket): Opens a WebSocket connection for a user and thread,
      initializes session and email scheduler job, and streams AI responses.
    - /close/{username}/{thread_id} (POST): Closes the WebSocket connection and cleans up the session.
Author: Satyam Mishra
Date: 14-09-2025
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, WebSocket

from app.core.config import settings
from app.core.logging import logger
from app.db.repos.auth.get_user_data import get_user_data
from app.schemas.chat_session import ChatSession
from app.services.jobs import start_email_scheduler_job
from app.services.session.delete_session import delete_session
from app.services.session.get_session import get_session
from app.services.session.session_utils import (
    close_websocket_session,
    init_or_get_session,
)
from app.utils._api_helper import call_graph, minutes_to_seconds, second_to_minutes

router = APIRouter()

namespace_for_memory = ("auth", "user")


@router.websocket("/open/{username}/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, username: str, thread_id: str):
    # pylint: disable=duplicate-code
    # WebSocket endpoint shares logic with REST close route, intentional duplication

    await websocket.accept()
    logger.debug(f"Websocket connection of user - {username} is opened.")

    user_data: Dict[str, Any] = get_user_data(username, namespace_for_memory)
    # Ensure correct parsing of auto_email_monitoring as boolean
    app_settings: Dict[str, Any] = user_data.get("app_settings", {})
    auto_email_monitoring: bool = app_settings.get("auto_email_monitoring", False)
    email_monitoring_frequency: int = app_settings.get(
        "email_monitoring_frequency", 30
    )  # in minutes
    email_monitoring_frequency_seconds: int = minutes_to_seconds(
        email_monitoring_frequency
    )  # in seconds
    logger.debug(f"Auto Email Monitoring Enabled: {auto_email_monitoring}")
    logger.debug(
        f"Auto Email Fetch Frequency in seconds: {email_monitoring_frequency_seconds}"
    )

    # Run email fetch scheduler job if enabled fron configs and user settings has auto_email_monitoring enabled
    job = None  # Empty job to avoid reference before assignment error
    if settings.RUN_JOB_SCHEDULER and auto_email_monitoring:
        logger.debug("Starting auto email fetch scheduler job...")
        job = start_email_scheduler_job(
            username=username,
            thread_id=thread_id,
            interval=email_monitoring_frequency_seconds,
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

            # Decide whether to stream or not
            streaming = False
            async for ai_output in await call_graph(
                user_input=message,
                username=username,
                thread_id=thread_id,
                streaming=streaming,
            ):
                if isinstance(ai_output, str):
                    logger.debug(f"AI Output: {ai_output}")
                    await websocket.send_text(ai_output)

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


@router.post("/close/{username}/{thread_id}")
async def close_websocket(username: str, thread_id: str):
    session: ChatSession = get_session(username, thread_id)
    websocket: Optional[WebSocket | None] = session.websocket

    return await close_websocket_session(
        username=username, thread_id=thread_id, websocket=websocket
    )
