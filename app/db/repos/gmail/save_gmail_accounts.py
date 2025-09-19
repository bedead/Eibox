"""
Gmail account persistence service.

This module defines functionality for saving Gmail account credentials
to the database. Accounts are serialized to JSON before storage and
can later be retrieved for authentication or API access.

Functions:
    save_gmail_account(username: str, accounts: List[GmailAccount], namespace_for_memory: Tuple[str, str]) -> dict:
        Saves a list of Gmail accounts for the given user into storage.
        Returns a success response if saving is successful.
        Raises HTTPException if an error occurs while storing data.
"""

import json
from typing import List, Tuple

from fastapi import HTTPException

from app.core.logging import logger
from app.db.redis import db_store
from app.schemas.gmail_account import GmailAccount


def save_gmail_account(
    username: str, accounts: List[GmailAccount], namespace_for_memory: Tuple[str, str]
):
    # This function should save the tokens to the database or any storage
    # db_store.put()
    key = f"user-gmail-accounts:{username}"

    try:
        db_store.put(
            namespace=namespace_for_memory,
            key=key,
            value=json.dumps([account.model_dump() for account in accounts]),  # type: ignore
        )
        logger.debug(f"Saved the gmail_account data for {username}.")
        return {"success": True}

    except Exception as e:
        logger.error(f"Error while storing gmail accounts: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error while storing gmail accounts: {str(e)}"
        )
