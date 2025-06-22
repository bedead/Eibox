from core import graph
from core.utils.utils import display_graph

# display_graph(
#     graph,
#     use_mermaid=True,
#     use_api=True,
# )

print(graph.get_graph().draw_mermaid())