from app.schemas.chat_session import ChatSession
from .store_session import active_sessions
from app.core.logging import logger


def get_session(username: str, thread_id: str) -> ChatSession:
    try:
        connection_key = (username, thread_id)
        session = active_sessions[connection_key]
        if session:
            logger.debug(f"Existing session found for username {username} ")
            return session
    except Exception as e:
        logger.error(
            f"{e} error occured while reading session for username {username}."
        )
