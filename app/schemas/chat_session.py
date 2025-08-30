# Session object: stores socket + extra context
from typing import Any, Dict
from fastapi import WebSocket

from app.services.gmail.gmail_toolkit import GmailToolKit


class ChatSession:
    def __init__(
        self,
        websocket: WebSocket,
        username: str,
        thread_id: str,
        toolkit: GmailToolKit = None,
        session_job=None,
        extra_data: Dict[str, Any] = None,
    ):
        self.websocket: WebSocket = websocket
        self.username: str = username
        self.thread_id: str = thread_id
        self.gmail_toolkit: GmailToolKit = toolkit
        self.session_job = session_job
        self.extra_data: Dict[str, Any] = extra_data
