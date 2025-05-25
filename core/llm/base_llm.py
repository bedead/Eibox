from abc import ABC, abstractmethod
from typing import Dict, List


class BaseLLMArch(ABC):
    """Abstract base class for LLM callings implementations"""

    model_provider: str = None

    @abstractmethod
    def generate_response(
        self, contents: str | List[str], system_instruction: str = None, **kwargs
    ) -> str:
        """Generate single-turn response from the LLM"""
        pass

    @abstractmethod
    def chat(self, message: str | List[Dict[str, str]], **kwargs) -> str:
        """Generate response based on chat history"""
        pass
