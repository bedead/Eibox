from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()
namespace_for_memory = ("auth", "user")


class DeleteAccountRequest(BaseModel):
    """Payload schema for account deletion request from user."""

    pass


@router.post("/delete_user_account")
def delete_user_account(user: DeleteAccountRequest):
    """Register a new user with properly formatted data."""

    pass


@router.post("/reset_ai_agent_directions")
def reset_user_specific_ai_agent_directions():
    pass
