from fastapi import HTTPException
from api._helper import _hash_password
from api.schema.LoginSchema import LoginSchema
from core.storage.setup import db_store


def login_user(user: LoginSchema, namespace_for_memory: tuple):
    """
    Log in a user with the provided user schema.
    """
    # Construct the user key based on username and email
    # Email is optional, so we handle it accordingly
    user_key = f"user-auth:{user.username.lower()}"
    try:
        data = db_store.get(namespace=namespace_for_memory, key=user_key)

        # Check if user exists and password matches
        if not data or not data.value:
            raise HTTPException(status_code=404, detail="User not found")

        # Assuming data is a dictionary with a 'password' field
        data = data.value

        # Check if the provided password matches the stored hashed password
        if data.get("password") != _hash_password(user.password):
            raise HTTPException(status_code=401, detail="Invalid password")

    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"{str(e)}")

    # If user exists and password matches, return success
    return {"success": 200, "message": "User logged in successfully", "data": data}
