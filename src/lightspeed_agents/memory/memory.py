import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel


class MemoryEntry(BaseModel):
    role: str
    content: str
    timestamp: str = ""

    def __init__(self, **data):
        if not data.get("timestamp"):
            data["timestamp"] = datetime.now(timezone.utc).isoformat()
        super().__init__(**data)


class AgentMemory:

    def __init__(self, agent_id: str, memory_dir: str = "memory"):
        self.agent_id = agent_id
        self.dir = Path(memory_dir)
        self.entries: list[MemoryEntry] = []
        self._load()

    def add(self, role: str, content: str) -> MemoryEntry:
        entry = MemoryEntry(role=role, content=content)
        self.entries.append(entry)
        self._save()
        return entry

    def get_history(self, limit: int = 0) -> list[MemoryEntry]:
        if limit > 0:
            return self.entries[-limit:]
        return list(self.entries)

    def get_context(self, limit: int = 10) -> str:
        recent = self.get_history(limit)
        if not recent:
            return ""
        lines = []
        for entry in recent:
            lines.append(f"{entry.role}: {entry.content}")
        return "\n".join(lines)

    def clear(self):
        self.entries = []
        self._save()

    def _path(self) -> Path:
        return self.dir / f"{self.agent_id}.json"

    def _load(self):
        path = self._path()
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.entries = [MemoryEntry(**e) for e in data]

    def _save(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        path = self._path()
        data = [e.model_dump() for e in self.entries]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
