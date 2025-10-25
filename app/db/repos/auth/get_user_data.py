""" """

from ast import parse
from typing import Any, Dict, List, Tuple, cast

from fastapi import HTTPException
from langgraph.store.base import Item

from app.core.logger_config import logger
from app.db.redis import db_store
from app.utils.common import safe_json_parse


def get_user_data(
    username: str, namespace_for_memory: Tuple[str, str]
) -> Dict[str, Any]:
    """
    Retrieve user data from the database.
    """
    # Construct the user key based on username
    user_key = f"user-auth:{username}"
    try:
        data: Item | None = db_store.get(namespace=namespace_for_memory, key=user_key)

        # Check if user exists and password matches
        if not data or not data.value:
            logger.debug(f"404: User data not found for username: {username}")
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

    except Exception as e:
        logger.error(f"Error while retrieving user data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"{str(e)}")

    # If user exists and password matches, return success
    logger.debug(f"Username: {username} data retrieved successfully.")
    return parsed_data
