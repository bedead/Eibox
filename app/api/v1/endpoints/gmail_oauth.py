"""
Endpoints for Gmail OAuth authentication flow.
This module provides FastAPI routes to start the Gmail OAuth process, handle the OAuth callback,
and check the status of the OAuth flow for a given mobile session.
Routes:
    /gmail/start: Initiates the Gmail OAuth flow for a user.
    /gmail/callback: Handles the OAuth callback from Google and saves account information.
    /gmail/status/{mobile_session_id}: Checks if the OAuth flow has been completed for a mobile session.
Author: Satyam Mishra
Date: 14-09-2025
"""

from typing import Any, Dict, cast
import requests
import secrets
from datetime import datetime, timedelta, timezone

from google_auth_oauthlib.flow import Flow
from google.auth.credentials import Credentials
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.db import add_gmail_account, update_user_data as uud
from app.schemas import GmailAccount
from app.core import settings
from app.utils import (
    CALLBACK_ERROR_TEMPLATE,
    CALLBACK_SUCCESS_TEMPLATE,
    get_gcp_client_id,
    get_gcp_client_secret,
    get_gmail_redirect_uri,
)


GOOGLE_CLIENT_ID: str = get_gcp_client_id()
GOOGLE_CLIENT_SECRET: str = get_gcp_client_secret()
OAUTH_REDIRECT_URI: str = get_gmail_redirect_uri()

router = APIRouter()
namespace_for_memory = ("auth", "user")

oauth_states: Dict[str, Any] = {}


@router.get("/gmail/start")
async def start_gmail_oauth(
    username: str = Query(...), mobile_session_id: str = Query(...)
):
    """Start Gmail OAuth flow"""
    if not username:
        return JSONResponse(
            {"error": "username parameter is required"}, status_code=400
        )

    # Create OAuth flow
    flow: Flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [OAUTH_REDIRECT_URI],
            }
        },
        scopes=settings.GOOGLE_GMAIL_SCOPE,
    )
    flow.redirect_uri = OAUTH_REDIRECT_URI

    # Generate state
    state: str = secrets.token_urlsafe(32)

    # Store state
    oauth_states[state] = {
        "username": username,
        "mobile_session_id": mobile_session_id,
        "timestamp": datetime.now(),
        "expires_at": datetime.now() + timedelta(minutes=10),
        "completed": False,
    }

    # Get authorization URL
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=state,
        include_granted_scopes="true",
    )

    return RedirectResponse(url=cast(str, authorization_url))


@router.get("/gmail/callback")
async def gmail_oauth_callback(request: Request):
    """Handle OAuth callback"""
    try:
        state = request.query_params.get("state")
        if not state or state not in oauth_states:
            return HTMLResponse(
                CALLBACK_ERROR_TEMPLATE.replace(
                    "{{error}}", "Invalid or expired OAuth state"
                )
            )

        state_info: Dict[str, Any] = oauth_states[state]
        if datetime.now() > state_info["expires_at"]:
            del oauth_states[state]
            return HTMLResponse(
                CALLBACK_ERROR_TEMPLATE.replace("{{error}}", "OAuth session expired")
            )

        # OAuth flow
        flow: Flow = Flow.from_client_config(  # type: ignore
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [OAUTH_REDIRECT_URI],
                }
            },
            scopes=settings.GOOGLE_GMAIL_SCOPE,
            state=state,
        )
        flow.redirect_uri = OAUTH_REDIRECT_URI
        flow.fetch_token(authorization_response=str(request.url))

        credentials: Credentials = flow.credentials

        # Get user info
        user_info_response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
        user_info = user_info_response.json()

        # converting datetime to utc timezone and then calculating expires_in time in seconds
        expiry: datetime = credentials.expiry  # type: ignore
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        expires_in: int = int((expiry - datetime.now(timezone.utc)).total_seconds())

        account_data = GmailAccount(
            username=state_info["username"],
            email=user_info.get("email"),
            access_token=str(credentials.token),
            refresh_token=str(credentials.refresh_token),
            expires_in=expires_in,
            token_type="Bearer",
            scope=settings.GOOGLE_GMAIL_SCOPE,
            token_last_refresh_time=str(datetime.now()),
        )

        save_result = add_gmail_account(
            account_data, namespace_for_memory=namespace_for_memory
        )

        gmail_user_data_update_result = uud(
            username=account_data.username,
            namespace_for_memory=namespace_for_memory,
            app_settings={
                "connected_gmail_accounts_email": [account_data.email],
            },
        )

        oauth_states[state]["email"] = user_info.get("email")

        if save_result["success"] and gmail_user_data_update_result["success"]:
            oauth_states[state]["completed"] = True

            return HTMLResponse(
                CALLBACK_SUCCESS_TEMPLATE.replace(
                    "{{email}}", user_info.get("email", "")
                ).replace("{{username}}", state_info["username"])
            )
        else:
            return HTMLResponse(
                CALLBACK_ERROR_TEMPLATE.replace(
                    "{{error}}", f"Failed to save account: {save_result['error']}"
                )
            )

    except Exception as e:
        return HTMLResponse(
            CALLBACK_ERROR_TEMPLATE.replace(
                "{{error}}", f"OAuth callback failed: {str(e)}"
            )
        )


@router.get("/gmail/status/{mobile_session_id}")
async def check_oauth_status(mobile_session_id: str):
    """Check if OAuth flow completed for a mobile session"""
    for state, info in oauth_states.items():
        stored_session_id: str = info.get("mobile_session_id")
        completed: bool = info.get("completed", False)
        email: str = info.get("email", "")

        if stored_session_id == mobile_session_id and completed:
            del oauth_states[state]
            return JSONResponse({"completed": True, "email": email})

    return JSONResponse({"completed": False})
