import pytest
import os
import yaml

from lightspeed_agents.workflow.loader import load_workflows, get_workflow


@pytest.fixture
def sample_yaml(tmp_path):
    data = {
        "workflows": [
            {
                "id": "test-wf",
                "name": "Test Workflow",
                "description": "A test",
                "owner": "cto",
                "steps": [
                    {
                        "id": "step-1",
                        "instruction": "Do first",
                        "assignee": "cto",
                        "tier": "T0",
                    },
                    {
                        "id": "step-2",
                        "instruction": "Do second",
                        "assignee": "cfo",
                        "depends_on": ["step-1"],
                        "tier": "T2",
                    },
                ],
            }
        ]
    }
    path = tmp_path / "workflows.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f)
    return str(path)


def test_load_workflows(sample_yaml):
    workflows = load_workflows(sample_yaml)
    assert len(workflows) == 1
    assert workflows[0].id == "test-wf"
    assert len(workflows[0].steps) == 2


def test_load_workflows_missing():
    assert load_workflows("/nonexistent/path.yaml") == []


def test_get_workflow(sample_yaml):
    wf = get_workflow("test-wf", sample_yaml)
    assert wf is not None
    assert wf.name == "Test Workflow"


def test_get_workflow_not_found(sample_yaml):
    assert get_workflow("nonexistent", sample_yaml) is None


def test_load_workflows_string_steps(tmp_path):
    data = {
        "workflows": [
            {
                "id": "simple",
                "name": "Simple",
                "steps": ["step-a", "step-b"],
            }
        ]
    }
    path = tmp_path / "workflows.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f)

    workflows = load_workflows(str(path))
    assert len(workflows) == 1
    assert len(workflows[0].steps) == 2
    assert workflows[0].steps[0].id == "step-a"


def test_load_default_workflows():
    from lightspeed_agents.workflow.loader import DEFAULT_WORKFLOWS_PATH

    if os.path.exists(os.path.abspath(DEFAULT_WORKFLOWS_PATH)):
        workflows = load_workflows()
        assert len(workflows) == 4
        ids = [wf.id for wf in workflows]
        assert "daily-executive-briefing" in ids
        assert "software-development" in ids
