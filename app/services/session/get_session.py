from app.schemas.chat_session import ChatSession
from .store_session import active_sessions


def get_session(username: str, thread_id: str) -> ChatSession:
    connection_key = (username, thread_id)

    return active_sessions[connection_key]
