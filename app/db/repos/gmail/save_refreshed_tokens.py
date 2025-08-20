import json
from app.db.redis import db_store
from app.schemas.gmail_account import GmailAccount
from app.core.logging import logger


def save_refreshed_tokens(
    updated_account: GmailAccount, username: str, namespace_for_memory=("auth", "user")
):
    """
    Callback function to save refreshed tokens back to your storage.
    This function will be called whenever tokens are refreshed.
    """
    try:
        key = f"user-gmail-accounts:{username}"

        db_store.put(
            namespace=namespace_for_memory,
            key=key,
            value=json.dumps([account.model_dump() for account in updated_account]),
        )

        logger.debug(f"Tokens refreshed and saved for {updated_account.email}")
        logger.debug(f"New access token: {updated_account.access_token[:20]}...")

    except Exception as e:
        logger.error(f"Error saving refreshed tokens: {e}")
