"""
Temporal decay module for memory consolidation.

Implements configurable decay functions for different memory types.
Episodic memories decay faster (short-term context), while semantic/procedural
memories persist longer. Decay reduces importance scores over time,
affecting consolidation pruning decisions.
"""

import math
from dataclasses import dataclass
from datetime import datetime, UTC
from enum import Enum
from typing import Any

from lightspeed_agents.memory.models import MemoryEntry


class DecayFunction(Enum):
    """Supported decay function types."""

    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    STEP = "step"


@dataclass(frozen=True)
class DecayConfig:
    """Configuration for temporal decay behavior."""

    function: DecayFunction = DecayFunction.EXPONENTIAL
    half_life_days: dict[str, float] = None  # per memory type
    min_importance: float = 0.01  # minimum importance floor
    no_decay_threshold: float = 1.01  # importance above which no decay applies (set > 1.0 to allow all to decay)
    initial_importance: float = 1.0  # starting importance for new memories

    def __post_init__(self):
        if self.half_life_days is None:
            object.__setattr__(self, "half_life_days", {
                "episodic": 7.0,      # 1 week half-life
                "semantic": 90.0,     # ~3 months half-life
                "procedural": 180.0,  # ~6 months half-life
                "relational": 60.0,   # ~2 months half-life
                "temporal": 30.0,     # ~1 month half-life
                "aggregate": 365.0,   # ~1 year half-life
            })


DEFAULT_DECAY_CONFIG = DecayConfig()


def calculate_age_days(entry: MemoryEntry) -> float:
    """Calculate the age of a memory entry in days."""
    created = datetime.fromisoformat(entry.created_at)
    age = datetime.now(UTC) - created
    return age.total_seconds() / 86400.0  # seconds per day


def get_half_life(memory_type: str, config: DecayConfig) -> float:
    """Get the half-life in days for a given memory type."""
    return config.half_life_days.get(memory_type, config.half_life_days.get("episodic", 7.0))


def calculate_decay_factor(
    entry: MemoryEntry,
    config: DecayConfig = DEFAULT_DECAY_CONFIG,
) -> float:
    """
    Calculate the decay factor for a memory entry based on its age and type.

    Returns a value between 0 and 1, where 1 means no decay and 0 means fully decayed.
    """
    # Check if importance is above no-decay threshold
    current_importance = entry.importance_score
    if current_importance >= config.no_decay_threshold:
        return 1.0

    age_days = calculate_age_days(entry)
    half_life = get_half_life(entry.memory_type, config)

    if half_life <= 0:
        return 1.0

    if config.function == DecayFunction.EXPONENTIAL:
        # Exponential decay: factor = 0.5^(age / half_life)
        factor = math.pow(0.5, age_days / half_life)
    elif config.function == DecayFunction.LINEAR:
        # Linear decay: factor = max(0, 1 - age / (2 * half_life))
        factor = max(0.0, 1.0 - (age_days / (2 * half_life)))
    elif config.function == DecayFunction.STEP:
        # Step decay: factor drops at half-life intervals
        steps = int(age_days / half_life)
        factor = math.pow(0.5, steps)
    else:
        factor = 1.0

    # Apply minimum importance floor
    return max(factor, config.min_importance / config.initial_importance)


def calculate_decayed_importance(
    entry: MemoryEntry,
    config: DecayConfig = DEFAULT_DECAY_CONFIG,
) -> float:
    """
    Calculate the current decayed importance score for a memory entry.

    The importance score decays over time based on the memory type's decay rate.
    High-importance memories (above threshold) are protected from decay.
    """
    current_importance = entry.importance_score

    # No decay for high-importance memories
    if current_importance >= config.no_decay_threshold:
        return current_importance

    decay_factor = calculate_decay_factor(entry, config)
    decayed_importance = current_importance * decay_factor

    # Ensure we don't go below minimum
    return max(decayed_importance, config.min_importance)


def apply_decay_to_entry(
    entry: MemoryEntry,
    config: DecayConfig = DEFAULT_DECAY_CONFIG,
) -> MemoryEntry:
    """
    Apply temporal decay to a memory entry, updating its importance score.

    Returns a new MemoryEntry with updated importance score in metadata.
    """
    decayed_importance = calculate_decayed_importance(entry, config)

    # Create updated metadata
    new_metadata = dict(entry.metadata)
    new_metadata["importance_score"] = decayed_importance
    new_metadata["decay_factor"] = calculate_decay_factor(entry, config)
    new_metadata["last_decay_applied"] = datetime.now(UTC).isoformat()

    # Create new entry with updated metadata
    updated = MemoryEntry(
        id=entry.id,
        content=entry.content,
        memory_type=entry.memory_type,
        agent_id=entry.agent_id,
        task_id=entry.task_id,
        department=entry.department,
        tags=entry.tags,
        metadata=new_metadata,
        access_count=entry.access_count,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )

    return updated


def apply_decay_to_entries(
    entries: list[MemoryEntry],
    config: DecayConfig = DEFAULT_DECAY_CONFIG,
) -> list[MemoryEntry]:
    """Apply temporal decay to a list of memory entries."""
    return [apply_decay_to_entry(entry, config) for entry in entries]


def should_prune_by_decay(
    entry: MemoryEntry,
    config: DecayConfig = DEFAULT_DECAY_CONFIG,
    prune_threshold: float = 0.05,
) -> bool:
    """
    Determine if a memory entry should be pruned based on its decayed importance.

    Returns True if the decayed importance falls below the prune threshold.
    """
    decayed_importance = calculate_decayed_importance(entry, config)
    return decayed_importance < prune_threshold


__all__ = [
    "DecayFunction",
    "DecayConfig",
    "DEFAULT_DECAY_CONFIG",
    "calculate_age_days",
    "get_half_life",
    "calculate_decay_factor",
    "calculate_decayed_importance",
    "apply_decay_to_entry",
    "apply_decay_to_entries",
    "should_prune_by_decay",
]