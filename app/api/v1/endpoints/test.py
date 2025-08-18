from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel
from app.db.repos.gmail.get_gmail_accounts import get_gmail_account
from dotenv import load_dotenv


load_dotenv()


router = APIRouter()
namespace_for_memory = ("auth", "user")


class GoogleAccountRequest(BaseModel):
    user_id: str
    username: str


@router.post("/get_google_account/v1")
def get_google_account(token: GoogleAccountRequest):
    try:
        return get_gmail_account(
            user_id=token.user_id,
            username=token.username,
            namespace_for_memory=namespace_for_memory,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save tokens: {str(e)}")


@router.websocket("/chatbot/v1/{username}/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, username: str, thread_id: str):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"AI : {message} - from {username}")

    except Exception as e:
        await websocket.send_text(f"[ERROR] {str(e)}")
    finally:
        await websocket.close()
