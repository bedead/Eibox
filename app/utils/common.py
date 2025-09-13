import json
import re
from dotenv import load_dotenv
import os
from app.core.logging import logger
from app.core.config import settings

load_dotenv()


def get_gcp_client_id() -> str:
    return os.environ.get("GMAIL_WEB_CLIENT_ID")


def get_gcp_client_secret() -> str:
    return os.environ.get("GMAIL_WEB_CLIENT_SECRET")


def get_dev_server_url() -> str:
    return os.environ.get("DEV_SERVER_URL")


def get_prod_server_url() -> str:
    return os.environ.get("PROD_SERVER_URL")


def get_gmail_redirect_uri() -> str:
    # Get server type config url
    if settings.API_DEV_SERVER:
        SERVER_URL = get_dev_server_url()
    else:
        SERVER_URL = get_prod_server_url()

    # Get the default GMAIL_WEB_REDIRECT_URI Endpoint for redirect
    GMAIL_WEB_REDIRECT_URI = os.environ.get("GMAIL_WEB_REDIRECT_URI")

    # Return the combined URL Endpoint
    return f"{SERVER_URL}{GMAIL_WEB_REDIRECT_URI}"


def get_google_gemini_key() -> str | None:
    """Get the Google Gemini API key from environment variables."""
    return os.environ.get("GOOGLE_API_KEY")


def get_redis_store_host() -> str | None:
    """Get the redis store host endpoint with port."""
    return os.environ.get("LOCAL_REDIS_STORE_HOST")


def get_cloud_redis_store_host() -> str | None:
    return os.environ.get("CLOUD_REDIS_STORE_HOST")


def get_groq_key():
    """Get the Groq API key from environment variables."""
    return os.environ.get("GROQ_API_KEY")


from langchain_core.runnables.graph import MermaidDrawMethod


def display_graph(
    compiled_graph, use_mermaid: bool = False, use_api: bool = False, max_retry: int = 1
):
    """
    Display the image of the compiled graph.
    """
    if use_mermaid:
        compiled_graph.get_graph().draw_mermaid_png(
            output_file_path="graph.png",
            draw_method=(
                MermaidDrawMethod.PYPPETEER if not use_api else MermaidDrawMethod.API
            ),
            max_retries=max_retry,
        )
    else:
        compiled_graph.get_graph().draw_png()


def clean_and_parse_ai_output(text: str):
    # Step 1: Remove markdown-style code fences
    cleaned = re.sub(r"```json|```", "", text).strip()

    # Step 2: Parse the JSON
    try:
        parsed = json.loads(cleaned)
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}", exc_info=True)
        return None


def deep_merge_dicts(original: dict, updates: dict) -> dict:
    """Recursively merge updates into original dict. Append to lists instead of overwriting."""
    for key, value in updates.items():
        if key in original:
            if isinstance(original[key], dict) and isinstance(value, dict):
                # Merge nested dicts
                original[key] = deep_merge_dicts(original[key], value)
            elif isinstance(original[key], list) and isinstance(value, list):
                # Append unique values to lists
                for v in value:
                    if v not in original[key]:
                        original[key].append(v)
            else:
                # Overwrite scalars
                original[key] = value
        else:
            original[key] = value
    return original


from typing import Any, Union


def safe_json_parse(data: Any, *, default: Any = None) -> Union[dict, list, Any]:
    """
    Universal JSON parser that safely converts strings to Python objects (dict, list, etc.).

    - If `data` is already a dict/list, returns it as-is.
    - If `data` is a JSON string, parses it.
    - If parsing fails, returns `default` (defaults to original data).
    - Works recursively for nested JSON strings (if needed).
    """
    # If already a Python object, just return
    if isinstance(data, (dict, list)):
        return data

    # If None or empty, return default
    if data is None:
        return default

    # Try parsing JSON string
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            # Recursively parse if there are nested JSON strings
            if isinstance(parsed, dict):
                return {k: safe_json_parse(v, default=v) for k, v in parsed.items()}
            elif isinstance(parsed, list):
                return [safe_json_parse(v, default=v) for v in parsed]
            return parsed
        except json.JSONDecodeError:
            return default if default is not None else data

    # For other datatypes (int, float, bool, etc.)
    return data
