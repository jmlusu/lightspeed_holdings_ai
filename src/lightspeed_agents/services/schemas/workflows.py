"""Pydantic response schemas for the Workflows API (D5-020)."""

from typing import Optional

from pydantic import BaseModel

from lightspeed_agents.workflow.models import Workflow, WorkflowStep


class WorkflowStepResponse(BaseModel):
    """API representation of a single workflow step."""

    id: str
    instruction: str = ""
    assignee: str = ""
    tier: str = "T0"
    depends_on: list[str] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_step(cls, step: WorkflowStep) -> "WorkflowStepResponse":
        return cls(
            id=step.id,
            instruction=step.instruction,
            assignee=step.assignee,
            tier=step.tier,
            depends_on=step.depends_on,
        )


class WorkflowResponse(BaseModel):
    """API representation of a workflow with metadata."""

    id: str
    name: str
    description: str = ""
    owner: str = ""
    version: str = "1.0"
    steps: list[WorkflowStepResponse] = []
    step_count: int = 0

    model_config = {"from_attributes": True}

    @classmethod
    def from_workflow(cls, workflow: Workflow) -> "WorkflowResponse":
        steps = [WorkflowStepResponse.from_step(s) for s in workflow.steps]
        return cls(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            owner=workflow.owner,
            version=workflow.version,
            steps=steps,
            step_count=len(workflow.steps),
        )


class WorkflowListResponse(BaseModel):
    """Paginated list of workflows."""

    workflows: list[WorkflowResponse] = []
    total: int = 0
