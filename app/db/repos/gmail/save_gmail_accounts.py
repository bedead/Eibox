import json
from typing import List
from fastapi import HTTPException
from app.db.redis import db_store
from app.schemas.gmail_account import GmailAccount
from app.utils.common import get_db_gmail_account_key


def save_gmail_account(
    user_id: str, username: str, accounts: List[GmailAccount], namespace_for_memory: str
):
    # This function should save the tokens to the database or any storage
    # db_store.put()
    try:
        db_store.put(
            namespace=namespace_for_memory,
            key=get_db_gmail_account_key(user_id=user_id, username=username),
            value=json.dumps([account.model_dump() for account in accounts])
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while storing gmail accounts: {str(e)}"
        )
