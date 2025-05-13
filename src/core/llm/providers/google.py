from typing import Dict, List
import logging
from google.genai.chats import Chat
from .types.providers import BaseProvider
from .types.models_google import GoogleModel
from ..base_llm import BaseLLMArch
from ...utils.utils import get_google_gemini_key


class GeminiLLM(BaseLLMArch):
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        from google import genai

        self.model_provider = BaseProvider.GOOGLE
        self.client = genai.Client(api_key=get_google_gemini_key())
        self.model_name: GoogleModel = model_name
        self.logger = logging.getLogger(__name__)

    def generate_response(
        self, contents: str | List[str], system_instruction, **kwargs
    ) -> str:
        from google.genai.types import GenerateContentConfig

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                config=GenerateContentConfig(
                    system_instruction=system_instruction,
                ),
                contents=[contents]
                + [value for key, value in kwargs.items() if len(kwargs) > 0],
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return ""

    def initialize_chat(self, **kwargs) -> Chat:
        """Initialize chat with the model"""
        return self.client.chats.create(model=self.model_name)

    def chat(self, message: str | List[Dict[str, str]], **kwargs) -> str:
        try:
            response = kwargs.get("chat_instance").send_message(message)
            return response.text
        except Exception as e:
            self.logger.error(f"Error in GeminiLLM chat: {e}")
            return ""
