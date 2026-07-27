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
        correlation_id: str = "",
    ):
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "task_id": task_id,
            "event": event,
            "agent_id": agent_id,
            "correlation_id": correlation_id or task_id,
            "details": details or {},
        }
        self._write_entry(entry)

    def log_tool_call(
        self,
        task_id: str,
        agent_id: str,
        tool: str,
        args: dict,
        result: str,
        success: bool,
        correlation_id: str = "",
        cost_usd: float = 0.0,
    ):
        self.record(
            task_id=task_id,
            event="tool_call",
            agent_id=agent_id,
            correlation_id=correlation_id,
            details={
                "tool": tool,
                "args": args,
                "result": result[:2000],
                "success": success,
                "cost_usd": cost_usd,
            },
        )

    def log_decision(
        self,
        task_id: str,
        agent_id: str,
        decision: str,
        rationale: str,
        tier: str = "",
        approved: bool = True,
        correlation_id: str = "",
    ):
        self.record(
            task_id=task_id,
            event="decision",
            agent_id=agent_id,
            correlation_id=correlation_id,
            details={
                "decision": decision,
                "rationale": rationale,
                "tier": tier,
                "approved": approved,
            },
        )

    def log_permission_check(
        self,
        task_id: str,
        agent_id: str,
        tool: str,
        approved: bool,
        tier: str,
        reason: str = "",
        correlation_id: str = "",
    ):
        self.record(
            task_id=task_id,
            event="permission_check",
            agent_id=agent_id,
            correlation_id=correlation_id,
            details={
                "tool": tool,
                "approved": approved,
                "tier": tier,
                "reason": reason,
            },
        )

    def log_iteration(
        self,
        task_id: str,
        agent_id: str,
        iteration: int,
        thought: str,
        action: str,
        observation: str,
        correlation_id: str = "",
    ):
        self.record(
            task_id=task_id,
            event="iteration",
            agent_id=agent_id,
            correlation_id=correlation_id,
            details={
                "iteration": iteration,
                "thought": thought[:500],
                "action": action,
                "observation": observation[:1000],
            },
        )

    def log_cost(
        self,
        task_id: str,
        agent_id: str,
        model: str,
        tokens: int,
        cost_usd: float,
        correlation_id: str = "",
    ):
        self.record(
            task_id=task_id,
            event="cost",
            agent_id=agent_id,
            correlation_id=correlation_id,
            details={
                "model": model,
                "tokens": tokens,
                "cost_usd": cost_usd,
            },
        )

    def get_entries(
        self,
        task_id: str = None,
        agent_id: str = None,
        event: str = None,
        correlation_id: str = None,
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
                if event and entry.get("event") != event:
                    continue
                if correlation_id and entry.get("correlation_id") != correlation_id:
                    continue
                results.append(entry)

        return results[-limit:]

    def get_task_trace(self, task_id: str) -> list[dict]:
        return self.get_entries(task_id=task_id, limit=1000)

    def get_correlation_trace(self, correlation_id: str) -> list[dict]:
        return self.get_entries(correlation_id=correlation_id, limit=1000)

    def get_agent_history(self, agent_id: str, limit: int = 50) -> list[dict]:
        return self.get_entries(agent_id=agent_id, limit=limit)

    def _write_entry(self, entry: dict):
        path = os.path.join(self.store.directory, self.audit_file)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
