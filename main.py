from core.agents.main_graph.graph import graph
from core.agents.shared_state import SharedState
from core.utils.utils import display_graph
from langgraph.config import RunnableConfig


# display_graph(
#     graph,
#     use_mermaid=True,
#     use_api=True,
# )


mainState = SharedState()
config = RunnableConfig(configurable={"thread_id": 1})


while True:
    user_i = input("You : ")
    if user_i in ["exit", "close"]:
        break
    chunk = graph.stream(
        input={"messages": {"role": "user", "content": user_i}},
        config=config,
        stream_mode="values",
    )
    for event in chunk:
        if "messages" in event:
            event["messages"][-1].pretty_print()
        # print(node_id)
        # not usefull as for now
        # if node_id == "__interrupt__":
        #     # question = value[0].value.get("question", "Human input required")
        #     command = Command(resume={"data": input("You : ")})
        #     resumed_output = graph.stream(command, config=config)
