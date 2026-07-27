import pytest

from lightspeed_agents.models.agent import Agent
from lightspeed_agents.registry.registry import AgentRegistry


@pytest.fixture
def registry():
    return AgentRegistry()


def test_register_and_list(registry):
    agent = Agent(id="a1", name="Agent One", role="Role One")
    registry.register(agent)
    assert len(registry.list()) == 1
    assert registry.list()[0].id == "a1"


def test_list_empty(registry):
    assert registry.list() == []


def test_register_multiple(registry):
    for i in range(5):
        registry.register(Agent(id=f"a{i}", name=f"Agent {i}", role="Role {i}"))
    assert len(registry.list()) == 5


def test_find_by_id(registry):
    registry.register(Agent(id="cto", name="CTO", role="Tech"))
    found = registry.find("cto")
    assert found is not None
    assert found.id == "cto"


def test_find_by_name(registry):
    registry.register(Agent(id="x", name="Chief Tech Officer", role="Tech"))
    found = registry.find("Chief Tech Officer")
    assert found is not None
    assert found.id == "x"


def test_find_by_name_case_insensitive(registry):
    registry.register(Agent(id="x", name="CTO", role="Tech"))
    assert registry.find("cto") is not None
    assert registry.find("CTO") is not None


def test_find_not_found(registry):
    assert registry.find("nonexistent") is None
