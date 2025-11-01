from typing import Any, Dict, Tuple, Optional

from fastapi import WebSocket
from apscheduler.job import Job

from app.db import ChatSession
from app.services.gmail_toolkit import GmailToolKit
from app.core import logger

# 🔧 Force forward reference resolution now that both exist
ChatSession.model_rebuild()

active_sessions: Dict[Tuple[str, str], ChatSession] = {}


def store_session(
    username: str,
    thread_id: str,
    gmail_toolkit: Optional[GmailToolKit] = None,
    websocket: Optional[WebSocket] = None,
    session_job: Optional[Job] = None,
    extra_data: Optional[Dict[str, Any]] = None,
):
    connection_key = (username, thread_id)

    session = ChatSession(
        username=username,
        thread_id=thread_id,
        gmail_toolkit=gmail_toolkit,
        websocket=websocket,
        session_job=session_job,
        extra_data=extra_data,
    )

    active_sessions[connection_key] = session

    logger.debug(f"New session for user {username} is created")
