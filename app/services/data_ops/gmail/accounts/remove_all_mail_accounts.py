"""
Gmail account removal service.

This module provides functionality to delete all stored mail accounts
associated with a specific user from the database.

Functions:
    remove_all_mail_accounts(username: str, nfm: Tuple[str, str]) -> dict:
        Deletes all mail account records for the given user.
        Returns a success response if deletion is successful.
        Raises HTTPException in case of an error during the deletion process.
"""

from typing import Tuple

from fastapi import HTTPException

from app.core import logger
from app.db.redis import db_store
from app.services.data_ops.auth.get_user_data import get_user_data
from app.services.data_ops.auth.update_user_data import update_user_data


def remove_all_mail_accounts(
    username: str,
    nfm: Tuple[str, str],
) -> dict:
    gmail_account_key = f"user-gmail-accounts:{username}"

    try:
        # Clear connected Gmail accounts from user data
        result = update_user_data(
            username=username,
            namespace_for_memory=nfm,
            connected_gmail_accounts_email=[],
        )

        # Remove all Gmail accounts from Redis
        db_store.put(
            namespace=nfm,
            key=gmail_account_key,
            value=[], # type: ignore
        )

        # Verify removal
        updated_user_data = get_user_data(
            username=username,
            namespace_for_memory=nfm,
        )

        cur_gmail_accounts = (
            updated_user_data.get("app_settings", {})
            .get("connected_gmail_accounts_email", [])
        )

        if cur_gmail_accounts:
            raise HTTPException(
                status_code=500,
                detail="Failed to remove all Gmail accounts from user data.",
            )

        logger.info(f"Removed all mail accounts for user {username}")

        return {"success": True,}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error while removing all mail accounts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error while removing all mail accounts: {str(e)}",
        )