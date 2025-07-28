from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import *

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.debug = True
app.include_router(auth_router, prefix="/cron", tags=["cron"])
app.include_router(cron_router, prefix="/auth", tags=["auth"])
app.include_router(websocket_router, prefix="/ws", tags=["chatbot", "websocket"])
# app.include_router(websocket_router)
