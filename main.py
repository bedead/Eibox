# from langgraph.types import Command
from core import main_graph, MainState
from core.utils.utils import display_graph
from langgraph.config import RunnableConfig

# display_graph(
#     main_graph,
#     use_mermaid=True,
#     use_api=True,
# )

mainState = MainState()
config = RunnableConfig(configurable={"thread_id": 1})


config = {"configurable": {"thread_id": "1"}}


def call_graph(user_input, config=config):
    events = main_graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="updates",
        debug=False,
    )
    for event in events:
        if event["llm_node"]["messages"]:
            print(event["llm_node"]["messages"].content)


while True:
    user_input = input("You :")
    if user_input in ["quit", "exit"]:
        break
    else:
        call_graph(user_input=user_input)
