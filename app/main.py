# Standard Library
import os

# Third Party
import uvicorn

# Project Packages
from app.core import settings


# ✅ Must happen before LangChain/LangSmith is imported anywhere
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

if settings.LANGSMITH_TRACING:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"  # new SDK flag
    os.environ["LANGSMITH_TRACING"] = "true"  # legacy flag
    os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
    os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT

# --- only after this, import FastAPI and other deps ---
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.core import scheduler, add_middleware
from app.api.v1.routers import (
    cron_router,
    auth_router,
    oauth_router,
    websocket_router,
    test_router,
    account_actions_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCIPTION,
    summary=settings.APP_SUMMARY,
    version=settings.APP_VERSION,
    lifespan=lifespan,
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

# API ROUTERS WITH VERSIONING
API_V1_PREFIX = "/v1"

# Include cron router (containing schedular start/stop/etc) only if scheduler is enabled
if settings.CRON_SCHEDULER_API_ENABLED:
    app.include_router(cron_router, prefix=f"{API_V1_PREFIX}/cron", tags=["cron"])

app.include_router(auth_router, prefix=f"{API_V1_PREFIX}/auth", tags=["auth"])
app.include_router(oauth_router, prefix=f"{API_V1_PREFIX}/oauth", tags=["oauth"])
app.include_router(account_actions_router, prefix=f"{API_V1_PREFIX}/account_actions", tags=["account"])
app.include_router(
    websocket_router, prefix=f"{API_V1_PREFIX}/chatbot", tags=["chatbot", "websocket"]
)
app.include_router(test_router, prefix=f"{API_V1_PREFIX}/test", tags=["testing"])

# EXAMPLE FOR FUTURE V2
# from app.api.v2.routers import some_new_router
# API_V2_PREFIX = "/v2"
# app.include_router(some_new_router, prefix=f"{API_V2_PREFIX}/some-feature", tags=["new-feature"])

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=settings.APPLICATION_PORT, reload=True)