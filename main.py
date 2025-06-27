from langgraph.types import Command
from core import graph
from core.agents.sequence_graph.states import SequenceState
from core.utils.utils import display_graph
from langgraph.config import RunnableConfig

# display_graph(
#     graph,
#     use_mermaid=True,
#     use_api=True,
# )
inputState = SequenceState()
config = RunnableConfig(configurable={"thread_id": 1})
# result = graph.invoke(
#     input=input, config=RunnableConfig(configurable={"thread_id": 1}), debug=True
# )
# print(result)


for chunk in graph.stream(
    input=inputState,
    config=config,
    #   stream_mode="values"
):
    for id, value in chunk.items():
        if id == "__interrupt__":
            # print(value)
            # Send the received data to the other user
            question = value[0].value["question"]
            response = input(f"{question}")
            # resume_map = {
            #     i.interrupt_id: f"{response}"
            #     for i in graph.get_state(config=config).interrupts
            # }
            graph.invoke(Command(resume=response), config=config)
