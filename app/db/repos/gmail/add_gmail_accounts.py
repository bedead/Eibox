import json
from typing import List

from fastapi import HTTPException
from app.schemas.google_access_token import GoogleAccessTokens
from app.schemas.gmail_account import GmailAccount
from app.db.redis import db_store
from .save_gmail_accounts import save_gmail_account
from .get_gmail_accounts import get_gmail_account
from app.utils.common import get_db_gmail_account_key


def add_gmail_account(token: GoogleAccessTokens, namespace_for_memory: str):
    username = token.username
    user_id = token.user_id
    key = get_db_gmail_account_key(user_id=user_id, username=username)

    try:
        # Load existing accounts (if any)
        gmail_accounts: List[GmailAccount] = get_gmail_account(
            user_id=user_id,
            username=username,
            namespace_for_memory=namespace_for_memory,
        )

        # Build new GmailAccount from token
        gaccount = GmailAccount(
            email=token.account_email,
            refresh_token=token.token["refreshToken"],
            access_token=token.token["accessToken"],
            expires_in=token.token["expiresIn"],
            token_type=token.token["tokenType"],
            scope=token.token["scope"].split(),  # handle string → list
        )

        # Remove existing account with the same email
        gmail_accounts = [acc for acc in gmail_accounts if acc.email != gaccount.email]

        # Add new account
        gmail_accounts.append(gaccount)

        # Save updated accounts
        save_gmail_account(
            user_id=user_id,
            username=username,
            accounts=gmail_accounts,
            namespace_for_memory=namespace_for_memory,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add gmail accounts due to error: {str(e)}",
        )
