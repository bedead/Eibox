from .endpoints.websocket import router as websocket_router
from .endpoints.cron_api import router as cron_router
from .endpoints.auth import router as auth_router
from .endpoints.test import router as test_router

__all__ = ["websocket_router", "cron_router", "auth_router", "test_router"]
