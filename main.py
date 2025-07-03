# from core.agents.chatbot_agent.graph import graph
from core.agents.manager_agent.graph import graph

# from core.agents.sequence_graph.graph import graph
from core.agents.email_agent.states import EmailState

from langgraph.types import Command
from core.utils.utils import display_graph
from langgraph.config import RunnableConfig

# print(graph.get_graph().draw_mermaid())

# display_graph(
#     graph,
#     use_mermaid=True,
#     use_api=True,
# )

# mainState = MainState()
config = RunnableConfig(configurable={"thread_id": 1})


import asyncio


async def main():
    while True:
        user_i = input("You : ")
        if user_i in ["exit", "close"]:
            break

        # call astream correctly
        async for each in graph.astream(
            input={"messages": [{"role": "user", "content": user_i}]},
            config=config,
            subgraphs=False,
            debug=True,
        ):
            messages = each.get("chatbotAgent", {}).get("messages", [])
            for msg in messages:
                if getattr(msg, "type", "") in ["ai", "assistant"]:
                    print(f"AI: {msg.content}")


if __name__ == "__main__":
    asyncio.run(main())
