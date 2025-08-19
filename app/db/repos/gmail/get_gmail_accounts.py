import json
from typing import List
from fastapi import HTTPException
from app.db.redis import db_store
from app.schemas.gmail_account import GmailAccount


def get_gmail_account(username: str, namespace_for_memory: str) -> List[GmailAccount]:
    key = f"user-gmail-accounts:{username}"
    try:
        raw = db_store.get(
            namespace=namespace_for_memory,
            key=key,
        )
        gmail_accounts: List[GmailAccount] = (
            [GmailAccount(**item) for item in json.loads(raw.value)] if raw else []
        )
        return gmail_accounts
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while reading gmail accounts: {str(e)}"
        )
