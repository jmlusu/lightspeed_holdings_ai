from datetime import UTC, datetime
from typing import Optional

from pydantic import BaseModel, Field


class Agent(BaseModel):
    id: str
    name: str
    role: str
    description: str = ""
    type: str = "Specialist"
    department: str = "general"
    reports_to: Optional[str] = Field(None, alias="reportsTo")
    tools: list[str] = []
    permissions: list[str] = []
    model: str = "ollama"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {"populate_by_name": True}
