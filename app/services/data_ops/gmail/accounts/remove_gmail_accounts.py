"""
Gmail account removal service.

This module provides functionality to delete all stored Gmail accounts
associated with a specific user from the database.

Functions:
    remove_gmail_account(username: str, namespace_for_memory: Tuple[str, str]) -> dict:
        Deletes the Gmail account records for the given user. Returns a
        success response if deletion is successful. Raises HTTPException
        in case of an error during the deletion process.
"""

from typing import Tuple

from fastapi import HTTPException

from app.db.redis import db_store
from app.core import logger
from app.services.data_ops.auth.get_user_data import get_user_data
from app.services.data_ops.gmail.accounts.get_gmail_accounts import get_gmail_account


def remove_gmail_account(
    username: str,
    namespace_for_memory: Tuple[str, str],
    email_address: str,
) -> dict:
    auth_key = f"user-auth:{username}"
    gmail_account_key = f"user-gmail-accounts:{username}"

    try:
        # read both data from gmail_account_key and auth_key
        user_auth_data = get_user_data(
            username=username, namespace_for_memory=namespace_for_memory
        )
        # Fetch existing gmail accounts
        gmail_accounts_data = (
            get_gmail_account(
                username=username, namespace_for_memory=namespace_for_memory
            )
            or []
        )

        # Check if account exists
        if email_address not in gmail_accounts_data:
            raise HTTPException(
                status_code=404,
                detail=f"Gmail account '{email_address}' not found for this user.",
            )

        # Remove the email
        updated_accounts = [acc for acc in gmail_accounts_data if acc != email_address]
        print("Updated accounts:", updated_accounts)

        # Save back to Redis
        db_store.put(
            namespace_for_memory,
            key=gmail_account_key,
            value=updated_accounts,
        )

        logger.info(f"Removed Gmail account {email_address} for user {username}")

        return {
            "success": True,
            "removed": email_address,
            "remaining_accounts": updated_accounts,
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error while removing gmail accounts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error while removing gmail accounts: {str(e)}",
        )
