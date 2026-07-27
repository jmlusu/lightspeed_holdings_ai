import json
import os
from datetime import datetime, UTC, date
from dataclasses import dataclass, field


@dataclass
class UsageRecord:
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    agent_id: str = ""
    task_id: str = ""
    timestamp: str = ""


@dataclass
class BudgetConfig:
    daily_limit_usd: float = 50.0
    task_limit_usd: float = 5.0
    enabled: bool = True


_MODEL_PRICING = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "llama3": {"input": 0.0, "output": 0.0},
    "llama3:8b": {"input": 0.0, "output": 0.0},
    "llama3:70b": {"input": 0.0, "output": 0.0},
}


class CostTracker:

    def __init__(
        self,
        results_dir: str = "results",
        budget: BudgetConfig = None,
    ):
        self.results_dir = results_dir
        self.budget = budget or BudgetConfig()
        self._daily_cost = 0.0
        self._task_cost = 0.0
        self._current_date = date.today()
        self._usage_log = []
        os.makedirs(results_dir, exist_ok=True)

    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        pricing = _MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
        input_cost = prompt_tokens * pricing["input"] / 1000
        output_cost = completion_tokens * pricing["output"] / 1000
        return input_cost + output_cost

    def record_usage(
        self,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        agent_id: str = "",
        task_id: str = "",
    ) -> UsageRecord:
        cost = self.calculate_cost(model, prompt_tokens, completion_tokens)

        record = UsageRecord(
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
            agent_id=agent_id,
            task_id=task_id,
            timestamp=datetime.now(UTC).isoformat(),
        )

        self._usage_log.append(record)
        self._task_cost += cost

        today = date.today()
        if today != self._current_date:
            self._daily_cost = 0.0
            self._current_date = today
        self._daily_cost += cost

        self._append_log(record)
        return record

    def check_budget(self, task_id: str = "") -> tuple[bool, str]:
        if not self.budget.enabled:
            return True, "Budget tracking disabled"

        if self._daily_cost >= self.budget.daily_limit_usd:
            return False, (
                f"Daily budget exceeded: ${self._daily_cost:.4f} / "
                f"${self.budget.daily_limit_usd:.2f}"
            )

        if self._task_cost >= self.budget.task_limit_usd:
            return False, (
                f"Task budget exceeded: ${self._task_cost:.4f} / "
                f"${self.budget.task_limit_usd:.2f}"
            )

        return True, "OK"

    def reset_task_cost(self):
        self._task_cost = 0.0

    def get_summary(self) -> dict:
        total_tokens = sum(
            r.prompt_tokens + r.completion_tokens for r in self._usage_log
        )
        total_cost = sum(r.cost_usd for r in self._usage_log)

        by_model = {}
        for r in self._usage_log:
            if r.model not in by_model:
                by_model[r.model] = {"calls": 0, "tokens": 0, "cost": 0.0}
            by_model[r.model]["calls"] += 1
            by_model[r.model]["tokens"] += r.prompt_tokens + r.completion_tokens
            by_model[r.model]["cost"] += r.cost_usd

        return {
            "total_calls": len(self._usage_log),
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "daily_cost_usd": self._daily_cost,
            "task_cost_usd": self._task_cost,
            "daily_budget_remaining": max(
                0, self.budget.daily_limit_usd - self._daily_cost
            ),
            "task_budget_remaining": max(
                0, self.budget.task_limit_usd - self._task_cost
            ),
            "by_model": by_model,
        }

    def _append_log(self, record: UsageRecord):
        path = os.path.join(self.results_dir, "cost_log.jsonl")
        entry = {
            "timestamp": record.timestamp,
            "model": record.model,
            "provider": record.provider,
            "prompt_tokens": record.prompt_tokens,
            "completion_tokens": record.completion_tokens,
            "cost_usd": record.cost_usd,
            "agent_id": record.agent_id,
            "task_id": record.task_id,
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
