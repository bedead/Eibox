import os

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_STATE = os.getenv("API_ENVIRONMENT_TYPE", "dev")  # default "dev"
# Get the project root directory
env_file = f".env.{ENV_STATE}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_file, extra="ignore")

    # =============================
    # App Details
    # =============================
    APP_NAME: str = "Eibox"
    APP_DESCIPTION: str = (
        "Eibox is an intelligent email management system that uses AI to read, categorize, prioritize, and respond to emails. It helps users focus on important messages while automating routine email tasks."
    )
    APP_SUMMARY: str = (
        "AI-powered email assistant that reads, categorizes, prioritizes, and responds to emails automatically, helping users manage their inbox efficiently."
    )
    APP_VERSION: str = "0.2.4"

    # =============================
    # API Details
    # =============================
    API_SERVER_URL: str = ""
    API_V1_STR: str = "/api/v1"
    API_DEV_SERVER: bool = True

    # =============================
    # GCP Gmail OAuth
    # =============================
    GMAIL_WEB_CLIENT_ID: str = "your-client-id"
    GMAIL_WEB_CLIENT_SECRET: str = "your-client-secret"
    GMAIL_WEB_REDIRECT_URI: str = "http://localhost/oauth2callback"

    GOOGLE_GMAIL_SCOPE: List[str] = [
        "https://mail.google.com/",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]

    # =============================
    # LLM Providers
    # =============================
    GOOGLE_API_KEY: str = "your-google-api-key"
    GROQ_API_KEY: str = "your-groq-api-key"

    # =============================
    # Langsmith Tracing
    # =============================
    LANGSMITH_TRACING: bool = False
    LANGSMITH_ENDPOINT: str = ""
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = ""

    # =============================
    # Redis DB
    # =============================
    CLOUD_REDIS_STORE_HOST_URL: str = ""
    CLOUD_REDIS_STORE_HOST_PORT: int = 0
    CLOUD_REDIS_STORE_HOST: str = ""

    # =============================
    # JWT config details
    # =============================
    JWT_SECRET: str = ""  # TODO: update later
    JWT_ALGO: str = ""  # TODO: update later

    # =============================
    # App logging / scheduler
    # =============================
    SCHEDULER_API_ENABLED: bool = False
    LOG_TYPE: str = "debug"
    RUN_JOB_SCHEDULER: bool = True  # Set to False for dev server
    LOG_FOLDER_NAME: str = "log_dump"

    def configure_runtime(self) -> None:
        """
        Post-init adjustments based on environment.
        """
        # if self.API_DEV_SERVER:
        #     self.LOG_TYPE = "debug"
        #     self.RUN_JOB_SCHEDULER = False
        # else:
        #     self.LOG_TYPE = "info"
        #     self.RUN_JOB_SCHEDULER = True

        # Compose redis host if not already set
        if not self.CLOUD_REDIS_STORE_HOST and self.CLOUD_REDIS_STORE_HOST_URL:
            self.CLOUD_REDIS_STORE_HOST = (
                f"{self.CLOUD_REDIS_STORE_HOST_URL}:{self.CLOUD_REDIS_STORE_HOST_PORT}"
            )


settings = Settings()
settings.configure_runtime()
