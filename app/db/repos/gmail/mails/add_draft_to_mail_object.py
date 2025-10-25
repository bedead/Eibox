""" """

from typing import Dict, Tuple, Union

from fastapi import HTTPException

from app.core.logger_config import logger
from app.db.repos.gmail.mails.get_mail_object import get_mail_object
from app.schemas.unread_mails import UnreadMailsSchema
from app.db.redis import db_store


def add_draft_to_mail_object(
    username: str,
    current_mail_id: str,
    draft_response: str,
    namespace_for_memory: Tuple[str, str],
) -> Union[Dict[str, str], None]:
    """Add draft response to to mail object with specific mail ID in storage."""
    key = f"user-mails-object:{username}"
    try:
        # Get existing mail object data
        existing_mail_object: Union[UnreadMailsSchema, None] = get_mail_object(
            username, namespace_for_memory
        )
        if existing_mail_object:
            # Check if the mail with the same ID already exists
            for mail in existing_mail_object.mails_data:
                if mail.mail_id == current_mail_id:
                    mail.draft_response = draft_response
                    break

            db_store.put(
                namespace_for_memory, key, value=existing_mail_object.model_dump()
            )
            logger.debug(f"Draft Response added to mail with ID '{current_mail_id}.")
            return {
                "status": "success",
                "message": f"Draft Response added to mail with ID '{current_mail_id}' for user '{username}'.",
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add new mail data for user '{username}' due to error: {str(e)}",
        )
