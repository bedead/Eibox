from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App details
    APP_NAME: str = "Eibox"
    APP_DESCIPTION: str = ""
    APP_SUMMARY: str = ""
    APP_VERSION: str = "0.1.0"

    # API details
    # TODO: Use this API prefix in all routers and remove the existing hardcoded prefixes in the specific routers
    API_V1_STR: str = "/api/v1"

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
    RUN_JOB_SCHEDULER: bool = False
    SCHEDULER_API_ENABLED: bool = False

    LOG_TYPE: str = "info"  # "info" or "debug"
    LOG_FOLDER_NAME: str = "log_dump"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
