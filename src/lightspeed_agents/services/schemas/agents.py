"""Pydantic models for Agent API responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AgentResponse(BaseModel):
    """Single agent representation returned by the API."""

    id: str
    name: str
    role: str
    department: str
    tools: list[str]
    permissions: list[str]
    reports_to: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentListResponse(BaseModel):
    """Paginated list of agents."""

    agents: list[AgentResponse]
    total: int
