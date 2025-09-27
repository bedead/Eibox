"""
Common utility functions for environment variable management, JSON parsing, dictionary merging, and graph visualization.
This module provides:
- Functions to retrieve required environment variables for GCP, Gmail, Redis, Groq, and Google Gemini API keys.
- Error logging and exception raising for missing environment variables.
- Utilities for displaying LangChain graphs using Mermaid or PNG formats.
- Functions for cleaning and parsing AI-generated JSON output.
- Deep dictionary merging with support for nested dicts and list appending.
- Safe universal JSON parsing for strings and Python objects.
"""

import json
from typing import Any, Dict, List, Literal, Union


from dotenv import load_dotenv
from langchain_core.runnables.graph import MermaidDrawMethod

load_dotenv()

from app.core.logging import logger
from app.core.config import settings


def get_gcp_client_id() -> str:
    """Returns GOOGLE CLOUD PROVIDERS web client Id."""

    var: str | None = settings.GMAIL_WEB_CLIENT_ID
    if var is None:
        logger.critical(f"Missing required environment variable: GMAIL_WEB_CLIENT_ID")
        raise RuntimeError("Missing required environment variable: GMAIL_WEB_CLIENT_ID")
    return var


def get_gcp_client_secret() -> str:
    """Returns GOOGLE CLOUD PROVIDERS web client secret."""
    var: str | None = settings.GMAIL_WEB_CLIENT_SECRET
    if var is None:
        logger.critical(
            f"Missing required environment variable: GMAIL_WEB_CLIENT_SECRET"
        )
        raise RuntimeError(
            "Missing required environment variable: GMAIL_WEB_CLIENT_SECRET"
        )
    return var


def get_api_server_url() -> str:
    """Returns API Server URL."""
    var: str | None = settings.API_SERVER_URL
    if var is None:
        logger.critical(f"Missing required environment variable: API_SERVER_URL")
        raise RuntimeError("Missing required environment variable: API_SERVER_URL")
    return var


def get_gmail_redirect_uri() -> str:
    """Returns the Gmail OAUTH Redirect URI for Server based on Config env."""
    # Get the server URL based on the environment
    api_server_url: str = get_api_server_url()

    # Get the default GMAIL_WEB_REDIRECT_URI Endpoint for redirect
    gmail_web_redirect_uri: str | None = settings.GMAIL_WEB_REDIRECT_URI

    # If GMAIL_WEB_REDIRECT_URI env variable not found raise and log error
    if gmail_web_redirect_uri == None:
        logger.critical(
            f"Missing required environment variable: GMAIL_WEB_REDIRECT_URI"
        )
        raise RuntimeError(
            "Missing required environment variable: GMAIL_WEB_REDIRECT_URI"
        )

    # Return the combined URL Endpoint
    return f"{api_server_url}{gmail_web_redirect_uri}"


def get_google_gemini_key() -> str | None:
    """Returns the Google Gemini API key from environment variables."""
    var: str | None = settings.GOOGLE_API_KEY
    if var is None:
        logger.critical(f"Missing required environment variable: GOOGLE_GEMINI_API_KEY")
        raise RuntimeError(
            "Missing required environment variable: GOOGLE_GEMINI_API_KEY"
        )

    return var


def get_cloud_redis_store_host() -> str | None:
    """Get the cloud redis store host endpoint with port."""
    var: str | None = settings.CLOUD_REDIS_STORE_HOST
    if var is None:
        logger.critical(
            f"Missing required environment variable: CLOUD_REDIS_STORE_HOST"
        )
        raise RuntimeError(
            "Missing required environment variable: CLOUD_REDIS_STORE_HOST"
        )
    return var


def get_groq_key():
    """Get the Groq API key from environment variables."""
    var: str | None = settings.GROQ_API_KEY
    if var is None:
        logger.critical(f"Missing required environment variable: GROQ_API_KEY")
        raise RuntimeError("Missing required environment variable: GROQ_API_KEY")
    return var


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


def safe_json_parse(
    data: Union[str, Dict[str, Any], List[Any]],
    get: Literal["dict", "list"] = "dict",
) -> Union[Dict[str, Any], List[Any], Any]:
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

    # Try parsing JSON string
    if isinstance(data, str):
        data = data.strip()
        # Only try parsing if it *looks like* JSON
        if data.startswith("{") or data.startswith("["):
            try:
                parsed = json.loads(data)

                # Ensure type matches `get`
                if get == "dict" and not isinstance(parsed, dict):
                    raise ValueError("Expected dict but got something else")
                if get == "list" and not isinstance(parsed, list):
                    raise ValueError("Expected list but got something else")

                # Recursively parse if there are nested JSON strings
                if isinstance(parsed, dict):
                    return {str(k): safe_json_parse(v, get="dict") for k, v in parsed.items()}  # type: ignore
                elif isinstance(parsed, list):
                    return [safe_json_parse(v, get="list") for v in parsed]  # type: ignore
                return parsed
            except (TypeError, json.JSONDecodeError) as e:
                raise ValueError("Invalid JSON input") from e
