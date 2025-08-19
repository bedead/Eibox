# Session object: stores socket + extra context
from typing import Any, Dict
from fastapi import WebSocket

from app.services.gmail.gmail_toolkit import GmailToolKit


class ChatSession:
    def __init__(
        self,
        websocket: WebSocket,
        username: str,
        user_id: str,
        thread_id: str,
        toolkit: GmailToolKit = None,
        job=None,
    ):
        self.websocket: WebSocket = websocket
        self.username: str = username
        self.user_id: str = user_id
        self.thread_id: str = thread_id
        self.gmail_toolkit: GmailToolKit = toolkit
        self.job = job
        self.extra_data: Dict[str, Any] = {}  # <-- free space for anything else
