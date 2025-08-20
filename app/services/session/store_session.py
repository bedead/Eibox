from typing import Dict, Tuple

from app.schemas.chat_session import ChatSession
from app.core.logging import logger

active_sessions: Dict[Tuple[str, str], ChatSession] = {}


def store_session(username: str, thread_id: str, websocket=None, gmail_toolkit=None):
    connection_key = (username, thread_id)

    session = ChatSession(
        websocket=websocket,
        username=username,
        thread_id=thread_id,
        toolkit=gmail_toolkit,
    )

    active_sessions[connection_key] = session

    logger.debug(f"New session for user {username} is created")
