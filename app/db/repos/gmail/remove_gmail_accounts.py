from typing import Tuple

from fastapi import HTTPException
from app.db.redis import db_store
from app.core.logging import logger


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
