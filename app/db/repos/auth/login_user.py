"""
This module provides functionality for authenticating and logging in users.
Functions:
    login_user(user: LoginSchema, namespace_for_memory: Tuple[str, str]) -> Dict[str, Any]:
        Authenticates a user based on the provided login schema and retrieves user data from Redis.
        Handles password verification and returns appropriate HTTP exceptions for invalid credentials or errors.
"""

from typing import Any, Dict, List, Tuple, cast

from fastapi import HTTPException

from app.core import logger
from app.utils._api_helper import hash_password
from app.schemas.login import LoginSchema
from app.db.redis import db_store
from app.utils._env_helper import safe_json_parse


def login_user(
    user: LoginSchema, namespace_for_memory: Tuple[str, str]
) -> Dict[str, Any]:
    """
    Log in a user with the provided user schema.
    """
    # Construct the user key based on username and email
    # Email is optional, so we handle it accordingly
    user_key = f"user-auth:{user.username}"
    try:
        data = db_store.get(namespace=namespace_for_memory, key=user_key)

        # Check if user exists and password matches
        if not data or not data.value:
            logger.debug(f"404: User data not found for username: {user.username}")
            raise HTTPException(status_code=404, detail="User not found")

        str_data: str = cast(str, data.value)
        # Paring the safe josn values from  nested redis object
        parsed_data: Dict[str, Any] | List[Any] | Any = safe_json_parse(
            str_data, get="dict"
        )
        if not isinstance(parsed_data, dict):
            logger.critical("Parsed user data is not a dictionary")
            raise HTTPException(status_code=500, detail="Invalid user data format")

        # Check if the provided password matches the stored hashed password
        parsed_data = cast(Dict[str, Any], parsed_data)
        if parsed_data.get("password") != hash_password(user.password):
            logger.warning(f"401: Invalid password")
            raise HTTPException(
                status_code=401, detail=f"User {user.username} entered invalid password"
            )

    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"{str(e)}")

    # If user exists and password matches, return success
    logger.debug(f"User {user.username} logged in successfully")
    return {"success": 200, "message": "User logged in successfully", "data": parsed_data}
