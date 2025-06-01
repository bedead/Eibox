from enum import Enum
from google import genai
from dotenv import load_dotenv
import os
from google.genai.types import GenerateContentConfig
from typing import List


load_dotenv()


def get_google_gemini_key():
    """Get the Google Gemini API key from environment variables."""
    return os.environ.get("GOOGLE_API_KEY")


def get_groq_key():
    """Get the Groq API key from environment variables."""
    return os.environ.get("GROQ_API_KEY")


def get_gemini_client():
    key = get_google_gemini_key()
    client = genai.Client(api_key=key)
    return client


def get_single_call_gemini_response(
    client,
    system_instruction: str = None,
    model_name="gemini-1.5-flash",
    contents: List[str] = ["what can you do?"],
):
    response = client.models.generate_content(
        model=model_name,
        config=GenerateContentConfig(
            system_instruction=system_instruction,
        ),
        contents=contents,
    )
    return response


def get_chat_gemini_response(
    client, model_name="gemini-2.0-flash", question="what can you do?"
):
    chat = client.chats.create(model=model_name)
    response = chat.send_message(message=question)
    return response


from langchain_core.runnables.graph import MermaidDrawMethod


def display_graph(
    compiled_graph, use_mermaid: bool = False, use_api: bool = False, max_retry: int = 1
):
    """
    Display the image of the compiled graph.
    """
    if use_mermaid:
        compiled_graph.get_graph().draw_mermaid_png(
            output_file_path="graph.png",
            draw_method=(
                MermaidDrawMethod.PYPPETEER if not use_api else MermaidDrawMethod.API
            ),
            max_retries=max_retry,
        )
    else:
        compiled_graph.get_graph().draw_png()


from langgraph.checkpoint.base import SerializerProtocol
from pydantic import BaseModel
from typing import Any, Tuple
import orjson
from core.agents.sequence_graph.states import SequenceState

import orjson
from enum import Enum
from pydantic import BaseModel
from typing import Any, Tuple, Type

from core.agents.sequence_graph.states import SequenceState  # Import your model(s)


class SafePydanticSerializer:
    def __init__(self, exclude_fields: set = None):
        self.EXCLUDE_FIELDS = exclude_fields or {
            "gmail_tool",
            "ai_toolkit",
            "selected_model",
            "gmail_toolkit_status",
        }

        # 👇 Register all known models you want to auto-rehydrate
        self.model_registry: dict[str, Type[BaseModel]] = {
            "SequenceState": SequenceState,
            # Add more as needed
        }

    def dumps(self, obj: Any) -> bytes:
        return orjson.dumps(self._sanitize(obj))

    def loads(self, data: bytes) -> Any:
        return orjson.loads(data)

    def dumps_typed(self, obj: Any) -> Tuple[str, bytes]:
        type_name = type(obj).__name__
        return type_name, self.dumps(obj)

    def loads_typed(self, data: Tuple[str, bytes]) -> Any:
        type_name, payload = data
        raw = self.loads(payload)

        if isinstance(raw, dict) and type_name in self.model_registry:
            model_cls = self.model_registry[type_name]
            return model_cls(**raw)

        return raw

    def _sanitize(self, obj: Any) -> Any:
        if isinstance(obj, BaseModel):
            return obj.model_dump(exclude=self.EXCLUDE_FIELDS)
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, dict):
            return {k: self._sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._sanitize(i) for i in obj]
        elif hasattr(obj, "__str__"):
            return str(obj)  # Fallback
        else:
            return obj
