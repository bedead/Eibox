import logging
from typing import Any, Dict, List

from .types.providers import BaseProvider
from ..base_llm import BaseLLMArch
from ...utils.utils import get_groq_key


class GroqLLM(BaseLLMArch):
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        from groq import Groq

        self.model_provider = BaseProvider.GROQ
        self.client = Groq(api_key=get_groq_key())
        self.model = model_name
        self.logger = logging.getLogger(__name__)

    def generate_response(
        self, contents: str | List[str], system_instruction: str = None, **kwargs
    ) -> str:
        contents = [contents] + [
            value for key, value in kwargs.items() if len(kwargs) > 0
        ]

        return self.chat(
            [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": contents},
            ]
        )

    def chat(self, message: str | List[Dict[str, str]], **kwargs) -> str:
        try:
            completion = self.client.chat.completions.create(
                messages=message,
                model=self.model,
            )
            return completion.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error in GroqLLM chat: {e}")
            return ""
