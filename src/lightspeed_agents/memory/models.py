import uuid
from datetime import datetime, UTC
from typing import Any

from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    content: str
    memory_type: str = "episodic"
    agent_id: str = ""
    task_id: str = ""
    department: str = ""
    tags: list[str] = []
    metadata: dict[str, Any] = {}
    access_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    def __init__(self, **data):
        now = datetime.now(UTC).isoformat()
        if not data.get("created_at"):
            data["created_at"] = now
        if not data.get("updated_at"):
            data["updated_at"] = now
        super().__init__(**data)

    def touch(self):
        self.access_count += 1
        self.updated_at = datetime.now(UTC).isoformat()

    def is_older_than_days(self, days: int) -> bool:
        created = datetime.fromisoformat(self.created_at)
        age = datetime.now(UTC) - created
        return age.days > days
