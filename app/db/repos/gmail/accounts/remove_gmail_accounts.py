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
from app.core.logger_config import logger


def remove_gmail_account(username: str, namespace_for_memory: Tuple[str, str]):
    account_key = f"user-gmail-accounts:{username}"

    try:
        db_store.delete(
            namespace=namespace_for_memory,
            key=account_key,
        )
        logger.debug(f"Removed the gmail_account data for {username}.")
        return {"success": True}

    except Exception as e:
        logger.error(f"Error while removing gmail accounts: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error while removing gmail accounts: {str(e)}"
        )
