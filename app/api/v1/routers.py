"""
Packages all the available routers in one place.
"""

from .endpoints.websocket import router as websocket_router
from .endpoints.cron_api import router as cron_router
from .endpoints.auth import router as auth_router
from .endpoints.test import router as test_router
from .endpoints.gmail_oauth import router as oauth_router
from .endpoints.account_actions import router as account_actions_router

__all__ = [
    "websocket_router",
    "cron_router",
    "auth_router",
    "test_router",
    "oauth_router",
    "account_actions_router",
]
