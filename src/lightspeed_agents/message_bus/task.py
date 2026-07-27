import re
import uuid
from datetime import datetime, UTC
from typing import Any

from pydantic import BaseModel, Field, field_validator

from lightspeed_agents.message_bus.task_status import TaskStatus, TaskPriority

KEBAB_CASE_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Task(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    assignee: str = ""
    sender_id: str = ""
    receiver_id: str = ""
    instruction: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_task_id: str = ""
    result: str = ""
    error: str = ""
    retry_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    claimed_at: str = ""
    completed_at: str = ""
    tags: list[str] = []
    metadata: dict[str, Any] = {}

    def __init__(self, **data):
        now = datetime.now(UTC).isoformat()
        if not data.get("created_at"):
            data["created_at"] = now
        if not data.get("updated_at"):
            data["updated_at"] = now
        super().__init__(**data)

    @field_validator("receiver_id")
    @classmethod
    def validate_receiver_kebab(cls, v):
        if v and not KEBAB_CASE_RE.match(v):
            raise ValueError(f"receiver_id must be kebab-case, got '{v}'")
        return v

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.DELETED,
        }

    def touch(self):
        self.updated_at = datetime.now(UTC).isoformat()
