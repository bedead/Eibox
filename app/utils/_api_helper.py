import hashlib
from typing import Any, Dict, AsyncGenerator

from apscheduler.job import Job
from langchain_core.messages import AIMessageChunk, HumanMessage


from app.core.logging import logger
from app.services.agents.chatbot_agent import ChatAgent, ChatbotState
from app.utils._text_helper import _to_text


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


def second_to_minutes(seconds: int) -> float:
    """Convert seconds to minutes rounded to int"""
    return round(seconds / 60)


def minutes_to_seconds(minutes: int) -> int:
    """Convert minutes to seconds"""
    return minutes * 60
