from fastapi import FastAPI, APIRouter
from core import EmailAgent, EmailState
from pydantic import BaseModel

router = APIRouter()


class ChatInput(BaseModel):
    thread_id: str
    pending_emails: bool


@router.post("/v1/gmail_monitor")
def chat(input: ChatInput):
    config = {"configurable": {"thread_id": input.thread_id}}
    response = EmailAgent.invoke(
        input={"pending_email": input.pending_emails}, config=config
    )
    return response


@router.get("/")
def test():
    return {"success": 200}
