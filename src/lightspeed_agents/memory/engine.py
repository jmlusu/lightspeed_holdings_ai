from datetime import datetime, timezone

from lightspeed_agents.memory.models import MemoryEntry
from lightspeed_agents.memory.filestore import FileStore
from lightspeed_agents.memory.search import keyword_search
from lightspeed_agents.memory.consolidation import (
    ConsolidationScheduler,
    ConsolidationConfig,
)


MEMORY_TYPES = [
    "episodic", "semantic", "procedural",
    "relational", "temporal", "aggregate",
]


class MemoryEngine:

    def __init__(self, memory_dir: str = "memory", config: ConsolidationConfig = None):
        self.filestore = FileStore(memory_dir)
        self.scheduler = ConsolidationScheduler(self.filestore, config)
        self._tick_count = 0

    def record_task_outcome(
        self,
        task_id: str,
        agent_id: str,
        content: str,
        status: str = "completed",
        department: str = "",
        tags: list[str] = None,
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
        self._append("episodic.json", entry)
        self._tick()
        return entry

    def record_knowledge(
        self,
        content: str,
        agent_id: str = "",
        department: str = "",
        tags: list[str] = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            content=content,
            memory_type="semantic",
            agent_id=agent_id,
            department=department,
            tags=tags or ["knowledge"],
        )
        self._append("semantic.json", entry)
        self._tick()
        return entry

    def record_procedure(
        self,
        content: str,
        agent_id: str = "",
        tags: list[str] = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            content=content,
            memory_type="procedural",
            agent_id=agent_id,
            tags=tags or ["procedure"],
        )
        self._append("procedural.json", entry)
        self._tick()
        return entry

    def record_relationship(
        self,
        content: str,
        agent_id: str = "",
        tags: list[str] = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            content=content,
            memory_type="relational",
            agent_id=agent_id,
            tags=tags or ["relationship"],
        )
        self._append("relational.json", entry)
        self._tick()
        return entry

    def record_temporal(
        self,
        content: str,
        agent_id: str = "",
        tags: list[str] = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            content=content,
            memory_type="temporal",
            agent_id=agent_id,
            tags=tags or ["temporal"],
        )
        self._append("temporal.json", entry)
        self._tick()
        return entry

    def recall_context(
        self,
        query: str,
        agent_id: str = "",
        memory_types: list[str] = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        types = memory_types or ["episodic", "semantic", "procedural"]
        all_entries = []

        for mt in types:
            entries = self.get_entries(mt)
            if agent_id:
                entries = [e for e in entries if e.agent_id == agent_id]
            all_entries.extend(entries)

        results = keyword_search(all_entries, query, limit)

        for entry in results:
            entry.touch()
            self._update_entry(entry)

        return results

    def search(
        self,
        query: str,
        memory_types: list[str] = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        types = memory_types or MEMORY_TYPES
        all_entries = []

        for mt in types:
            all_entries.extend(self.get_entries(mt))

        return keyword_search(all_entries, query, limit)

    def get_entries(self, memory_type: str) -> list[MemoryEntry]:
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
