from typing import Any, Dict
from api._helper import _hash_password
from api.schema import UserSchema
from core.storage.setup import db_store


def register_user(user: UserSchema, namespace_for_memory: tuple) -> Dict[str, Any]:
    """
    Register a new user with the provided user schema.
    """
    user_key = f"user:{user.username}:{user.email if user.email else 'no-email'}"
    try:
        db_store.get(namespace=namespace_for_memory, key=user_key)
    except KeyError:
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
            return {"success": 200, "message": "User registered successfully"}
        except Exception as e:
            return {"success": 500, "message": f"Error registering user: {str(e)}"}

    return {
        "success": 200,
        "message": "User registered successfully",
        "data": user.dict(),
    }
