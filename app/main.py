from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.middleware import add_middleware
from app.core.config import settings
from app.api.v1.routers import (
    cron_router,
    auth_router,
    oauth_router,
    websocket_router,
    test_router,
)


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCIPTION,
    summary=settings.APP_SUMMARY,
    version=settings.APP_VERSION,
    # lifespan=lifespan,
)

# Call middleware setup here (before app starts serving requests)
add_middleware(app)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(cron_router, prefix="/cron", tags=["cron"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(oauth_router, prefix="/oauth", tags=["oauth"])
app.include_router(websocket_router, prefix="/ws", tags=["chatbot", "websocket"])
app.include_router(test_router, prefix="/test", tags=["testing"])
