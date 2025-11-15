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

from fastapi import APIRouter, HTTPException, WebSocket

from app.core import logger
from app.db import ChatSession
from app.services import (
    delete_session,
    get_session,
    close_websocket_session,
    init_or_get_session,
    call_main_agent,
)

router = APIRouter()

namespace_for_memory = ("auth", "user")


@router.websocket("/open/{username}/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, username: str, thread_id: str):
    # pylint: disable=duplicate-code
    # WebSocket endpoint shares logic with REST close route, intentional duplication

    await websocket.accept()
    logger.debug(f"Websocket connection of user - {username} is opened.")
    s = init_or_get_session(
        username=username,
        thread_id=thread_id,
        websocket=websocket,
        namespace_for_memory=namespace_for_memory,
    )

    try:
        while True:
            message = await websocket.receive_text()

            # Decide whether to stream or not
            streaming = False
            async for ai_output in await call_main_agent(
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
    session: Optional[ChatSession] = get_session(username, thread_id)
    if not session:
        return HTTPException(status_code=404, detail="Session not found")

    websocket: Optional[WebSocket | None] = session.websocket

    return await close_websocket_session(
        username=username, thread_id=thread_id, websocket=websocket
    )
