import asyncio
import os

from colorama import init


from app.core.config import settings

os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
from app.services.agents.email_agent import EmailAgent, EmailState
from app.services.session.session_utils import init_or_get_session

test_username = "satyam"
test_thread_id = "test"

state = EmailState()
init_or_get_session(
    username=test_username,
    thread_id=test_thread_id,
    namespace_for_memory=("auth", "user"),
)


async def main():
    for chunk in await EmailAgent.ainvoke(
        input=state,
        config={
            "configurable": {
                "thread_id": test_thread_id,
                "username": test_username,
            }
        },
        stream_mode="updates",
        print_mode="updates",
    ):
        pass


if __name__ == "__main__":
    asyncio.run(main())
