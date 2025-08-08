from typing import Dict


store = {}


def save_user_token(user_id: str, code: Dict):
    # This function should save the tokens to the database or any storage
    store[user_id] = code
