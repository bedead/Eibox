# from core.agents.chatbot_agent.graph import graph
from core.agents.manager_agent.graph import AgentManagerWithAioconsole

# from core.agents.sequence_graph.graph import graph
from core.agents.email_agent.states import EmailState

from langgraph.types import Command
from core.utils.utils import display_graph
import asyncio

# print(graph.get_graph().draw_mermaid())

# display_graph(
#     graph,
#     use_mermaid=True,
#     use_api=True,
# )


# mainState = MainState()
async def main():
    from langchain_core.runnables import RunnableConfig

    config = RunnableConfig(configurable={"thread_id": 1})

    manager = AgentManagerWithAioconsole(config)
    await manager.run()


if __name__ == "__main__":
    asyncio.run(main())
