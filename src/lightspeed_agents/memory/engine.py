from lightspeed_agents.memory.models import MemoryEntry
from lightspeed_agents.memory.filestore import FileStore
from lightspeed_agents.memory.search import keyword_search
from lightspeed_agents.memory.consolidation import (
    ConsolidationScheduler,
    ConsolidationConfig,
)
from lightspeed_agents.memory.decay import (
    DecayConfig,
    DEFAULT_DECAY_CONFIG,
    calculate_decayed_importance,
    apply_decay_to_entry,
)
from lightspeed_agents.memory.scoring import (
    ImportanceScorer,
    DEFAULT_SCORING_CONFIG,
)

MEMORY_TYPES = [
    "episodic",
    "semantic",
    "procedural",
    "relational",
    "temporal",
    "aggregate",
]


class MemoryEngine:

    def __init__(
        self,
        memory_dir: str = "memory",
        config: ConsolidationConfig = None,
        decay_config: DecayConfig = None,
        scoring_config=None,
    ):
        self.filestore = FileStore(memory_dir)
        self.scheduler = ConsolidationScheduler(self.filestore, config)
        self.decay_config = decay_config or DEFAULT_DECAY_CONFIG
        self.scoring_config = scoring_config or DEFAULT_SCORING_CONFIG
        self.scorer = ImportanceScorer(self.scoring_config)
        self._tick_count = 0

    def record_task_outcome(
        self,
        task_id: str,
        agent_id: str,
        content: str,
        status: str = "completed",
        department: str = "",
        tags: list[str] = None,
        importance: float = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            content=content,
            memory_type="episodic",
            agent_id=agent_id,
            task_id=task_id,
            department=department,
            tags=tags or ["task", status],
            metadata={"status": status},
        )
        # Calculate importance score if not manually provided
        if importance is not None:
            entry.metadata["importance_score"] = importance
        else:
            entry = self.scorer.update_entry_score(entry)
        self._append("episodic.json", entry)
        self._tick()
        return entry

    def record_knowledge(
        self,
        content: str,
        agent_id: str = "",
        department: str = "",
        tags: list[str] = None,
        importance: float = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            content=content,
            memory_type="semantic",
            agent_id=agent_id,
            department=department,
            tags=tags or ["knowledge"],
        )
        if importance is not None:
            entry.metadata["importance_score"] = importance
        else:
            entry = self.scorer.update_entry_score(entry)
        self._append("semantic.json", entry)
        self._tick()
        return entry

    def record_procedure(
        self,
        content: str,
        agent_id: str = "",
        tags: list[str] = None,
        importance: float = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            content=content,
            memory_type="procedural",
            agent_id=agent_id,
            tags=tags or ["procedure"],
        )
        if importance is not None:
            entry.metadata["importance_score"] = importance
        else:
            entry = self.scorer.update_entry_score(entry)
        self._append("procedural.json", entry)
        self._tick()
        return entry

    def record_relationship(
        self,
        content: str,
        agent_id: str = "",
        tags: list[str] = None,
        importance: float = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            content=content,
            memory_type="relational",
            agent_id=agent_id,
            tags=tags or ["relationship"],
        )
        if importance is not None:
            entry.metadata["importance_score"] = importance
        else:
            entry = self.scorer.update_entry_score(entry)
        self._append("relational.json", entry)
        self._tick()
        return entry

    def record_temporal(
        self,
        content: str,
        agent_id: str = "",
        tags: list[str] = None,
        importance: float = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            content=content,
            memory_type="temporal",
            agent_id=agent_id,
            tags=tags or ["temporal"],
        )
        if importance is not None:
            entry.metadata["importance_score"] = importance
        else:
            entry = self.scorer.update_entry_score(entry)
        self._append("temporal.json", entry)
        self._tick()
        return entry

    def recall_context(
        self,
        query: str,
        agent_id: str = "",
        memory_types: list[str] = None,
        limit: int = 10,
        apply_decay: bool = True,
    ) -> list[MemoryEntry]:
        types = memory_types or ["episodic", "semantic", "procedural"]
        all_entries = []

        for mt in types:
            entries = self.get_entries(mt, apply_decay=apply_decay)
            if agent_id:
                entries = [e for e in entries if e.agent_id == agent_id]
            all_entries.extend(entries)

        results = keyword_search(all_entries, query, limit)

        if apply_decay:
            for entry in results:
                entry.metadata["decayed_importance"] = calculate_decayed_importance(entry, self.decay_config)
            results.sort(key=lambda e: e.metadata.get("decayed_importance", 0), reverse=True)

        for entry in results:
            entry.touch()
            self._update_entry(entry)

        return results

    def search(
        self,
        query: str,
        memory_types: list[str] = None,
        limit: int = 10,
        apply_decay: bool = True,
    ) -> list[MemoryEntry]:
        types = memory_types or MEMORY_TYPES
        all_entries = []

        for mt in types:
            all_entries.extend(self.get_entries(mt))

        results = keyword_search(all_entries, query, limit)

        if apply_decay:
            # Apply decay and re-sort by decayed importance
            for entry in results:
                entry.metadata["decayed_importance"] = calculate_decayed_importance(entry, self.decay_config)
            results.sort(key=lambda e: e.metadata.get("decayed_importance", 0), reverse=True)

        return results

    def search_by_importance(
        self,
        query: str,
        memory_types: list[str] = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> list[MemoryEntry]:
        """Search and filter/sort by importance score."""
        types = memory_types or MEMORY_TYPES
        all_entries = []

        for mt in types:
            all_entries.extend(self.get_entries_raw(mt))

        results = keyword_search(all_entries, query, limit * 2)  # Get more for filtering

        # Filter by importance
        results = [e for e in results if self.scorer.calculate_score(e) >= min_importance]

        # Sort by importance
        results.sort(key=lambda e: self.scorer.calculate_score(e), reverse=True)

        return results[:limit]

    def get_entries(self, memory_type: str, apply_decay: bool = True) -> list[MemoryEntry]:
        entries = self.filestore.load(f"{memory_type}.json")
        if apply_decay:
            entries = [apply_decay_to_entry(e, self.decay_config) for e in entries]
        return entries

    def get_entries_raw(self, memory_type: str) -> list[MemoryEntry]:
        """Get entries without applying decay (for maintenance/debugging)."""
        return self.filestore.load(f"{memory_type}.json")

    def get_stats(self) -> dict:
        stats = {}
        total = 0
        for mt in MEMORY_TYPES:
            entries = self.get_entries(mt)
            count = len(entries)
            stats[mt] = count
            total += count
        stats["total"] = total
        return stats

    def consolidate(self):
        self.scheduler.consolidate()

    def prune(self, memory_type: str = None):
        self.scheduler.prune(memory_type)

    def clear(self, memory_type: str = None):
        types = [memory_type] if memory_type else MEMORY_TYPES
        for mt in types:
            self.filestore.delete(f"{mt}.json")

    def _append(self, filename: str, entry: MemoryEntry):
        entries = self.filestore.load(filename)
        entries.append(entry)
        self.filestore.save(filename, entries)

    def _update_entry(self, updated: MemoryEntry):
        entries = self.filestore.load(f"{updated.memory_type}.json")
        for i, entry in enumerate(entries):
            if entry.id == updated.id:
                entries[i] = updated
                break
        self.filestore.save(f"{updated.memory_type}.json", entries)

    def _tick(self):
        self._tick_count += 1
        self.scheduler.on_tick()

    # Importance scoring API methods
    def get_importance(self, entry: MemoryEntry) -> float:
        """Get the current importance score for an entry."""
        return self.scorer.get_score(entry) or self.scorer.calculate_score(entry)

    def set_importance(self, entry: MemoryEntry, score: float, reason: str = "") -> MemoryEntry:
        """Manually override the importance score for an entry."""
        updated = self.scorer.override_score(entry, score, reason)
        self._update_entry(updated)
        return updated

    def recalculate_importance(self, entry: MemoryEntry) -> MemoryEntry:
        """Recalculate importance score for an entry."""
        updated = self.scorer.update_entry_score(entry)
        self._update_entry(updated)
        return updated

    def clear_importance_override(self, entry: MemoryEntry) -> MemoryEntry:
        """Clear manual importance override and recalculate."""
        updated = self.scorer.clear_override(entry)
        self._update_entry(updated)
        return updated

    def sort_by_importance(self, entries: list[MemoryEntry], descending: bool = True) -> list[MemoryEntry]:
        """Sort entries by importance score."""
        return self.scorer.sort_by_importance(entries, descending)

    def filter_by_importance(
        self,
        entries: list[MemoryEntry],
        min_score: float = 0.0,
        max_score: float = 1.0
    ) -> list[MemoryEntry]:
        """Filter entries by importance score range."""
        return self.scorer.filter_by_importance(entries, min_score, max_score)
