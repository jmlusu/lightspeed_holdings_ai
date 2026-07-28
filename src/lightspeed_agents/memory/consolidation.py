from collections import Counter
from datetime import datetime, UTC

from lightspeed_agents.memory.models import MemoryEntry
from lightspeed_agents.memory.filestore import FileStore
from lightspeed_agents.memory.decay import (
    DecayConfig,
    DEFAULT_DECAY_CONFIG,
    apply_decay_to_entries,
    should_prune_by_decay,
)


class ConsolidationConfig:
    def __init__(
        self,
        tick_interval: int = 50,
        entry_threshold: int = 500,
        capacity_cap: int = 2000,
        age_prune_days: int = 90,
        decay_config: DecayConfig = None,
        decay_prune_threshold: float = 0.05,
        high_importance_threshold: float = 0.8,
    ):
        self.tick_interval = tick_interval
        self.entry_threshold = entry_threshold
        self.capacity_cap = capacity_cap
        self.age_prune_days = age_prune_days
        self.decay_config = decay_config or DEFAULT_DECAY_CONFIG
        self.decay_prune_threshold = decay_prune_threshold
        self.high_importance_threshold = high_importance_threshold


class ConsolidationScheduler:

    def __init__(self, filestore: FileStore, config: ConsolidationConfig = None):
        self.filestore = filestore
        self.config = config or ConsolidationConfig()
        self.tick_count = 0

    def on_tick(self):
        self.tick_count += 1
        if self.tick_count % self.config.tick_interval == 0:
            self.consolidate()

    def consolidate(self):
        for memory_type in [
            "episodic",
            "semantic",
            "procedural",
            "relational",
            "temporal",
            "aggregate",
        ]:
            filename = f"{memory_type}.json"
            entries = self.filestore.load(filename)

            if not entries:
                continue

            entries = self._apply_decay(entries, memory_type)
            entries = self._prune(entries, memory_type)
            entries = self._deduplicate(entries, memory_type)
            entries = self._enforce_cap(entries)

            self.filestore.save(filename, entries)

        self._generate_aggregates()

    def prune(self, memory_type: str = None):
        types = (
            [memory_type]
            if memory_type
            else [
                "episodic",
                "semantic",
                "procedural",
                "relational",
                "temporal",
            ]
        )

        for mt in types:
            filename = f"{mt}.json"
            entries = self.filestore.load(filename)
            entries = self._apply_decay(entries, mt)
            entries = self._prune(entries, mt)
            entries = self._enforce_cap(entries)
            self.filestore.save(filename, entries)

    def _apply_decay(self, entries: list[MemoryEntry], memory_type: str) -> list[MemoryEntry]:
        """Apply temporal decay to entries based on memory type."""
        return apply_decay_to_entries(entries, self.config.decay_config)

    def _prune(self, entries: list[MemoryEntry], memory_type: str) -> list[MemoryEntry]:
        result = []
        for entry in entries:
            # Skip pruning for high-importance memories
            if entry.get_importance() >= self.config.high_importance_threshold:
                result.append(entry)
                continue

            # Age-based pruning for episodic memories
            if memory_type == "episodic":
                if entry.is_older_than_days(self.config.age_prune_days):
                    continue

            # Decay-based pruning
            if should_prune_by_decay(entry, self.config.decay_config, self.config.decay_prune_threshold):
                continue

            result.append(entry)
        return result

    def _deduplicate(
        self, entries: list[MemoryEntry], memory_type: str
    ) -> list[MemoryEntry]:
        if memory_type != "semantic":
            return entries

        seen = {}
        result = []
        for entry in entries:
            normalized = " ".join(entry.content.lower().split())
            if normalized not in seen:
                seen[normalized] = entry
                result.append(entry)
        return result

    def _enforce_cap(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        if len(entries) <= self.config.capacity_cap:
            return entries

        entries.sort(
            key=lambda e: (e.access_count, e.created_at),
            reverse=True,
        )
        return entries[: self.config.capacity_cap]

    def _generate_aggregates(self):
        all_entries = {}
        for mt in ["episodic", "semantic", "procedural", "relational", "temporal"]:
            entries = self.filestore.load(f"{mt}.json")
            all_entries[mt] = entries

        tag_counts = Counter()
        agent_counts = Counter()
        dept_counts = Counter()

        for entries in all_entries.values():
            for entry in entries:
                tag_counts.update(entry.tags)
                if entry.agent_id:
                    agent_counts[entry.agent_id] += 1
                if entry.department:
                    dept_counts[entry.department] += 1

        aggregates = []

        if tag_counts:
            top_tags = tag_counts.most_common(20)
            aggregates.append(
                MemoryEntry(
                    content=f"Top tags: {', '.join(f'{t}({c})' for t, c in top_tags)}",
                    memory_type="aggregate",
                    tags=["stats", "tags"],
                    metadata={"top_tags": dict(top_tags)},
                )
            )

        if agent_counts:
            top_agents = agent_counts.most_common(20)
            aggregates.append(
                MemoryEntry(
                    content=f"Most active agents: {', '.join(f'{a}({c})' for a, c in top_agents)}",
                    memory_type="aggregate",
                    tags=["stats", "agents"],
                    metadata={"top_agents": dict(top_agents)},
                )
            )

        if dept_counts:
            top_depts = dept_counts.most_common(20)
            aggregates.append(
                MemoryEntry(
                    content=f"Most active departments: {', '.join(f'{d}({c})' for d, c in top_depts)}",
                    memory_type="aggregate",
                    tags=["stats", "departments"],
                    metadata={"top_departments": dict(top_depts)},
                )
            )

        total_counts = {mt: len(entries) for mt, entries in all_entries.items()}
        aggregates.append(
            MemoryEntry(
                content=f"Entry counts: {total_counts}",
                memory_type="aggregate",
                tags=["stats", "counts"],
                metadata={"counts": total_counts},
            )
        )

        self.filestore.save("aggregate.json", aggregates)
