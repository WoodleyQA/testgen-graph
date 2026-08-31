import logging
from langgraph.graph import StateGraph, END

from .state import GraphState
from .llm_guard import log_state_transition
from .nodes.generate_cases import generate_cases
from .nodes.generate_skeletons import generate_skeletons

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


def with_state_logging(node_name, node_fn):
    """
    Wraps a node so every transition logs state automatically — logging lives at
    the graph level, not duplicated inside each node function.
    """
    def wrapped(state: GraphState) -> GraphState:
        result = node_fn(state)
        log_state_transition(node_name, result)
        return result
    return wrapped


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("generate_cases", with_state_logging("generate_cases", generate_cases))
    graph.add_node("generate_skeletons", with_state_logging("generate_skeletons", generate_skeletons))

    graph.set_entry_point("generate_cases")
    graph.add_edge("generate_cases", "generate_skeletons")
    graph.add_edge("generate_skeletons", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({
        "requirement": "User can reset their password via a link emailed to their registered address. Reset links expire after 1 hour and can only be used once.",
        "generated_cases": [],
        "skeletons": [],
        "run_metadata": {},
    })
    print(f"Generated {len(result['generated_cases'])} cases, {len(result['skeletons'])} skeletons")
