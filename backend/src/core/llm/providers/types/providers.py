from enum import Enum


class BaseProvider(Enum):
    GOOGLE = "google"
    GROQ = "groq"
    OPENAI = "openai"
