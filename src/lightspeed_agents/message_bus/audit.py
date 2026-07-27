import json
import os
from datetime import datetime, UTC

from lightspeed_agents.message_bus.file_store import FileStore


class AuditStore:

    def __init__(self, directory: str = ".opencode"):
        self.store = FileStore(directory)
        self.audit_file = "audit.jsonl"

    def record(
        self,
        task_id: str,
        event: str,
        agent_id: str = "",
        details: dict = None,
    ):
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "task_id": task_id,
            "event": event,
            "agent_id": agent_id,
            "details": details or {},
        }
        path = os.path.join(self.store.directory, self.audit_file)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def get_entries(
        self,
        task_id: str = None,
        agent_id: str = None,
        limit: int = 100,
    ) -> list[dict]:
        path = os.path.join(self.store.directory, self.audit_file)
        if not os.path.exists(path):
            return []

        results = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                if task_id and entry.get("task_id") != task_id:
                    continue
                if agent_id and entry.get("agent_id") != agent_id:
                    continue
                results.append(entry)

        return results[-limit:]
