"""
This module provides functionality to register a new user in the authentication system.
It checks for existing users, hashes passwords, and stores user data in the database.
"""

from typing import Any, Dict, Tuple

from fastapi import HTTPException

from app.utils import hash_password
from app.db import db_store, UserModel


def register_user(
    user: UserModel, namespace_for_memory: Tuple[str, str]
) -> Dict[str, Any]:
    """
    Register a new user with the provided user schema.
    """
    user_key = f"user-auth:{user.username}"
    data = db_store.get(namespace=namespace_for_memory, key=user_key)
    if data and data.value:
        raise HTTPException(
            status_code=409, detail="User already exists, try different username"
        )
    # User does not exist, proceed to register
    try:
        user.password = hash_password(user.password)  # Store hashed password
        # Store user data in the database
        db_store.put(
            namespace=namespace_for_memory,
            key=user_key,
            value=user.model_dump(),
            index=False,
        )
        return {
            "success": 200,
            "message": "User registered successfully",
            "data": user.model_dump_json(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering user: {str(e)}")
