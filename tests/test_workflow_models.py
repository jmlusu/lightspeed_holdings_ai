import pytest

from lightspeed_agents.workflow.models import (
    Workflow,
    WorkflowRun,
    WorkflowStep,
    WorkflowStatus,
    WorkflowStepStatus,
)


def test_step_defaults():
    step = WorkflowStep(id="test-step")
    assert step.id == "test-step"
    assert step.status == WorkflowStepStatus.PENDING
    assert step.tier == "T0"
    assert step.requires_approval is False


def test_step_requires_approval():
    step = WorkflowStep(id="test", tier="T2")
    assert step.requires_approval is True
    step.tier = "T3"
    assert step.requires_approval is True
    step.tier = "T0"
    assert step.requires_approval is False


def test_step_with_dependencies():
    step = WorkflowStep(id="test", depends_on=["step-a", "step-b"])
    assert step.depends_on == ["step-a", "step-b"]


def test_workflow_defaults():
    wf = Workflow(id="test-wf", name="Test Workflow")
    assert wf.id == "test-wf"
    assert wf.name == "Test Workflow"
    assert wf.steps == []


def test_workflow_with_steps():
    steps = [
        WorkflowStep(id="s1", instruction="do first"),
        WorkflowStep(id="s2", instruction="do second", depends_on=["s1"]),
    ]
    wf = Workflow(id="wf-1", name="Test", steps=steps)
    assert len(wf.steps) == 2
    assert wf.steps[1].depends_on == ["s1"]


def test_run_defaults():
    run = WorkflowRun(workflow_id="wf-1")
    assert run.id != ""
    assert run.workflow_id == "wf-1"
    assert run.status == WorkflowStatus.CREATED
    assert run.current_step_index == 0
    assert run.created_at != ""


def test_run_touch():
    run = WorkflowRun(workflow_id="wf-1")
    old = run.updated_at
    run.touch()
    assert run.updated_at >= old


def test_run_unique_ids():
    r1 = WorkflowRun(workflow_id="wf-1")
    r2 = WorkflowRun(workflow_id="wf-1")
    assert r1.id != r2.id


def test_run_serialization():
    run = WorkflowRun(workflow_id="wf-1")
    data = run.model_dump(mode="json")
    restored = WorkflowRun(**data)
    assert restored.id == run.id
    assert restored.workflow_id == "wf-1"
