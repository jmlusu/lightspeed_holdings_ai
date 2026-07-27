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

    model_config = {"populate_by_name": True}
