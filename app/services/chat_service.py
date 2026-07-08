from typing import AsyncGenerator, Optional

from fastapi import WebSocket
from langchain_core.messages import AIMessageChunk, HumanMessage

from app.core import logger
from app.db import ChatSession
from app.utils import _to_text
from app.services.agents.chatbot_agent.graph import graph as ChatAgent
from app.services.agents.chatbot_agent.states import ChatbotState
from app.services.session.get_session import get_session


async def call_main_agent(
    user_input: str, username: str, thread_id: str, streaming: bool = True
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
                        text = _to_text(message_chunk.content)
                        # print(f"Token: {text}")
                        yield text

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
                            # print(f"Response: {response}")
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
