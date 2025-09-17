import hashlib
from typing import Any, Dict, Generator

import asyncio
from apscheduler.job import Job
from langchain_core.messages import AIMessageChunk


from app.services.agents.chatbot_agent import ChatAgent
from app.services.agents.chatbot_agent.states import ChatbotState


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


async def to_async_gen(sync_gen):
    loop = asyncio.get_event_loop()
    for item in sync_gen:
        yield item
        await asyncio.sleep(0)  # let event loop breathe


def call_graph(
    user_input: str, username: str, thread_id: str, streaming: bool = False
) -> str | Generator[str | list[str | Dict[str, Any]]]:
    state = ChatbotState(
        messages=[{"role": "user", "content": user_input}],
    )
    if streaming:
        # Streaming mode → generator
        def _stream():
            for chunk in ChatAgent.stream(
                input=state,
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "username": username,
                    }
                },
                stream_mode="messages",
                debug=True,
            ):
                if isinstance(chunk, tuple):
                    message_chunk, metadata = chunk
                    if (
                        isinstance(message_chunk, AIMessageChunk)
                        and metadata["langgraph_node"] == "chatbot"
                    ):
                        yield message_chunk.content

        return _stream()  # returns generator

    else:
        # Non-streaming mode → plain string
        response: Any = ChatAgent.invoke(
            input=state,
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "username": username,
                }
            },
            stream_mode="updates",
            print_mode="updates",
        )

        # response["chatbot"] is likely a list
        print(type(response))
        chatbot_output = response[-1]["chatbot"]
        if chatbot_output:
            messages = chatbot_output.get("messages")[0]
            if messages:
                return messages.content
        return "[ERROR] No response from AI"
