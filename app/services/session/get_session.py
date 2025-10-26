from typing import Optional

from app.db import ChatSession
from app.core import logger
from .store_session import active_sessions


def get_session(username: str, thread_id: str) -> Optional[ChatSession]:
    try:
        connection_key = (username, thread_id)
        session = active_sessions[connection_key]
        if session:
            logger.debug(f"Existing session found for username {username} ")
            return session
    except Exception as e:
        logger.warning(
            f"{e} error occured while reading session for username {username}."
        )
