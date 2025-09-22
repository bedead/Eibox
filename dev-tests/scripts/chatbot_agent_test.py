from typing import Generator

from app.services.agents.chatbot_agent import ChatbotState, ChatAgent
from app.services.session.session_utils import init_or_get_session
from app.utils._api_helper import _to_text

test_username = "satyam"
test_thread_id = "test"
session = init_or_get_session(
    username=test_username,
    thread_id=test_thread_id,
    namespace_for_memory=("auth", "user"),
)


def _stream_messages(user_input: str):
    state = ChatbotState(
        messages=[{"role": "user", "content": user_input}],
    )
    for chunk in ChatAgent.stream(  # <- sync generator
        input=state,
        config={
            "configurable": {
                "thread_id": test_thread_id,
                "username": test_username,
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


if __name__ == "__main__":
    while True:
        user_input = input("\nUser Input: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        print("Chatbot Response: ", end="", flush=True)
        for msg in _stream_messages(user_input=user_input):
            print(msg, end="", flush=True)
