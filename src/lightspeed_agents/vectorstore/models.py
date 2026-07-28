"""Data models for the VectorStore interface."""

from datetime import datetime, UTC
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


class VectorRecord(BaseModel):
    """A single vector record stored in the vector store."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    embedding: list[float]
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    model_config = ConfigDict(validate_assignment=True)


class SearchResult(BaseModel):
    """A single search result with score and rank."""

    record: VectorRecord
    score: float
    rank: int

    model_config = ConfigDict(validate_assignment=True)


class VectorStoreConfig(BaseModel):
    """Base configuration for vector store providers."""

    persist_dir: str | None = None
    index_type: str = "flat"

    model_config = ConfigDict(use_enum_values=True)
