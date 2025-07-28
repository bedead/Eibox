from api._helper import _hash_password
from api.schema.UserSchema import UserSchema
from core.storage.setup import db_store


def login_user(user: UserSchema, namespace_for_memory: tuple):
    """
    Log in a user with the provided user schema.
    """
    # Construct the user key based on username and email
    # Email is optional, so we handle it accordingly
    user_key = f"user:{user.username}:{user.email if user.email else 'no-email'}"
    try:
        data = db_store.get(namespace=namespace_for_memory, key=user_key)

        # Check if user exists and password matches
        if not data:
            return {"success": 404, "message": "User not found"}

        # Assuming data is a dictionary with a 'password' field
        data = data.value

        # Check if the provided password matches the stored hashed password
        if data.get("password") != _hash_password(user.password):
            return {"success": 401, "message": "Invalid password"}
    except KeyError:
        return {"success": 404, "message": "User not found"}

    # If user exists and password matches, return success
    return {"success": 200, "message": "User logged in successfully", "data": data}
