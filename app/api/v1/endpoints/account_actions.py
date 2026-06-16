from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel

from app.services import remove_gmail_account as rga

router = APIRouter()
namespace_for_memory = ("auth", "user")


class DeleteAccountRequest(BaseModel):
    """Payload schema for account deletion request from user."""

    pass


@router.post("/delete_user_account")
def delete_user_account(user: DeleteAccountRequest):
    """Register a new user with properly formatted data."""

    pass


@router.post("/reset_ai_agent_data")
def reset_user_specific_ai_agent_data():
    pass


class RemoveGmailAccountRequest(BaseModel):
    """Payload schema for removing connected Gmail account."""

    username: str
    email_address: str


@router.post("/gmail_account/remove")
def remove_connected_gmail_account(input: RemoveGmailAccountRequest):
    result = rga(
        username=input.username,
        namespace_for_memory=namespace_for_memory,
        email_address=input.email_address,
    )
    return result


## More endpoints for other third party account removals can be added here
# @router.post("/outlook_account/remove")
# def remove_connected_outlook_account():
#     pass
