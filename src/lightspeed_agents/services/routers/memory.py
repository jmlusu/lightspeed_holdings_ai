"""Memory search API endpoint (D5-027)."""

import time

from fastapi import APIRouter, Depends, Query

from lightspeed_agents.memory.engine import MemoryEngine, MEMORY_TYPES
from lightspeed_agents.memory.models import MemoryEntry
from lightspeed_agents.services.dependencies import get_memory_engine
from lightspeed_agents.services.schemas.memory import (
    MemoryEntryResponse,
    MemorySearchResponse,
)

router = APIRouter(prefix="/memory", tags=["memory"])


def _entry_to_response(
    entry: MemoryEntry, rank: int, total: int
) -> MemoryEntryResponse:
    """Convert a MemoryEntry to an API response with a rank-based relevance score."""
    relevance = round(1.0 - (rank / max(total, 1)), 3) if total > 0 else None
    return MemoryEntryResponse(
        id=entry.id,
        content=entry.content,
        memory_type=entry.memory_type,
        tags=entry.tags,
        agent_id=entry.agent_id,
        relevance_score=relevance,
        created_at=entry.created_at,
    )


@router.get("/search", response_model=MemorySearchResponse)
async def search_memory(
    q: str = Query(..., min_length=1, description="Search query"),
    type: str | None = Query(  # noqa: A002 — matches API spec query param name
        None,
        description="Filter by memory type (episodic, semantic, procedural, relational, temporal, aggregate)",
    ),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of results to return"
    ),
    engine: MemoryEngine = Depends(get_memory_engine),  # noqa: B008
) -> MemorySearchResponse:
    """Search memory entries by query string.

    Returns ranked results ordered by relevance. Optionally filter by memory type.
    """
    start = time.perf_counter()

    # Build type filter list
    memory_types: list[str] | None = None
    if type is not None:
        if type not in MEMORY_TYPES:
            # Return empty for invalid type rather than erroring — graceful degradation
            return MemorySearchResponse(
                query=q,
                results=[],
                total=0,
                search_time_ms=0.0,
            )
        memory_types = [type]

    results: list[MemoryEntry] = engine.search(
        query=q,
        memory_types=memory_types,
        limit=limit,
    )

    elapsed_ms = (time.perf_counter() - start) * 1000

    response_results = [
        _entry_to_response(entry, rank, len(results))
        for rank, entry in enumerate(results)
    ]

    return MemorySearchResponse(
        query=q,
        results=response_results,
        total=len(response_results),
        search_time_ms=round(elapsed_ms, 2),
    )
