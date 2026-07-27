from lightspeed_agents.models.agent import Agent


def test_agent_minimal():
    agent = Agent(id="test", name="Test Agent", role="Tester")
    assert agent.id == "test"
    assert agent.name == "Test Agent"
    assert agent.role == "Tester"
    assert agent.description == ""
    assert agent.type == "Specialist"
    assert agent.department == "general"
    assert agent.reports_to is None
    assert agent.tools == []
    assert agent.permissions == []
    assert agent.model == "ollama"


def test_agent_full():
    agent = Agent(
        id="cto",
        name="Chief Technology Officer",
        role="Technology Executive",
        description="Oversees tech",
        type="Executive",
        department="engineering",
        reportsTo="human-ceo",
        tools=["python", "git"],
        permissions=["read", "edit"],
        model="openai",
    )
    assert agent.id == "cto"
    assert agent.reports_to == "human-ceo"
    assert agent.tools == ["python", "git"]
    assert agent.model == "openai"


def test_agent_from_json_dict():
    data = {
        "id": "cfo",
        "name": "Chief Financial Officer",
        "role": "Finance Executive",
        "type": "Executive",
        "department": "finance",
        "reportsTo": "human-ceo",
        "tools": ["finance"],
        "permissions": ["read"],
    }
    agent = Agent(**data)
    assert agent.id == "cfo"
    assert agent.reports_to == "human-ceo"
    assert agent.department == "finance"
