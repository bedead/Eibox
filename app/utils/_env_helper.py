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


from dotenv import load_dotenv

load_dotenv()

from app.core import logger, settings


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
