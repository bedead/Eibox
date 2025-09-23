import asyncio

from app.services.session.session_utils import init_or_get_session
from app.utils._api_helper import call_graph

test_username = "satyam"
test_thread_id = "test"
session = init_or_get_session(
    username=test_username,
    thread_id=test_thread_id,
    namespace_for_memory=("auth", "user"),
)


async def main():
    while True:
        user_input = input("\nUser Input: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        print("Chatbot Response: ", end="", flush=True)
        async for msg in await call_graph(
            user_input=user_input,
            username=test_username,
            thread_id=test_thread_id,
            streaming=False,
        ):
            print(msg, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
