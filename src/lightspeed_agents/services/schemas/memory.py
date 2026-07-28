"""Pydantic schemas for the Memory API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MemoryEntryResponse(BaseModel):
    """Schema for a single memory entry in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    content: str
    memory_type: str
    tags: list[str] = []
    agent_id: str = ""
    relevance_score: float | None = None
    created_at: datetime


class MemorySearchResponse(BaseModel):
    """Schema for memory search results."""

    query: str
    results: list[MemoryEntryResponse] = []
    total: int = 0
    search_time_ms: float = 0.0


class MemoryStatsResponse(BaseModel):
    """Schema for memory statistics."""

    total_entries: int
    by_type: dict[str, int] = Field(default_factory=dict)
    recent_additions: int = 0
