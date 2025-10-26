"""
Chat session model definition.

This module defines the `ChatSession` class, which represents a user’s active
chat session. It stores metadata such as username, thread ID, WebSocket
connection, Gmail toolkit instance, scheduled job, and any extra session data.

The model uses Pydantic for validation and supports arbitrary types
(e.g., FastAPI WebSocket, APScheduler Job, and custom GmailToolKit).
"""

from typing import Any, Dict, Optional, TYPE_CHECKING

from apscheduler.job import Job
from fastapi import WebSocket
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from app.services import GmailToolKit


class ChatSession(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )  # allows Job, WebSocket, GmailToolKit

    username: str
    thread_id: str
    websocket: Optional[WebSocket] = None
    gmail_toolkit: Optional['GmailToolKit'] = None
    session_job: Optional[Job] = None
    extra_data: Optional[Dict[str, Any]] = None
