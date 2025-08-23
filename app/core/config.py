from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Eibox"
    APP_DESCIPTION: str = ""
    REDIS_URL: str = ""  # TODO: read from secret env file
    JWT_SECRET: str = ""  # TODO: study and update
    JWT_ALGO: str = ""  # TODO: study and update
    GOOGLE_GMAIL_SCOPE: List[str] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]

    LOG_TYPE: str = "info"  # "info" or "debug"
    LOG_FOLDER_NAME: str = "log_dump"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
