from enum import Enum
from google import genai
from dotenv import load_dotenv
import os
from google.genai.types import GenerateContentConfig
from typing import Dict, List, Any, Optional


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
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer


class ObjectMetadataSerializer(SerializerProtocol):
    """Custom serializer that stores object metadata and reconstructs objects on load."""

    def __init__(self, base_serializer: Optional[SerializerProtocol] = None):
        self.base_serializer = base_serializer or JsonPlusSerializer()

    def _serialize_special_objects(self, obj: Any) -> Any:
        """Convert special objects to metadata representations."""
        if isinstance(obj, dict):
            return {k: self._serialize_special_objects(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return type(obj)(self._serialize_special_objects(item) for item in obj)

        obj_class_name = obj.__class__.__name__

        if obj_class_name == "GmailToolKit":
            return {
                "__object_type__": "GmailToolKit",
                "__metadata__": {
                    "max_results": getattr(obj, "max_results", 1),
                    "status": "initialized",
                },
            }
        elif obj_class_name == "GmailToolKitRunningStatus":
            return {
                "__object_type__": "GmailToolKitRunningStatus",
                "__metadata__": {
                    "value": obj.value if hasattr(obj, "value") else str(obj)
                },
            }
        elif obj_class_name == "ModelSelector":
            return {
                "__object_type__": "ModelSelector",
                "__metadata__": {
                    "model_name": getattr(obj, "model_name", "default"),
                    "provider": getattr(obj, "provider", "default"),
                },
            }
        elif obj_class_name == "AIToolkit":
            model_info = getattr(obj, "model", None)
            if (
                model_info
                and hasattr(model_info, "__class__")
                and model_info.__class__.__name__ == "ModelSelector"
            ):
                return {
                    "__object_type__": "AIToolkit",
                    "__metadata__": {
                        "model_name": getattr(model_info, "model_name", "default"),
                        "provider": getattr(model_info, "provider", "default"),
                        "status": "initialized",
                    },
                }

        return obj

    def _deserialize_special_objects(self, obj: Any) -> Any:
        """Reconstruct objects from metadata representations."""
        if isinstance(obj, dict):
            # Handle the case where the entire dict might be a serialized object
            if "__object_type__" in obj:
                return self._reconstruct_object(obj)

            # Process nested dictionaries
            result = {}
            model_selector_cache = {}

            # First pass: find and reconstruct ModelSelector objects
            for k, v in obj.items():
                if isinstance(v, dict) and v.get("__object_type__") == "ModelSelector":
                    model_selector_cache[k] = self._reconstruct_object(v)

            # Second pass: reconstruct all objects
            for k, v in obj.items():
                if isinstance(v, dict) and "__object_type__" in v:
                    if v["__object_type__"] == "ModelSelector":
                        result[k] = model_selector_cache[k]
                    elif v["__object_type__"] == "AIToolkit":
                        # Use the cached ModelSelector if available
                        model_selector = model_selector_cache.get("selected_model")
                        if model_selector:
                            from core.llm.ai_toolkit import get_ai_toolkit

                            result[k] = get_ai_toolkit(model=model_selector)
                        else:
                            result[k] = self._reconstruct_object(v)
                    else:
                        result[k] = self._reconstruct_object(v)
                else:
                    result[k] = self._deserialize_special_objects(v)

            return result
        elif isinstance(obj, (list, tuple)):
            return type(obj)(self._deserialize_special_objects(item) for item in obj)

        return obj

    def _reconstruct_object(self, obj_dict: Dict[str, Any]) -> Any:
        """Reconstruct a single object from its metadata."""
        obj_type = obj_dict["__object_type__"]
        metadata = obj_dict["__metadata__"]

        if obj_type == "GmailToolKit":
            from core.gmail.gmail_toolkit import GmailToolKit

            return GmailToolKit(max_results=metadata.get("max_results", 1))

        elif obj_type == "GmailToolKitRunningStatus":
            from core.gmail.status import GmailToolKitRunningStatus

            return GmailToolKitRunningStatus.PAUSED

        elif obj_type == "ModelSelector":
            from core.llm.providers.types.model_selector import ModelSelector

            return ModelSelector(
                model=metadata.get("model_name", "default"),
                provider=metadata.get("provider", "default"),
            )

        elif obj_type == "AIToolkit":
            from core.llm.ai_toolkit import get_ai_toolkit
            from core.llm.providers.types.model_selector import ModelSelector

            model_selector = ModelSelector(
                model=metadata.get("model_name", "default"),
                provider=metadata.get("provider", "default"),
            )
            return get_ai_toolkit(model=model_selector)

        return obj_dict  # Fallback

    def dumps_typed(self, obj: Any) -> tuple[str, bytes]:
        """Serialize object, converting special objects to metadata."""
        processed_obj = self._serialize_special_objects(obj)
        return self.base_serializer.dumps_typed(processed_obj)

    def loads_typed(self, data: tuple[str, bytes]) -> Any:
        """Deserialize object, reconstructing special objects from metadata."""
        obj = self.base_serializer.loads_typed(data)
        return self._deserialize_special_objects(obj)

    def dumps(self, obj: Any) -> bytes:
        """Serialize object to bytes."""
        processed_obj = self._serialize_special_objects(obj)
        return self.base_serializer.dumps(processed_obj)

    def loads(self, data: bytes) -> Any:
        """Deserialize object from bytes."""
        obj = self.base_serializer.loads(data)
        return self._deserialize_special_objects(obj)
