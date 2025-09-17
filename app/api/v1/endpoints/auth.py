"""
Authentication endpoints for the API.
Handles login, register, and update user data.
Author: Satyam Mishra
Date: 14-09-2025
"""

import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import APIRouter
from pydantic import BaseModel

load_dotenv()

from app.schemas.user_model import UserModel
from app.schemas.login import LoginSchema
from app.db.repos.auth.register_user import register_user as ru
from app.db.repos.auth.login_user import login_user as lu
from app.db.repos.auth.update_user_data import update_user_data as uud


router = APIRouter()
namespace_for_memory = ("auth", "user")


class RegisterRequest(BaseModel):
    """Payload schema for register request from user."""

    user_id: str
    account_created: str
    username: str
    full_name: str | None
    email: str
    password: str
    # user_type: Optional[str | None]
    gmail_accounts: Optional[List[str] | None]


@router.post("/register")
def register_user(user: RegisterRequest):
    """Register a new user with properly formatted data."""

    # Normalize and clean data
    now = datetime.datetime.now()

    formatted_data: Dict[str, Any] = {
        "user_id": user.user_id.strip(),
        "account_created": user.account_created or str(now),
        "username": user.username.strip(),
        "email": user.email.strip().lower(),
        "password": user.password,  # Assume hashing handled in `ru()`
        "full_name": user.full_name.strip() if user.full_name else None,
        "account_details_updated": None,
        "user_type": "free_user",
        "app_settings": {
            "auto_email_monitoring": False,
            "email_monitoring_frequency": 60,
            "email_notifications": False,
            "connected_gmail_accounts_email": user.gmail_accounts or [],
        },
    }

    # Create validated UserModel
    validated_user = UserModel(**formatted_data)

    # Save or register user
    return ru(validated_user, namespace_for_memory)


@router.post("/login")
def login_user(user: LoginSchema) -> Dict[str, Any]:
    return lu(user, namespace_for_memory)


# Model class for updating user data
class UpdateUserDataRequest(BaseModel):
    """Payload schema to update user data from user."""
    username: str
    full_name: Optional[str] = None
    auto_email_monitoring: Optional[bool] = None
    email_monitoring_frequency: Optional[int] = None
    email_notifications: Optional[bool] = None
    gmail_accounts: Optional[List[str]] = None


@router.post("/update_user_data")
def update_user_data(payload: UpdateUserDataRequest):
    # Build app_settings dict only with non-None values
    app_settings: Dict[str, Any] = {}
    print(f"Payload received: {payload}")

    if payload.auto_email_monitoring is not None:
        app_settings["auto_email_monitoring"] = payload.auto_email_monitoring

    if payload.email_monitoring_frequency is not None:
        app_settings["email_monitoring_frequency"] = payload.email_monitoring_frequency

    if payload.email_notifications is not None:
        app_settings["email_notifications"] = payload.email_notifications

    if payload.gmail_accounts is not None:
        app_settings["connected_gmail_accounts_email"] = payload.gmail_accounts

    return uud(
        username=payload.username,
        namespace_for_memory=namespace_for_memory,
        full_name=payload.full_name if payload.full_name is not None else None,
        app_settings=app_settings if app_settings else None,
    )
