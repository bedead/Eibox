from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import requests
from app.db.repos.gmail.add_gmail_accounts import add_gmail_account
from google_auth_oauthlib.flow import Flow
import secrets
from datetime import datetime, timedelta, timezone
from app.services.gmail.gmail_toolkit import GmailAccount
from app.core.config import settings
from app.utils.common import (
    get_gcp_client_id,
    get_gcp_client_secret,
    get_gmail_redirect_uri,
)

GOOGLE_CLIENT_ID: str = get_gcp_client_id()
GOOGLE_CLIENT_SECRET: str = get_gcp_client_secret()
OAUTH_REDIRECT_URI: str = get_gmail_redirect_uri()

router = APIRouter()
namespace_for_memory = ("auth", "user")

oauth_states = {}

CALLBACK_SUCCESS_TEMPLATE = """
<h2>✅ Gmail Connected!</h2>
<p>Usernmae: {{username}}</p>
<p>Email: {{email}}</p>
"""

CALLBACK_ERROR_TEMPLATE = """
<h2>❌ Error</h2>
<p>{{error}}</p>
"""


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
    flow = Flow.from_client_config(
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
    )
    flow.redirect_uri = OAUTH_REDIRECT_URI

    # Generate state
    state = secrets.token_urlsafe(32)

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

    return RedirectResponse(authorization_url)


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

        state_info = oauth_states[state]
        if datetime.now() > state_info["expires_at"]:
            del oauth_states[state]
            return HTMLResponse(
                CALLBACK_ERROR_TEMPLATE.replace("{{error}}", "OAuth session expired")
            )

        # OAuth flow
        flow = Flow.from_client_config(
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

        credentials = flow.credentials

        # Get user info
        user_info_response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
        user_info = user_info_response.json()

        # converting datetime to utc timezone and then calculating expires_in time in seconds
        expiry = credentials.expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        expires_in: int = int((expiry - datetime.now(timezone.utc)).total_seconds())

        account_data = GmailAccount(
            username=state_info["username"],
            email=user_info.get("email"),
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            expires_in=expires_in,
            token_type="Bearer",
            scope=settings.GOOGLE_GMAIL_SCOPE,
            token_last_refresh_time=str(datetime.now()),
        )

        save_result = add_gmail_account(
            account_data, namespace_for_memory=namespace_for_memory
        )

        oauth_states[state]["email"] = user_info.get("email")

        if save_result["success"]:
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
