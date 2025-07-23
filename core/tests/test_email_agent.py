import pytest
from core.agents.email_agent import EmailAgent, EmailState


def test_email_agent_structure():
    # Check that EmailAgent (the compiled graph) has expected attributes
    assert hasattr(EmailAgent, "run"), "EmailAgent should have a 'run' method"
    assert hasattr(
        EmailAgent, "get_graph"
    ), "EmailAgent should have a 'get_graph' method"


def test_email_state_initialization():
    # Test EmailState can be initialized with minimal/default values
    state = EmailState(
        namespace_for_memory=("test",),
        email={"subject": "Test", "body": "Hello"},
        is_mail_important=None,
        email_summary=None,
        is_response_needed=None,
        response_format=None,
        response_email_draft=None,
    )
    assert isinstance(state, dict)
    assert "email" in state


def test_email_agent_run_minimal_state():
    # Run the EmailAgent with a minimal valid state
    input_state = EmailState(
        namespace_for_memory=("test_user00", "test"),
        email={"subject": "Test", "body": "Hello"},
        is_mail_important=None,
        email_summary=None,
        is_response_needed=None,
        response_format=None,
        response_email_draft=None,
    )
    # The run method may expect a list of states or a single state
    result = EmailAgent.run(input_state)
    assert isinstance(result, dict)
    # Check that all expected keys are present in the result
    for key in EmailState.__annotations__:
        assert key in result


def test_email_agent_nodes_executable():
    # Check that each node in the graph can be executed without error
    graph = EmailAgent.get_graph()
    nodes = graph.nodes
    input_state = EmailState(
        namespace_for_memory=("test_user00", "test"),
        email={"subject": "Test", "body": "Hello"},
        is_mail_important=None,
        email_summary=None,
        is_response_needed=None,
        response_format=None,
        response_email_draft=None,
    )
    for node in nodes:
        # Some nodes may require specific input; this test checks for execution errors
        try:
            graph.get_node(node).action(input_state)
        except Exception as e:
            pytest.fail(f"Node '{node}' failed to execute: {e}")
