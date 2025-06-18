from typing import Union

from pydantic import BaseModel

from .models_google import GoogleModel
from .models_groq import GroqModel
from .providers import BaseProvider

LLMModel = Union[GoogleModel, GroqModel]


class ModelSelector(BaseModel):
    provider: BaseProvider
    model: LLMModel

    def get_model_string(self) -> str:
        return self.model.value

    def get_provider_string(self) -> str:
        return self.provider.value
