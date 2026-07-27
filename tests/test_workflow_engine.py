import pytest
import yaml

from lightspeed_agents.workflow.engine import WorkflowEngine
from lightspeed_agents.workflow.models import WorkflowStatus, WorkflowStepStatus
from lightspeed_agents.message_bus.message_bus import MessageBus
from lightspeed_agents.memory.engine import MemoryEngine
from lightspeed_agents.message_bus.task_status import TaskStatus


@pytest.fixture
def engine(tmp_path):
    bus = MessageBus(str(tmp_path / "bus"))
    memory = MemoryEngine(str(tmp_path / "memory"))
    return WorkflowEngine(bus=bus, memory=memory, bus_dir=str(tmp_path / "bus"))


@pytest.fixture
def workflows_file(tmp_path):
    data = {
        "workflows": [
            {
                "id": "simple-wf",
                "name": "Simple Workflow",
                "description": "Test workflow",
                "owner": "cto",
                "steps": [
                    {
                        "id": "s1",
                        "instruction": "Step 1",
                        "assignee": "cto",
                        "tier": "T0",
                    },
                    {
                        "id": "s2",
                        "instruction": "Step 2",
                        "assignee": "cfo",
                        "depends_on": ["s1"],
                        "tier": "T1",
                    },
                ],
            },
            {
                "id": "approval-wf",
                "name": "Approval Workflow",
                "description": "Needs approval",
                "owner": "cto",
                "steps": [
                    {
                        "id": "s1",
                        "instruction": "Step 1",
                        "assignee": "cto",
                        "tier": "T2",
                    },
                ],
            },
        ]
    }
    path = tmp_path / "workflows.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f)
    return str(path)


def test_list_workflows(engine, workflows_file):
    engine.workflows_path = workflows_file
    wfs = engine.list_workflows()
    assert len(wfs) == 2


def test_get_workflow(engine, workflows_file):
    engine.workflows_path = workflows_file
    wf = engine.get_workflow("simple-wf")
    assert wf is not None
    assert wf.name == "Simple Workflow"


def test_start_workflow(engine, workflows_file):
    engine.workflows_path = workflows_file
    run = engine.start_workflow("simple-wf")
    assert run.status == WorkflowStatus.RUNNING
    assert run.started_at != ""


def test_start_workflow_creates_bus_tasks(engine, workflows_file):
    engine.workflows_path = workflows_file
    run = engine.start_workflow("simple-wf")

    tasks = engine.bus.get_all_tasks()
    assert len(tasks) >= 1
    assert tasks[0].receiver_id == "cto"


def test_start_workflow_advances_past_completed(engine, workflows_file):
    engine.workflows_path = workflows_file
    run = engine.start_workflow("simple-wf")

    s1_task_id = run.step_results["s1"]["task_id"]
    engine.bus.complete_task(s1_task_id, result="done")

    run = engine.complete_step(run.id, "s1", result="done")
    assert run.step_results["s1"]["status"] == "completed"

    tasks = engine.bus.get_all_tasks()
    s2_tasks = [t for t in tasks if "s2" in str(engine.bus.get_task(t.id))]
    assert len(tasks) >= 2


def test_complete_step(engine, workflows_file):
    engine.workflows_path = workflows_file
    run = engine.start_workflow("simple-wf")

    run = engine.complete_step(run.id, "s1", result="finished")
    assert run.step_results["s1"]["status"] == "completed"
    assert run.step_results["s1"]["result"] == "finished"


def test_complete_step_not_found(engine, workflows_file):
    engine.workflows_path = workflows_file
    run = engine.start_workflow("simple-wf")

    with pytest.raises(ValueError, match="not found"):
        engine.complete_step(run.id, "nonexistent")


def test_fail_step(engine, workflows_file):
    engine.workflows_path = workflows_file
    run = engine.start_workflow("simple-wf")

    run = engine.fail_step(run.id, "s1", error="timeout")
    assert run.status == WorkflowStatus.FAILED
    assert run.step_results["s1"]["status"] == "failed"


def test_approval_step(engine, workflows_file):
    engine.workflows_path = workflows_file
    run = engine.start_workflow("approval-wf")

    assert run.step_results["s1"]["status"] == "waiting_approval"

    run = engine.approve_step(run.id, "s1")
    assert run.step_results["s1"]["status"] == "in_progress"


def test_workflow_completes(engine, workflows_file):
    engine.workflows_path = workflows_file
    run = engine.start_workflow("simple-wf")

    run = engine.complete_step(run.id, "s1", result="done")
    run = engine.complete_step(run.id, "s2", result="done")

    assert run.status == WorkflowStatus.COMPLETED
    assert run.completed_at != ""


def test_cancel_workflow(engine, workflows_file):
    engine.workflows_path = workflows_file
    run = engine.start_workflow("simple-wf")

    run = engine.cancel_workflow(run.id)
    assert run.status == WorkflowStatus.CANCELLED


def test_get_run(engine, workflows_file):
    engine.workflows_path = workflows_file
    run = engine.start_workflow("simple-wf")

    found = engine.get_run(run.id)
    assert found is not None
    assert found.id == run.id


def test_get_runs_by_workflow(engine, workflows_file):
    engine.workflows_path = workflows_file
    engine.start_workflow("simple-wf")
    engine.start_workflow("simple-wf")

    runs = engine.get_runs_by_workflow("simple-wf")
    assert len(runs) == 2


def test_memory_records(engine, workflows_file):
    engine.workflows_path = workflows_file
    run = engine.start_workflow("simple-wf")

    entries = engine.memory.get_entries("episodic")
    assert len(entries) > 0


def test_dependencies_block(engine, tmp_path):
    data = {
        "workflows": [
            {
                "id": "dep-wf",
                "name": "Dependent",
                "owner": "cto",
                "steps": [
                    {
                        "id": "s1",
                        "instruction": "First",
                        "assignee": "cto",
                        "tier": "T0",
                    },
                    {
                        "id": "s2",
                        "instruction": "Second",
                        "assignee": "cfo",
                        "depends_on": ["s1"],
                        "tier": "T0",
                    },
                    {
                        "id": "s3",
                        "instruction": "Third",
                        "assignee": "coo",
                        "depends_on": ["s2"],
                        "tier": "T0",
                    },
                ],
            }
        ]
    }
    path = tmp_path / "workflows.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f)
    engine.workflows_path = str(path)

    run = engine.start_workflow("dep-wf")

    tasks = engine.bus.get_all_tasks()
    assert len(tasks) == 1
    assert tasks[0].receiver_id == "cto"

    run = engine.complete_step(run.id, "s1", result="done")
    tasks = engine.bus.get_all_tasks()
    assert len(tasks) == 2
