import hashlib
import json
import re
from typing import Any, Dict, AsyncGenerator, List, Literal, Optional, Union

from apscheduler.job import Job
from fastapi import WebSocket
from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_core.runnables.graph import MermaidDrawMethod


from app.core import logger
from app.schemas import ChatSession
from app.services import ChatAgent, ChatbotState
from app.services import get_session


def job_to_dict(job: Job) -> Dict[str, Any]:
    """
    Convert an APScheduler Job object to a dictionary representation.
    """
    return {
        "id": job.id,
        "name": getattr(job, "name", None),
        "func": getattr(job, "func_ref", None),
        "args": list(job.args) if hasattr(job, "args") else [],
        "kwargs": dict(job.kwargs) if hasattr(job, "kwargs") else {},
        "trigger": str(job.trigger),
        "executor": getattr(job, "executor", None),
        "misfire_grace_time": getattr(job, "misfire_grace_time", None),
        "coalesce": getattr(job, "coalesce", None),
        "max_instances": getattr(job, "max_instances", None),
        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        "pending": job.pending if hasattr(job, "pending") else None,
    }


def job_to_str(job: Job) -> str:
    """
    Convert an APScheduler Job object to a str representation.
    """
    result = job_to_dict(job)
    return "".join(f"{key} : {value}" for key, value in result.items())


def hash_password(password: str) -> str:
    """Very basic hash, for demonstration only. Use bcrypt or Argon2 in production."""
    return hashlib.sha256(password.encode()).hexdigest()


async def call_graph(
    user_input: str, username: str, thread_id: str, streaming: bool = False
) -> AsyncGenerator[str, None]:
    state = ChatbotState(
        messages=[HumanMessage(content=user_input)],
    )

    if streaming:
        # Streaming mode → yield tokens
        async def _stream_token() -> AsyncGenerator[str, None]:
            async for chunk in ChatAgent.astream(
                input=state,
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "username": username,
                    }
                },
                stream_mode="messages",
                # debug=True,
            ):
                if isinstance(chunk, tuple):
                    message_chunk, metadata = chunk
                    if (
                        isinstance(message_chunk, AIMessageChunk)
                        and metadata["langgraph_node"] == "chatbot"
                    ):
                        yield _to_text(message_chunk.content)

        return _stream_token()

    else:
        # Non-streaming mode → yield whole chatbot messages (step-level)
        async def _stream_messages() -> AsyncGenerator[str, None]:
            async for chunk in ChatAgent.astream(  # <- sync generator
                input=state,
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "username": username,
                    }
                },
                stream_mode="updates",
                # print_mode="updates",
            ):
                # Debug
                # logger.debug(f"Chunk: {chunk}")
                if not isinstance(chunk, dict):
                    continue

                chatbot_output = chunk.get("chatbot")
                if chatbot_output:
                    m = chatbot_output.get("messages", [])[0]
                    if m and hasattr(m, "content"):
                        response = _to_text(m.content)
                        if response and response != "":
                            yield response

        return _stream_messages()


async def push_proactive_message(username: str, thread_id: str, message: str):
    session: Optional[ChatSession] | None = get_session(username, thread_id)
    if session and session.websocket:
        ws: WebSocket = session.websocket
        try:
            await ws.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send proactive message: {e}", exc_info=True)


def second_to_minutes(seconds: int) -> float:
    """Convert seconds to minutes rounded to int"""
    return round(seconds / 60)


def minutes_to_seconds(minutes: int) -> int:
    """Convert minutes to seconds"""
    return minutes * 60


def _to_text(content: Any) -> str:
    # Normalize content to string for consistent generator typing
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                # common LangChain content dicts may have 'text'
                text = part.get("text")
                if isinstance(text, str):
                    parts.append(text)
                else:
                    # best-effort fallback
                    parts.append(str(part))
            else:
                parts.append(str(part))
        return "".join(parts)
    return content if isinstance(content, str) else str(content)


def clean_and_parse_ai_output(text: str):
    # Step 1: Remove markdown-style code fences
    cleaned = re.sub(r"```json|```", "", text).strip()

    # Step 2: Parse the JSON
    try:
        parsed = json.loads(cleaned)
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}", exc_info=True)
        return None


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


def deep_merge_dicts(original: dict, updates: dict) -> dict:
    """Recursively merge updates into original dict. Append to lists instead of overwriting."""
    for key, value in updates.items():
        if key in original:
            if isinstance(original[key], dict) and isinstance(value, dict):
                # Merge nested dicts
                original[key] = deep_merge_dicts(original[key], value)
            elif isinstance(original[key], list) and isinstance(value, list):
                # Append unique values to lists
                for v in value:
                    if v not in original[key]:
                        original[key].append(v)
            else:
                # Overwrite scalars
                original[key] = value
        else:
            original[key] = value
    return original


def safe_json_parse(
    data: Union[str, Dict[str, Any], List[Any]],
    get: Literal["dict", "list"] = "dict",
) -> Union[Dict[str, Any], List[Any], Any]:
    """
    Universal JSON parser that safely converts strings to Python objects (dict, list, etc.).

    - If `data` is already a dict/list, returns it as-is.
    - If `data` is a JSON string, parses it.
    - If parsing fails, returns `default` (defaults to original data).
    - Works recursively for nested JSON strings (if needed).
    """
    # If already a Python object, just return
    if isinstance(data, (dict, list)):
        return data

    # Try parsing JSON string
    if isinstance(data, str):
        data = data.strip()
        # Only try parsing if it *looks like* JSON
        if data.startswith("{") or data.startswith("["):
            try:
                parsed = json.loads(data)

                # Ensure type matches `get`
                if get == "dict" and not isinstance(parsed, dict):
                    raise ValueError("Expected dict but got something else")
                if get == "list" and not isinstance(parsed, list):
                    raise ValueError("Expected list but got something else")

                # Recursively parse if there are nested JSON strings
                if isinstance(parsed, dict):
                    return {str(k): safe_json_parse(v, get="dict") for k, v in parsed.items()}  # type: ignore
                elif isinstance(parsed, list):
                    return [safe_json_parse(v, get="list") for v in parsed]  # type: ignore
                return parsed
            except (TypeError, json.JSONDecodeError) as e:
                raise ValueError("Invalid JSON input") from e
