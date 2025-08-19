import json
from typing import Dict
from fastapi import HTTPException
from app.utils._api_helper import _hash_password
from app.schemas.login import LoginSchema
from app.db.redis import db_store
from app.core.logging import logger


# TODO: #12 update user_key by adding user_id also, by taking optional user_id as input field.
def login_user(user: LoginSchema, namespace_for_memory: tuple):
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
            logger.info(f"404: User not found")
            raise HTTPException(status_code=404, detail="User not found")

        # Assuming data is a dictionary with a 'password' field
        data: Dict = json.loads(data.value)

        # Check if the provided password matches the stored hashed password
        if data.get("password") != _hash_password(user.password):
            logger.warning(f"401: Invalid password")
            raise HTTPException(
                status_code=401, detail=f"User {user.username} entered invalid password"
            )

    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"{str(e)}")

    # If user exists and password matches, return success
    logger.info(f"User {user.username} logged in successfully")
    return {"success": 200, "message": "User logged in successfully", "data": data}
