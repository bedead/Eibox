from fastapi import HTTPException
from typing import Any, Dict
from api._helper import _hash_password
from api.schema import RegisterSchema
from core.storage.setup import db_store


def register_user(user: RegisterSchema, namespace_for_memory: tuple) -> Dict[str, Any]:
    """
    Register a new user with the provided user schema.
    """
    user_key = f"user-auth:{user.username.lower()}"
    data = db_store.get(namespace=namespace_for_memory, key=user_key)
    if data and data.value:
        raise HTTPException(
            status_code=409, detail="User already exists, try different username"
        )
    # User does not exist, proceed to register
    try:
        user.password = _hash_password(user.password)  # Store hashed password
        # Store user data in the database
        db_store.put(
            namespace=namespace_for_memory,
            key=user_key,
            value=user.dict(),
            index=False,
        )
        return {
            "success": 200,
            "message": "User registered successfully",
            "data": user.dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering user: {str(e)}")
