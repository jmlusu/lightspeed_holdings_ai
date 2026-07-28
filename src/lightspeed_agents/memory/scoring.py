"""
Importance scoring for memory entries.

Implements configurable importance scoring based on:
1. Access frequency - how often the memory is accessed
2. Recency - how recently the memory was created/updated
3. Agent priority - priority based on agent/department
4. Task criticality - criticality based on task status
5. Cross-references - number of cross-references/tags

Scores are normalized to [0, 1] range and used for consolidation retention decisions.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

from lightspeed_agents.memory.models import MemoryEntry


@dataclass
class ImportanceScoringConfig:
    """Configuration for importance scoring weights."""

    access_frequency_weight: float = 0.30
    recency_weight: float = 0.25
    agent_priority_weight: float = 0.20
    task_criticality_weight: float = 0.15
    cross_reference_weight: float = 0.10

    # Score normalization range
    score_min: float = 0.0
    score_max: float = 1.0

    # Agent priority weights (department -> priority weight)
    agent_priority_weights: dict[str, float] = field(default_factory=lambda: {
        "engineering": 1.0,
        "executive": 1.0,
        "security": 1.0,
        "operations": 0.8,
        "data": 0.8,
        "product": 0.7,
        "marketing": 0.6,
        "sales": 0.6,
        "hr": 0.5,
        "finance": 0.5,
        "default": 0.5,
    })

    # Task criticality weights (status -> criticality weight)
    task_criticality_weights: dict[str, float] = field(default_factory=lambda: {
        "blocked": 1.0,
        "in_progress": 0.9,
        "completed": 0.7,
        "pending": 0.5,
        "cancelled": 0.2,
        "default": 0.5,
    })

    # Time decay constants
    recency_half_life_days: float = 7.0
    access_frequency_cap: int = 100  # cap for access count normalization
    cross_reference_cap: int = 50    # cap for cross-reference count normalization


DEFAULT_SCORING_CONFIG = ImportanceScoringConfig()
DEFAULT_IMPORTANCE_SCORING_CONFIG = DEFAULT_SCORING_CONFIG  # Alias for backward compatibility


class ImportanceScorer:
    """Calculates importance scores for memory entries."""

    def __init__(self, config: ImportanceScoringConfig = None):
        self.config = config or DEFAULT_SCORING_CONFIG

    def calculate_score(self, entry: MemoryEntry) -> float:
        """
        Calculate importance score for a memory entry.

        Score factors:
        1. Access frequency (0-1): normalized access_count
        2. Recency (0-1): exponential decay based on age
        3. Agent priority (0-1): department/agent priority weight
        4. Task criticality (0-1): task status criticality weight
        5. Cross-references (0-1): number of cross-references/tags

        Returns score in range [score_min, score_max]
        """
        factors = {
            "access_frequency": self._score_access_frequency(entry),
            "recency": self._score_recency(entry),
            "agent_priority": self._score_agent_priority(entry),
            "task_criticality": self._score_task_criticality(entry),
            "cross_references": self._score_cross_references(entry),
        }

        weights = {
            "access_frequency": self.config.access_frequency_weight,
            "recency": self.config.recency_weight,
            "agent_priority": self.config.agent_priority_weight,
            "task_criticality": self.config.task_criticality_weight,
            "cross_references": self.config.cross_reference_weight,
        }

        # Weighted sum
        weighted_sum = sum(factors[k] * weights[k] for k in factors)
        total_weight = sum(weights.values())

        if total_weight == 0:
            return self.config.score_min

        normalized_score = weighted_sum / total_weight

        # Clamp to range
        return max(self.config.score_min, min(self.config.score_max, normalized_score))

    def _score_access_frequency(self, entry: MemoryEntry) -> float:
        """Score based on access frequency (0-1)."""
        capped_count = min(entry.access_count, self.config.access_frequency_cap)
        return capped_count / self.config.access_frequency_cap

    def _score_recency(self, entry: MemoryEntry) -> float:
        """Score based on recency using exponential decay (0-1)."""
        try:
            created = datetime.fromisoformat(entry.created_at.replace('Z', '+00:00'))
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
        except Exception:
            return 0.5  # default if parse fails

        now = datetime.now(UTC)
        age_days = (now - created).total_seconds() / 86400

        # Exponential decay with half-life
        half_life = self.config.recency_half_life_days
        if half_life <= 0:
            return 0.5

        return 2 ** (-age_days / half_life)

    def _score_agent_priority(self, entry: MemoryEntry) -> float:
        """Score based on agent/department priority (0-1)."""
        dept = entry.department.lower() if entry.department else ""
        agent = entry.agent_id.lower() if entry.agent_id else ""

        # Check department priority
        if dept in self.config.agent_priority_weights:
            return self.config.agent_priority_weights[dept]

        # Check agent priority (check if agent_id contains department name)
        for dept_key, weight in self.config.agent_priority_weights.items():
            if dept_key in agent:
                return weight

        return self.config.agent_priority_weights.get("default", 0.5)

    def _score_task_criticality(self, entry: MemoryEntry) -> float:
        """Score based on task criticality (0-1)."""
        metadata = entry.metadata or {}
        status = metadata.get("status", "").lower()

        if status in self.config.task_criticality_weights:
            return self.config.task_criticality_weights[status]

        # Check tags for task status indicators
        for tag in entry.tags:
            tag_lower = tag.lower()
            if tag_lower in self.config.task_criticality_weights:
                return self.config.task_criticality_weights[tag_lower]

        return self.config.task_criticality_weights.get("default", 0.5)

    def _score_cross_references(self, entry: MemoryEntry) -> float:
        """Score based on cross-references (tags, metadata refs) (0-1)."""
        metadata = entry.metadata or {}
        cross_refs = metadata.get("cross_references", [])
        if isinstance(cross_refs, list):
            ref_count = len(cross_refs)
        else:
            ref_count = 0

        # Also consider tags as implicit references
        tag_count = len(entry.tags)

        total_refs = ref_count + tag_count
        capped = min(total_refs, self.config.cross_reference_cap)
        return capped / self.config.cross_reference_cap

    def get_factor_breakdown(self, entry: MemoryEntry) -> dict[str, float]:
        """Get individual factor scores for debugging/inspection."""
        return {
            "access_frequency": round(self._score_access_frequency(entry), 4),
            "recency": round(self._score_recency(entry), 4),
            "agent_priority": round(self._score_agent_priority(entry), 4),
            "task_criticality": round(self._score_task_criticality(entry), 4),
            "cross_references": round(self._score_cross_references(entry), 4),
        }

    def update_entry_score(self, entry: MemoryEntry) -> MemoryEntry:
        """Calculate and update the importance score on a memory entry."""
        score = self.calculate_score(entry)
        factors = self.get_factor_breakdown(entry)

        entry.metadata = entry.metadata or {}
        entry.metadata["importance_score"] = round(score, 4)
        entry.metadata["importance_factors"] = factors
        entry.metadata["importance_scored_at"] = datetime.now(UTC).isoformat()

        return entry

    def override_score(
        self,
        entry: MemoryEntry,
        score: float,
        reason: str = "",
        author: str = "manual"
    ) -> MemoryEntry:
        """
        Manually override the importance score.

        Args:
            entry: Memory entry to update
            score: New importance score (0-1)
            reason: Reason for override
            author: Who/what initiated the override

        Returns:
            Updated memory entry
        """
        clamped_score = max(self.config.score_min, min(self.config.score_max, score))

        entry.metadata = entry.metadata or {}
        entry.metadata["importance_score"] = round(clamped_score, 4)
        entry.metadata["importance_override"] = {
            "score": round(clamped_score, 4),
            "reason": reason,
            "author": author,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        entry.metadata["importance_factors"] = self.get_factor_breakdown(entry)

        return entry

    def get_score(self, entry: MemoryEntry) -> float | None:
        """Get the stored importance score from entry metadata, if present."""
        metadata = entry.metadata or {}
        return metadata.get("importance_score")

    def clear_override(self, entry: MemoryEntry) -> MemoryEntry:
        """Clear manual importance override and recalculate."""
        entry.metadata = entry.metadata or {}
        if "importance_override" in entry.metadata:
            del entry.metadata["importance_override"]
        return self.update_entry_score(entry)

    def sort_by_importance(self, entries: list[MemoryEntry], descending: bool = True) -> list[MemoryEntry]:
        """Sort entries by importance score."""
        return sorted(
            entries,
            key=lambda e: self.get_score(e) or self.calculate_score(e),
            reverse=descending,
        )

    def filter_by_importance(
        self,
        entries: list[MemoryEntry],
        min_score: float = 0.0,
        max_score: float = 1.0
    ) -> list[MemoryEntry]:
        """Filter entries by importance score range."""
        return [
            e for e in entries
            if min_score <= (self.get_score(e) or self.calculate_score(e)) <= max_score
        ]


def calculate_importance_score(
    entry: MemoryEntry,
    config: ImportanceScoringConfig = None
) -> float:
    """Convenience function to calculate importance score."""
    scorer = ImportanceScorer(config)
    return scorer.calculate_score(entry)


def update_entry_importance(
    entry: MemoryEntry,
    config: ImportanceScoringConfig = None
) -> MemoryEntry:
    """Convenience function to update entry importance score."""
    scorer = ImportanceScorer(config)
    return scorer.update_entry_score(entry)


def override_entry_importance(
    entry: MemoryEntry,
    score: float,
    reason: str = "",
    author: str = "manual",
    config: ImportanceScoringConfig = None
) -> MemoryEntry:
    """Convenience function to override entry importance score."""
    scorer = ImportanceScorer(config)
    return scorer.override_score(entry, score, reason, author)


__all__ = [
    "ImportanceScoringConfig",
    "DEFAULT_SCORING_CONFIG",
    "DEFAULT_IMPORTANCE_SCORING_CONFIG",
    "ImportanceScorer",
    "calculate_importance_score",
    "update_entry_importance",
    "override_entry_importance",
]