import json
from typing import List
from fastapi import HTTPException
from app.db.redis import db_store
from app.schemas.gmail_account import GmailAccount


def save_gmail_account(
    username: str, accounts: List[GmailAccount], namespace_for_memory: str
):
    # This function should save the tokens to the database or any storage
    # db_store.put()
    key = f"user-gmail-accounts:{username}"

    try:
        db_store.put(
            namespace=namespace_for_memory,
            key=key,
            value=json.dumps([account.model_dump() for account in accounts]),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while storing gmail accounts: {str(e)}"
        )
