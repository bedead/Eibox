""" """

from typing import Any, Dict, List, Tuple, Union

from fastapi import HTTPException
from langgraph.store.base import Item

from app.core.logging import logger
from app.db.redis import db_store
from app.schemas.unread_mails import UnreadMailsSchema
from app.utils._env_helper import safe_json_parse


def get_mail_object(
    username: str, namespace_for_memory: Tuple[str, str]
) -> Union[UnreadMailsSchema, None]:
    """Fetches mail object data for a specific user from storage."""
    key = f"user-mails-object:{username}"

    try:
        unread_mail_object: Item | None = db_store.get(namespace_for_memory, key=key)

        if not unread_mail_object or not unread_mail_object.value:
            logger.debug(f"No mail object data found for user: {username}")
            return None

        mail_object_data: Union[Dict[str, Any], List[Any], Any] = safe_json_parse(
            unread_mail_object.value, get="dict"
        )
        if isinstance(mail_object_data, dict):
            return UnreadMailsSchema(**mail_object_data)

    except Exception as e:
        logger.debug(
            f"Error while reading mail object data for user: {username}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error while reading mail object data for user: {username}.\nError: {str(e)}",
        )
