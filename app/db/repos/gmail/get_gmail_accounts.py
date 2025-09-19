"""
Gmail account retrieval service.

This module defines helper functions to load stored Gmail account information
for a given user from the database. It ensures that the data is properly
decoded, validated, and returned as a list of `GmailAccount` objects.

Functions:
    get_gmail_account(username: str, namespace_for_memory: Tuple[str, str]) -> List[GmailAccount]:
        Fetches Gmail accounts associated with a specific user from storage.
        Returns an empty list if no accounts are found. Raises HTTPException
        if the data format is invalid or any unexpected error occurs.
"""

import json
from typing import Any, List, Tuple

from fastapi import HTTPException
from pydantic import TypeAdapter

from app.core.logging import logger
from app.db.redis import db_store
from app.schemas.gmail_account import GmailAccount


def get_gmail_account(
    username: str, namespace_for_memory: Tuple[str, str]
) -> List[GmailAccount]:
    key = f"user-gmail-accounts:{username}"
    try:
        raw: Any = db_store.get(
            namespace=namespace_for_memory,
            key=key,
        )

        # Check if raw data is empty or not
        if not raw or not getattr(raw, "value", None):
            logger.debug(f"No gmail accounts found for username: {username}")
            return []

        # Since we always save as JSON string, always use json.loads
        data: List[GmailAccount] = json.loads(raw.value)

        # Validate that data is a list of dicts
        if not isinstance(data, list):
            raise HTTPException(
                status_code=500,
                detail=f"Invalid data format in DB for user {username}, expected list.",
            )

        gmail_accounts = TypeAdapter(List[GmailAccount]).validate_json(raw.value)

        return gmail_accounts
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while reading gmail accounts: {str(e)}"
        )
