from .store_session import active_sessions
from app.core.logging import logger


def delete_session(username: str, thread_id: str):
    connection_key = (username, thread_id)

    try:
        if connection_key in active_sessions:
            del active_sessions[connection_key]
            logger.info(f"Chat session of {username} deleted.")
        else:
            logger.info(f"No chat session of {username} found.")

    except Exception as e:
        logger.error(f"Exception occured: {e}")
