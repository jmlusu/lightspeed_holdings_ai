"""Tests for List Agents Endpoint (D5-033)."""

from datetime import datetime

from fastapi.testclient import TestClient

from lightspeed_agents.models.agent import Agent
from lightspeed_agents.services import create_app
from lightspeed_agents.services.dependencies import (
    get_agent_registry,
    reset_dependencies,
)


def _make_test_agents() -> list[Agent]:
    """Create a set of test agents spanning multiple departments."""
    return [
        Agent(
            id="human-ceo",
            name="Human CEO",
            role="CEO",
            department="executive",
            tools=["dashboard", "read", "search"],
            permissions=["read", "approve", "decide"],
            reports_to=None,
        ),
        Agent(
            id="cto",
            name="CTO",
            role="Chief Technology Officer",
            department="executive",
            tools=["dashboard", "read", "search", "edit"],
            permissions=["read", "edit", "decide"],
            reports_to="human-ceo",
        ),
        Agent(
            id="backend-engineer",
            name="Backend Engineer",
            role="Backend Developer",
            department="engineering",
            tools=["python", "git", "read", "search", "write", "edit"],
            permissions=["read", "edit"],
            reports_to="lead-engineer",
        ),
        Agent(
            id="frontend-engineer",
            name="Frontend Engineer",
            role="Frontend Developer",
            department="engineering",
            tools=["javascript", "git", "read", "search", "write", "edit"],
            permissions=["read", "edit"],
            reports_to="lead-engineer",
        ),
        Agent(
            id="qa-engineer",
            name="QA Engineer",
            role="Quality Engineer",
            department="engineering",
            tools=["python", "git", "read", "search", "write", "edit"],
            permissions=["read", "edit"],
            reports_to="lead-engineer",
        ),
        Agent(
            id="devops-engineer",
            name="DevOps Engineer",
            role="DevOps Specialist",
            department="operations",
            tools=["docker", "git", "shell", "read", "search", "write"],
            permissions=["read", "edit"],
            reports_to="coo",
        ),
    ]


class TestListAgents:
    """Test the GET /api/v1/agents/ endpoint."""

    def setup_method(self) -> None:
        reset_dependencies()
        self.app = create_app()
        self.client = TestClient(self.app)

        # Pre-populate the registry with test agents
        registry = get_agent_registry()
        for agent in _make_test_agents():
            registry.register(agent)

    def test_list_agents_returns_200(self) -> None:
        r = self.client.get("/api/v1/agents/")
        assert r.status_code == 200

    def test_list_agents_returns_all_agents(self) -> None:
        r = self.client.get("/api/v1/agents/")
        data = r.json()
        assert data["total"] == 6
        assert len(data["agents"]) == 6

    def test_agent_response_has_required_fields(self) -> None:
        r = self.client.get("/api/v1/agents/")
        data = r.json()
        agent = data["agents"][0]

        required_fields = {
            "id",
            "name",
            "role",
            "department",
            "tools",
            "permissions",
            "reports_to",
            "created_at",
        }
        assert required_fields.issubset(agent.keys())

    def test_agent_tools_is_list(self) -> None:
        r = self.client.get("/api/v1/agents/")
        data = r.json()
        for agent in data["agents"]:
            assert isinstance(agent["tools"], list)

    def test_agent_permissions_is_list(self) -> None:
        r = self.client.get("/api/v1/agents/")
        data = r.json()
        for agent in data["agents"]:
            assert isinstance(agent["permissions"], list)

    def test_agent_created_at_is_iso_string(self) -> None:
        r = self.client.get("/api/v1/agents/")
        data = r.json()
        for agent in data["agents"]:
            # Should parse without error
            datetime.fromisoformat(agent["created_at"])

    def test_agent_has_role_and_department(self) -> None:
        r = self.client.get("/api/v1/agents/")
        data = r.json()
        ceo = next(a for a in data["agents"] if a["id"] == "human-ceo")
        assert ceo["role"] == "CEO"
        assert ceo["department"] == "executive"

    def test_agent_has_reports_to(self) -> None:
        r = self.client.get("/api/v1/agents/")
        data = r.json()
        cto = next(a for a in data["agents"] if a["id"] == "cto")
        assert cto["reports_to"] == "human-ceo"

    def test_agent_reports_to_none_when_root(self) -> None:
        r = self.client.get("/api/v1/agents/")
        data = r.json()
        ceo = next(a for a in data["agents"] if a["id"] == "human-ceo")
        assert ceo["reports_to"] is None


class TestListAgentsDepartmentFilter:
    """Test the department query parameter filter."""

    def setup_method(self) -> None:
        reset_dependencies()
        self.app = create_app()
        self.client = TestClient(self.app)

        registry = get_agent_registry()
        for agent in _make_test_agents():
            registry.register(agent)

    def test_filter_by_engineering(self) -> None:
        r = self.client.get("/api/v1/agents/?department=engineering")
        data = r.json()
        assert data["total"] == 3
        for agent in data["agents"]:
            assert agent["department"] == "engineering"

    def test_filter_by_executive(self) -> None:
        r = self.client.get("/api/v1/agents/?department=executive")
        data = r.json()
        assert data["total"] == 2
        for agent in data["agents"]:
            assert agent["department"] == "executive"

    def test_filter_by_operations(self) -> None:
        r = self.client.get("/api/v1/agents/?department=operations")
        data = r.json()
        assert data["total"] == 1
        assert data["agents"][0]["id"] == "devops-engineer"

    def test_filter_nonexistent_department(self) -> None:
        r = self.client.get("/api/v1/agents/?department=marketing")
        data = r.json()
        assert data["total"] == 0
        assert data["agents"] == []

    def test_no_filter_returns_all(self) -> None:
        r = self.client.get("/api/v1/agents/")
        data = r.json()
        assert data["total"] == 6


class TestListAgentsEmpty:
    """Test behaviour when registry is empty."""

    def setup_method(self) -> None:
        reset_dependencies()
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_empty_registry_returns_empty_list(self) -> None:
        r = self.client.get("/api/v1/agents/")
        data = r.json()
        assert data["total"] == 0
        assert data["agents"] == []


class TestListAgentsSchema:
    """Test response model schema validation."""

    def setup_method(self) -> None:
        reset_dependencies()
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_response_matches_agent_list_response_model(self) -> None:
        from lightspeed_agents.services.schemas.agents import (
            AgentListResponse,
            AgentResponse,
        )

        registry = get_agent_registry()
        registry.register(
            Agent(id="test", name="Test Agent", role="Tester", department="qa")
        )

        r = self.client.get("/api/v1/agents/")
        data = r.json()

        # Validate via Pydantic model
        parsed = AgentListResponse(**data)
        assert parsed.total == 1
        assert isinstance(parsed.agents[0], AgentResponse)
