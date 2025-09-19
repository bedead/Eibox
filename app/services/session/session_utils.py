from typing import Optional, List, Tuple, Union

from fastapi import HTTPException, WebSocket

from app.core.logging import logger
from app.db.repos.gmail.get_gmail_accounts import get_gmail_account
from app.schemas.chat_session import ChatSession
from app.schemas.gmail_account import GmailAccount
from app.services.gmail.gmail_toolkit import GmailToolKit
from app.services.session.delete_session import delete_session
from app.services.session.get_session import get_session
from app.services.session.store_session import store_session


def init_or_get_session(
    username: str,
    thread_id: str,
    websocket: WebSocket,
    namespace_for_memory: Tuple[str, str],
):
    session: ChatSession = get_session(username=username, thread_id=thread_id)
    if session:
        return session

    logger.debug(
        f"Session not found. Creating new session for {username} with thread_id {thread_id}"
    )
    data: List[GmailAccount] = get_gmail_account(
        username=username, namespace_for_memory=namespace_for_memory
    )
    gmail_toolkit: Optional[GmailToolKit] = None
    if data and len(data) > 0:
        gmail_toolkit = GmailToolKit(
            gmail_account=data[0],
        )

    # print(f"Gmail data: {data}")

    store_session(
        username=username,
        thread_id=thread_id,
        gmail_toolkit=gmail_toolkit,
        websocket=websocket,
    )


async def close_websocket_session(
    username: str, thread_id: str, websocket: Union[WebSocket, None]
) -> dict:
    try:
        delete_session(username, thread_id)
        if websocket is None:
            return {
                "status": "no websocket found",
                "username": username,
                "thread_id": thread_id,
            }

        if websocket.client_state.name == "DISCONNECTED":
            return {
                "status": "websocket already closed",
                "username": username,
                "thread_id": thread_id,
            }

        await websocket.close()
        return {
            "status": "websocket closed and cleared session",
            "username": username,
            "thread_id": thread_id,
        }
    except Exception as e:
        logger.error(f"500: Failed to close websocket: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to close websocket: {str(e)}"
        )
