from unittest import result
from fastapi import APIRouter
from pydantic import BaseModel

from app.services import remove_one_mail_account as roma
from app.services import remove_all_mail_accounts as rama

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


class RemoveOneGmailAccountRequest(BaseModel):
    """Payload schema for removing connected Gmail account."""

    username: str
    email_address: str


@router.post("/mail_account/remove_one")
def remove_one_connected_gmail_account(input: RemoveOneGmailAccountRequest):
    result = roma(
        username=input.username,
        nfm=namespace_for_memory,
        email_address=input.email_address,
    )
    return result

class RemoveAllGmailAccountRequest(BaseModel):
    """Payload schema for removing connected Gmail account."""

    username: str

@router.delete("/mail_account/remove_all")
def remove_all_connected_gmail_account(payload: RemoveAllGmailAccountRequest):
    print(f"Called remove_all_connected_gmail_account for user: {payload.username}")

    result = rama(
        username=payload.username,
        nfm=namespace_for_memory,
    )

    return result
