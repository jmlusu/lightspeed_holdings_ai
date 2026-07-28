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
    importance_score: float = 1.0
    created_at: str = ""
    updated_at: str = ""

    def __init__(self, **data):
        now = datetime.now(UTC).isoformat()
        if not data.get("created_at"):
            data["created_at"] = now
        if not data.get("updated_at"):
            data["updated_at"] = now
        # Initialize importance_score from metadata if present
        if "importance_score" not in data and data.get("metadata", {}).get("importance_score") is not None:
            data["importance_score"] = data["metadata"]["importance_score"]
        # Default importance to 1.0 if not set
        if "importance_score" not in data:
            data["importance_score"] = 1.0
        super().__init__(**data)

    def touch(self):
        self.access_count += 1
        self.updated_at = datetime.now(UTC).isoformat()

    def is_older_than_days(self, days: int) -> bool:
        created = datetime.fromisoformat(self.created_at)
        age = datetime.now(UTC) - created
        return age.days > days

    def get_importance(self) -> float:
        """Get the current importance score."""
        # Use the field value, which is synced with metadata
        return self.importance_score

    def set_importance(self, score: float):
        """Set the importance score, clamped to [0, 1]."""
        self.importance_score = max(0.0, min(1.0, score))
        self.metadata["importance_score"] = self.importance_score
