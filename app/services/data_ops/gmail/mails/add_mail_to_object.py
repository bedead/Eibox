""" """

from typing import Dict, Tuple, Union

from fastapi import HTTPException

from app.core import logger
from app.db import db_store, MailDataSchema, UnreadMailsSchema
from app.services.data_ops.gmail.mails.get_mail_object import get_mail_object


def add_mail_to_object(
    username: str,
    individual_mail_data: MailDataSchema,
    namespace_for_memory: Tuple[str, str],
) -> Union[Dict[str, str], None]:
    """Adds a new mail entry to the user's mail object in storage."""
    key = f"user-mails-object:{username}"
    try:
        # Get existing mail object data
        existing_mail_object: Union[UnreadMailsSchema, None] = get_mail_object(
            username, namespace_for_memory
        )
        updated_mail_object: UnreadMailsSchema
        if existing_mail_object is None:
            # If no existing data, create a new one
            updated_mail_object = UnreadMailsSchema(
                unread_mails_count=1, mails_data=[individual_mail_data]
            )
        else:
            # Update existing data with new mail
            updated_mail_object = UnreadMailsSchema(
                unread_mails_count=existing_mail_object.unread_mails_count + 1,
                mails_data=list(existing_mail_object.mails_data)
                + [individual_mail_data],
            )

        db_store.put(namespace_for_memory, key, value=updated_mail_object.model_dump())
        logger.debug(f"Added new mail data for user '{username}' successfully.")
        return {
            "status": "success",
            "message": f"New mail data added for user '{username}'.",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add new mail data for user '{username}' due to error: {str(e)}",
        )
