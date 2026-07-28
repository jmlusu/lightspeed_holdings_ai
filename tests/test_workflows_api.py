"""Tests for List Workflows Endpoint (D5-020)."""

import pytest
import yaml
from fastapi.testclient import TestClient

from lightspeed_agents.services import create_app
from lightspeed_agents.services.dependencies import reset_dependencies
from lightspeed_agents.workflow.engine import WorkflowEngine
from lightspeed_agents.message_bus.message_bus import MessageBus
from lightspeed_agents.memory.engine import MemoryEngine


def _make_workflows_file(tmp_path, workflows_data):
    """Write a workflows YAML file and return its path."""
    path = tmp_path / "workflows.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump({"workflows": workflows_data}, f)
    return str(path)


def _patch_engine(tmp_path, workflows_data):
    """Reset DI, create app, and override the workflow engine with test data."""
    reset_dependencies()
    path = _make_workflows_file(tmp_path, workflows_data)

    bus = MessageBus(str(tmp_path / "bus"))
    memory = MemoryEngine(str(tmp_path / "memory"))
    engine = WorkflowEngine(bus=bus, memory=memory, workflows_path=path)

    app = create_app()

    # Override the DI provider so the router gets our test engine
    from lightspeed_agents.services import dependencies

    def _override():
        return engine

    app.dependency_overrides[dependencies.get_workflow_engine] = _override
    return app, engine


class TestListWorkflowsEmpty:
    """GET /api/v1/workflows/ when no workflows are defined."""

    def setup_method(self):
        self.app, _ = _patch_engine(
            pytest.importorspec("pathlib").Path("/tmp/test_empty"),
            [],
        )
        self.client = TestClient(self.app)

    def test_returns_200(self):
        r = self.client.get("/api/v1/workflows/")
        assert r.status_code == 200

    def test_empty_list(self):
        r = self.client.get("/api/v1/workflows/")
        data = r.json()
        assert data["workflows"] == []
        assert data["total"] == 0


class TestListWorkflowsWithData:
    """GET /api/v1/workflows/ when workflows are defined."""

    SAMPLE = [
        {
            "id": "deploy-prod",
            "name": "Deploy to Production",
            "description": "Full production deployment pipeline",
            "owner": "cto",
            "steps": [
                {
                    "id": "s1",
                    "instruction": "Run unit tests",
                    "assignee": "qa-engineer",
                    "tier": "T0",
                },
                {
                    "id": "s2",
                    "instruction": "Deploy to staging",
                    "assignee": "devops-engineer",
                    "tier": "T2",
                    "depends_on": ["s1"],
                },
                {
                    "id": "s3",
                    "instruction": "Deploy to production",
                    "assignee": "devops-engineer",
                    "tier": "T3",
                    "depends_on": ["s2"],
                },
            ],
        },
        {
            "id": "onboard-agent",
            "name": "Onboard Agent",
            "description": "Register a new agent",
            "owner": "coo",
            "steps": [
                {
                    "id": "s1",
                    "instruction": "Create agent config",
                    "assignee": "cto",
                    "tier": "T0",
                },
            ],
        },
    ]

    def setup_method(self):
        import pathlib

        self.app, _ = _patch_engine(pathlib.Path("/tmp/test_data"), self.SAMPLE)
        self.client = TestClient(self.app)

    def test_returns_200(self):
        r = self.client.get("/api/v1/workflows/")
        assert r.status_code == 200

    def test_returns_two_workflows(self):
        r = self.client.get("/api/v1/workflows/")
        data = r.json()
        assert data["total"] == 2
        assert len(data["workflows"]) == 2

    def test_workflow_ids_present(self):
        r = self.client.get("/api/v1/workflows/")
        ids = {wf["id"] for wf in r.json()["workflows"]}
        assert ids == {"deploy-prod", "onboard-agent"}

    def test_step_count_deploy_prod(self):
        r = self.client.get("/api/v1/workflows/")
        deploy = next(
            wf for wf in r.json()["workflows"] if wf["id"] == "deploy-prod"
        )
        assert deploy["step_count"] == 3

    def test_step_count_onboard_agent(self):
        r = self.client.get("/api/v1/workflows/")
        onboard = next(
            wf for wf in r.json()["workflows"] if wf["id"] == "onboard-agent"
        )
        assert onboard["step_count"] == 1

    def test_steps_included_in_response(self):
        r = self.client.get("/api/v1/workflows/")
        deploy = next(
            wf for wf in r.json()["workflows"] if wf["id"] == "deploy-prod"
        )
        assert len(deploy["steps"]) == 3
        step_ids = [s["id"] for s in deploy["steps"]]
        assert step_ids == ["s1", "s2", "s3"]

    def test_step_has_assignee(self):
        r = self.client.get("/api/v1/workflows/")
        deploy = next(
            wf for wf in r.json()["workflows"] if wf["id"] == "deploy-prod"
        )
        s1 = deploy["steps"][0]
        assert s1["assignee"] == "qa-engineer"

    def test_step_has_depends_on(self):
        r = self.client.get("/api/v1/workflows/")
        deploy = next(
            wf for wf in r.json()["workflows"] if wf["id"] == "deploy-prod"
        )
        s2 = deploy["steps"][1]
        assert s2["depends_on"] == ["s1"]

    def test_step_has_tier(self):
        r = self.client.get("/api/v1/workflows/")
        deploy = next(
            wf for wf in r.json()["workflows"] if wf["id"] == "deploy-prod"
        )
        s3 = deploy["steps"][2]
        assert s3["tier"] == "T3"

    def test_workflow_owner(self):
        r = self.client.get("/api/v1/workflows/")
        onboard = next(
            wf for wf in r.json()["workflows"] if wf["id"] == "onboard-agent"
        )
        assert onboard["owner"] == "coo"

    def test_workflow_description(self):
        r = self.client.get("/api/v1/workflows/")
        deploy = next(
            wf for wf in r.json()["workflows"] if wf["id"] == "deploy-prod"
        )
        assert deploy["description"] == "Full production deployment pipeline"


class TestResponseSchema:
    """Validate the response structure matches the schema contract."""

    def setup_method(self):
        import pathlib

        self.app, _ = _patch_engine(
            pathlib.Path("/tmp/test_schema"),
            [
                {
                    "id": "wf-1",
                    "name": "WF One",
                    "owner": "cto",
                    "steps": [
                        {"id": "s1", "instruction": "Do thing", "tier": "T0"}
                    ],
                }
            ],
        )
        self.client = TestClient(self.app)

    def test_top_level_keys(self):
        r = self.client.get("/api/v1/workflows/")
        data = r.json()
        assert "workflows" in data
        assert "total" in data

    def test_workflow_keys(self):
        r = self.client.get("/api/v1/workflows/")
        wf = r.json()["workflows"][0]
        expected_keys = {
            "id",
            "name",
            "description",
            "owner",
            "version",
            "steps",
            "step_count",
        }
        assert expected_keys == set(wf.keys())

    def test_step_keys(self):
        r = self.client.get("/api/v1/workflows/")
        step = r.json()["workflows"][0]["steps"][0]
        expected_keys = {
            "id",
            "instruction",
            "assignee",
            "tier",
            "depends_on",
        }
        assert expected_keys == set(step.keys())
