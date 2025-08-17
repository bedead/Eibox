from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Eibox"
    REDIS_URL: str = ""  # TODO: read from secret env file
    JWT_SECRET: str = "" # TODO: study and update
    JWT_ALGO: str = "" # TODO: study and update

    class Config:
        env_file = ".env"


settings = Settings()
