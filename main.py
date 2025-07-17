import asyncio
from core.agents.chatbot_agent import ChatAgent  # adjust the import as needed
from langchain_core.messages import AIMessage, AIMessageChunk


async def main():
    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            break

        async for chunk in ChatAgent.astream(
            input={"messages": [{"role": "user", "content": user_input}]},
            config={"configurable": {"thread_id": "test", "user_id": "satyam"}},
            stream_mode="messages",
        ):
            if isinstance(chunk, tuple):
                message_chunk, metadata = chunk
                if isinstance(message_chunk, AIMessageChunk):
                    print(f"AI: {message_chunk.content}")


if __name__ == "__main__":
    asyncio.run(main())
