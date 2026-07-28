import enum
import uuid
from datetime import datetime, UTC
from typing import Optional

from pydantic import BaseModel, Field

from lightspeed_agents.workflow.retry import RetryPolicy


class WorkflowStepStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(str, enum.Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TIER_APPROVAL_REQUIRED = {"T2", "T3", "T4"}


class WorkflowStep(BaseModel):
    id: str
    instruction: str = ""
    assignee: str = ""
    tier: str = "T0"
    depends_on: list[str] = []
    tags: list[str] = []
    compensating_action: str = ""
    retry_policy: Optional[RetryPolicy] = None
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    task_id: str = ""
    result: str = ""
    error: str = ""

    @property
    def requires_approval(self) -> bool:
        return self.tier in TIER_APPROVAL_REQUIRED


class Workflow(BaseModel):
    id: str
    name: str = ""
    description: str = ""
    owner: str = ""
    version: str = "1.0"
    steps: list[WorkflowStep] = []


class WorkflowRun(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.CREATED
    current_step_index: int = 0
    step_results: dict[str, dict] = {}
    created_at: str = ""
    updated_at: str = ""
    started_at: str = ""
    completed_at: str = ""

    def __init__(self, **data):
        now = datetime.now(UTC).isoformat()
        if not data.get("created_at"):
            data["created_at"] = now
        if not data.get("updated_at"):
            data["updated_at"] = now
        super().__init__(**data)

    def touch(self):
        self.updated_at = datetime.now(UTC).isoformat()
