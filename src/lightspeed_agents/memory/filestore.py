import json
import os
import tempfile
from pathlib import Path

from lightspeed_agents.memory.models import MemoryEntry


class FileStore:

    def __init__(self, directory: str):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def load(self, filename: str) -> list[MemoryEntry]:
        path = self.dir / filename
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [MemoryEntry(**e) for e in data]

    def save(self, filename: str, entries: list[MemoryEntry]):
        path = self.dir / filename
        data = [e.model_dump() for e in entries]

        fd, tmp_path = tempfile.mkstemp(
            dir=str(self.dir), suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def exists(self, filename: str) -> bool:
        return (self.dir / filename).exists()

    def delete(self, filename: str):
        path = self.dir / filename
        if path.exists():
            path.unlink()
