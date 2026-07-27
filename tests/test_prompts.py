import pytest

from lightspeed_agents.models.agent import Agent
from lightspeed_agents.prompts.builder import PromptBuilder


@pytest.fixture
def builder():
    return PromptBuilder("company")


def test_build_includes_identity(builder):
    agent = Agent(id="cto", name="CTO", role="Tech Executive", type="Executive")
    prompt = builder.build(agent)
    assert "CTO" in prompt
    assert "Tech Executive" in prompt
    assert "LightSpeed Holdings" in prompt


def test_build_includes_department(builder):
    agent = Agent(id="cto", name="CTO", role="Tech Executive", department="engineering")
    prompt = builder.build(agent)
    assert "engineering" in prompt


def test_build_includes_tools(builder):
    agent = Agent(id="cto", name="CTO", role="Tech", tools=["python", "git"])
    prompt = builder.build(agent)
    assert "python" in prompt
    assert "git" in prompt


def test_build_includes_kpis(builder):
    agent = Agent(id="cto", name="CTO", role="Tech", department="engineering")
    prompt = builder.build(agent)
    assert "Deployment Frequency" in prompt
    assert "Cycle Time" in prompt


def test_build_includes_workflows(builder):
    agent = Agent(id="cto", name="CTO", role="Tech", department="engineering")
    prompt = builder.build(agent)
    assert "Software Development Workflow" in prompt
    assert "Incident Response Workflow" in prompt


def test_build_includes_reports_to(builder):
    agent = Agent(id="cto", name="CTO", role="Tech", reports_to="human-ceo")
    prompt = builder.build(agent)
    assert "human-ceo" in prompt


def test_build_top_level(builder):
    agent = Agent(id="ceo", name="CEO", role="Chief Executive")
    prompt = builder.build(agent)
    assert "top of the organization" in prompt


def test_build_guidelines(builder):
    agent = Agent(id="x", name="X", role="Y")
    prompt = builder.build(agent)
    assert "Guidelines" in prompt
    assert "concise" in prompt


def test_build_no_agent_kpis(builder):
    agent = Agent(id="unknown", name="Unknown", role="Role", department="nonexistent")
    prompt = builder.build(agent)
    assert "Department KPIs" not in prompt


def test_build_no_workflows(builder):
    agent = Agent(id="unknown", name="Unknown", role="Role")
    prompt = builder.build(agent)
    assert "Owned Workflows" not in prompt


def test_build_empty_config(tmp_path):
    builder = PromptBuilder(str(tmp_path))
    agent = Agent(id="x", name="X", role="Y")
    prompt = builder.build(agent)
    assert "X" in prompt
    assert "Guidelines" in prompt
