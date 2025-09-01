import json
from typing import List, Tuple

from fastapi import HTTPException
from app.schemas.gmail_account import GmailAccount
from .save_gmail_accounts import save_gmail_account
from .get_gmail_accounts import get_gmail_account


def add_gmail_account(new_account: GmailAccount, namespace_for_memory: Tuple[str, str]):
    username = new_account.username

    try:
        # Load existing accounts (if any)
        gmail_accounts: List[GmailAccount] = get_gmail_account(
            username=username,
            namespace_for_memory=namespace_for_memory,
        )

        # Remove existing account with the same email
        gmail_accounts = [
            acc for acc in gmail_accounts if acc.email != new_account.email
        ]

        # Add new account
        gmail_accounts.append(new_account)

        # Save updated accounts
        result = save_gmail_account(
            username=username,
            accounts=gmail_accounts,
            namespace_for_memory=namespace_for_memory,
        )
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add gmail accounts due to error: {str(e)}",
        )
