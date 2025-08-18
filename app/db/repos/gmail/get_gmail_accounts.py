from fastapi import HTTPException
from app.db.redis import db_store
from app.utils.common import get_db_gmail_account_key


def get_gmail_account(user_id: str, username: str, namespace_for_memory: str):
    try:
        data = db_store.get(
            namespace=namespace_for_memory,
            key=get_db_gmail_account_key(user_id=user_id, username=username),
        )
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while reading gmail accounts: {str(e)}"
        )
