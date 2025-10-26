"""
This module provides functionality to safely update user details in the database,
including flexible updates to user application settings. It handles retrieval,
merging, validation, and storage of user data, ensuring data integrity and error handling.
Functions:
    - update_user_data: Updates user information and app settings in the database.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException

from app.core import logger
from app.db import db_store, UserModel
from app.utils import deep_merge_dicts, safe_json_parse


def update_user_data(
    username: str,
    namespace_for_memory: Tuple[str, str],
    full_name: Optional[str] = None,
    app_settings: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Safely update user details in the database with flexible app_settings.
    """
    user_key = f"user-auth:{username}"
    try:
        # Retrieve existing user data
        record = db_store.get(namespace=namespace_for_memory, key=user_key)
        raw_data = record.value if record and record.value else None

        if not raw_data:
            raise HTTPException(status_code=404, detail="User not found")

        logger.debug(f"User details found for username: {username}")

        existing_data = safe_json_parse(raw_data)
        if not isinstance(existing_data, dict):
            logger.critical("Parsed user data is not a dictionary")
            raise HTTPException(status_code=500, detail="Invalid user data format")

        # Merge updates without overwriting unspecified fields
        updated_data = {**existing_data}

        if full_name is not None:
            updated_data["full_name"] = full_name

        # Merge app_settings dynamically
        if app_settings:
            updated_data["app_settings"] = deep_merge_dicts(
                updated_data.get("app_settings", {}), app_settings
            )

        updated_data["account_details_updated"] = str(datetime.now())

        # Validate via Pydantic
        user_data = UserModel(**updated_data)
        # logger.debug(f"Updated User Model Data: {user_data}")

        # Store back in the database
        db_store.put(
            namespace=namespace_for_memory,
            key=user_key,
            value=user_data.model_dump(),
            index=False,
        )

        return {
            "success": 200,
            "message": "User details updated successfully",
            "updated_data": user_data.model_dump(),
        }

    except Exception as e:
        logger.error(f"Error updating user data: {e}, exc_info=True)")
        raise HTTPException(status_code=500, detail=f"Error updating user data: {e}")
