import pytest
from unittest.mock import patch, MagicMock

from lightspeed_agents.core.agent_runner import AgentRunner
from lightspeed_agents.registry.registry import registry
from lightspeed_agents.models.agent import Agent


@pytest.fixture(autouse=True)
def clean_registry():
    registry.agents = []
    yield
    registry.agents = []


@patch("lightspeed_agents.core.agent_runner.get_provider")
@patch("lightspeed_agents.core.agent_runner.load_agents")
def test_runner_returns_response(mock_load, mock_get_provider, tmp_path):
    mock_load.return_value = registry
    registry.register(
        Agent(
            id="cto",
            name="CTO",
            role="Tech Executive",
            department="engineering",
            tools=["python"],
            permissions=["read"],
            model="ollama",
        )
    )

    mock_provider = MagicMock()
    mock_provider.complete.return_value = "LLM response here"
    mock_get_provider.return_value = mock_provider

    runner = AgentRunner(memory_dir=str(tmp_path / "memory"))
    result = runner.run("cto", "do something")

    assert result["agent"] == "cto"
    assert result["name"] == "CTO"
    assert result["response"] == "LLM response here"
    assert result["task"] == "do something"


@patch("lightspeed_agents.core.agent_runner.get_provider")
@patch("lightspeed_agents.core.agent_runner.load_agents")
def test_runner_agent_not_found(mock_load, mock_get_provider, tmp_path):
    mock_load.return_value = registry
    runner = AgentRunner(memory_dir=str(tmp_path / "memory"))

    with pytest.raises(ValueError, match="not found"):
        runner.run("nonexistent", "task")


@patch("lightspeed_agents.core.agent_runner.get_provider")
@patch("lightspeed_agents.core.agent_runner.load_agents")
def test_runner_passes_system_prompt(mock_load, mock_get_provider, tmp_path):
    mock_load.return_value = registry
    registry.register(
        Agent(
            id="cfo",
            name="CFO",
            role="Finance Executive",
            department="finance",
            tools=["finance"],
            permissions=["read"],
            model="openai",
        )
    )

    mock_provider = MagicMock()
    mock_provider.complete.return_value = "ok"
    mock_get_provider.return_value = mock_provider

    runner = AgentRunner(memory_dir=str(tmp_path / "memory"))
    runner.run("cfo", "prepare budget")

    call_kwargs = mock_provider.complete.call_args
    system = call_kwargs.kwargs.get("system", call_kwargs[1].get("system", ""))
    assert "CFO" in system
    assert "finance" in system


@patch("lightspeed_agents.core.agent_runner.get_provider")
@patch("lightspeed_agents.core.agent_runner.load_agents")
def test_runner_records_to_episodic(mock_load, mock_get_provider, tmp_path):
    mock_load.return_value = registry
    registry.register(
        Agent(
            id="cto",
            name="CTO",
            role="Tech Executive",
            department="engineering",
            model="ollama",
        )
    )

    mock_provider = MagicMock()
    mock_provider.complete.return_value = "done"
    mock_get_provider.return_value = mock_provider

    runner = AgentRunner(memory_dir=str(tmp_path / "memory"))
    runner.run("cto", "review code")

    entries = runner.memory.get_entries("episodic")
    assert len(entries) == 1
    assert "review code" in entries[0].content
