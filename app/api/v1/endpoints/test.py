from typing import Dict, List, Tuple
from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel
from app.db.repos.gmail.get_gmail_accounts import get_gmail_account
from dotenv import load_dotenv

from app.schemas.gmail_account import GmailAccount
from app.services.gmail.gmail_toolkit import GmailToolKit
from app.services.job_scheduler.jobs import start_email_scheduler_job
from app.core.logging import logger
from app.services.session.get_session import get_session
from app.services.session.delete_session import delete_session
from app.services.session.store_session import store_session

load_dotenv()


router = APIRouter()
namespace_for_memory = ("auth", "user")


class GoogleAccountRequest(BaseModel):
    username: str


@router.post("/get_google_account/v1")
def get_google_account(token: GoogleAccountRequest):
    try:
        return get_gmail_account(
            username=token.username,
            namespace_for_memory=namespace_for_memory,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save tokens: {str(e)}")


@router.websocket("/chatbot/v1/{username}/{thread_id}")
async def open_chat_websocket(websocket: WebSocket, username: str, thread_id: str):
    await websocket.accept()
    logger.info(f"Websocket connection of user - {username} is opened.")
    # job = start_email_scheduler_job(
    #     username=username, user_id=user_id, thread_id=thread_id, interval=30
    # )
    data: List[GmailAccount] = get_gmail_account(
        username=username, namespace_for_memory=namespace_for_memory
    )
    # print(f"Gmail_accounts : {data}")
    if data and len(data) > 0:
        gmail_toolkit = GmailToolKit(gmail_account=data[0])

    # store session
    store_session(
        websocket=websocket,
        username=username,
        thread_id=thread_id,
        gmail_toolkit=gmail_toolkit,
    )

    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"AI : {message} - from {username}")

    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        delete_session(username=username, thread_id=thread_id)
        logger.info(f"Websocket connection of user - {username} is closed.")
        await websocket.close()


@router.post("/chatbot/v1/close/{username}/{thread_id}")
async def close_chat_websocket(username: str, thread_id: str):
    session = get_session(username, thread_id)
    websocket = session.websocket

    try:
        delete_session(username, thread_id)
        # Already closed?
        if websocket.client_state.name == "DISCONNECTED":
            # cleanup stale session
            return {
                "status": "websocket already closed",
                "username": username,
                "thread_id": thread_id,
            }
        else:
            await websocket.close(code=1000)  # Normal closure
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
