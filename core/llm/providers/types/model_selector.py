from typing import Union

from .models_google import GoogleModel
from .models_groq import GroqModel
from .providers import BaseProvider

LLMModel = Union[GoogleModel, GroqModel]


class ModelSelector:
    def __init__(self, provider: BaseProvider, model: LLMModel):
        self.provider = provider
        self.model = model

    def get_model_string(self):
        return self.model.value
