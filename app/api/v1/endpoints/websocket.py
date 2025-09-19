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

from typing import Optional

from fastapi import APIRouter, WebSocket

from app.core.config import settings
from app.core.logging import logger
from app.schemas.chat_session import ChatSession
from app.services.job_scheduler.jobs import start_email_scheduler_job
from app.services.session.delete_session import delete_session
from app.services.session.get_session import get_session
from app.services.session.session_utils import (
    close_websocket_session,
    init_or_get_session,
)
from app.services.session.store_session import store_session
from app.utils._api_helper import call_graph

router = APIRouter()

namespace_for_memory = ("auth", "user")


@router.websocket("/open/{username}/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, username: str, thread_id: str):
    # pylint: disable=duplicate-code
    # WebSocket endpoint shares logic with REST close route, intentional duplication

    await websocket.accept()
    logger.debug(f"Websocket connection of user - {username} is opened.")

    # Run email fetch scheduler job if enabled fron configs
    job = None  # Empty job to avoid reference before assignment error
    if settings.RUN_JOB_SCHEDULER:
        job = start_email_scheduler_job(
            username=username, thread_id=thread_id, interval=30
        )

    session = init_or_get_session(username, thread_id, websocket, namespace_for_memory)

    try:
        while True:
            message = await websocket.receive_text()

            # Decide whether to stream or not
            streaming = False
            if streaming:
                for chunk in call_graph(
                    user_input=message,
                    username=username,
                    thread_id=thread_id,
                    streaming=streaming,
                ):
                    if isinstance(chunk, str):
                        await websocket.send_text(chunk)
            else:
                ai_output = call_graph(
                    user_input=message,
                    username=username,
                    thread_id=thread_id,
                    streaming=streaming,
                )
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
