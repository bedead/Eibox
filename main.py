from core.agents.main_graph.graph import graph
from core.agents.shared_state import SharedState
from langgraph.types import Command
from core.utils.utils import display_graph
from langgraph.config import RunnableConfig


# display_graph(
#     graph,
#     use_mermaid=True,
#     use_api=True,
# )


mainState = SharedState()
config = RunnableConfig(configurable={"thread_id": 1})

# if "messages" in event:
#     event["messages"][-1].pretty_print()


async def call():
    while True:
        user_i = input("You : ")
        if user_i in ["exit", "close"]:
            break
        async for chunk in graph.astream(
            input={"messages": {"role": "user", "content": user_i}},
            config=config,
            stream_mode="updates",
            subgraphs=False,
        ):
            for node_id, value in chunk.items():
                # print(node_id)
                # not usefull as for now
                if node_id == "__interrupt__":
                    question = value[0].value.get("question")
                    print(f"Interrupt Question : {question}")
                    command = Command(resume={"data": input("You : ")})
                    resumed_output = graph.astream(command, config=config)

                    print(resumed_output)
                else:
                    print(f"STEP {node_id} : {value}")


import asyncio

asyncio.run(call())
