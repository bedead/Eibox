import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App details
    APP_NAME: str = os.environ.get("APP_NAME", "")
    APP_DESCIPTION: str = os.environ.get("APP_DESCIPTION", "")
    APP_SUMMARY: str = os.environ.get("APP_SUMMARY", "")
    APP_VERSION: str = os.environ.get("APP_VERSION", "")

    # API details
    # TODO: Use this API prefix in all routers and remove the existing hardcoded prefixes in the specific routers
    API_V1_STR: str = "/api/v1"
    API_DEV_SERVER: bool = (
        os.environ.get("API_DEV_SERVER", "True").lower() == "true"
    )  # Turn False if want to use PRODUCTIOn SERVER URL

    # Storage config details
    REDIS_URL: str = ""  # TODO: read from secret env file

    # JWT config details
    JWT_SECRET: str = ""  # TODO: study and update
    JWT_ALGO: str = ""  # TODO: study and update

    # Gmail OAuth2 details
    GOOGLE_GMAIL_SCOPE: List[str] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]

    # App settings details
    SCHEDULER_API_ENABLED: bool = False
    if API_DEV_SERVER:
        LOG_TYPE: str = "debug"  # "info" or "debug" for Dev Server
        RUN_JOB_SCHEDULER: bool = False
    else:
        LOG_TYPE: str = "info"  # for Prod Server
        RUN_JOB_SCHEDULER: bool = True
    LOG_FOLDER_NAME: str = "log_dump"
    RUN_JOB_SCHEDULER: bool = False  # default set to false to reduce overhead

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
