import json
import os
import tempfile

import pytest

from lightspeed_agents.core.cost_tracker import CostTracker, BudgetConfig, UsageRecord


@pytest.fixture
def tmp_results(tmp_path):
    return str(tmp_path / "results")


@pytest.fixture
def tracker(tmp_results):
    return CostTracker(results_dir=tmp_results)


@pytest.fixture
def tracker_with_budget(tmp_results):
    budget = BudgetConfig(daily_limit_usd=1.0, task_limit_usd=0.50, enabled=True)
    return CostTracker(results_dir=tmp_results, budget=budget)


class TestCostCalculation:
    def test_calculate_cost_gpt4o(self, tracker):
        cost = tracker.calculate_cost("gpt-4o", 1000, 500)
        assert cost == pytest.approx(0.005 + 0.0075, abs=0.001)

    def test_calculate_cost_gpt4o_mini(self, tracker):
        cost = tracker.calculate_cost("gpt-4o-mini", 1000, 500)
        assert cost == pytest.approx(0.00015 + 0.0003, abs=0.0001)

    def test_calculate_cost_ollama(self, tracker):
        cost = tracker.calculate_cost("llama3", 1000, 500)
        assert cost == 0.0

    def test_calculate_cost_unknown_model(self, tracker):
        cost = tracker.calculate_cost("unknown-model", 1000, 500)
        assert cost == 0.0


class TestRecordUsage:
    def test_record_usage(self, tracker):
        record = tracker.record_usage(
            model="gpt-4o-mini",
            provider="OpenAIProvider",
            prompt_tokens=100,
            completion_tokens=50,
            agent_id="test-agent",
            task_id="task-1",
        )
        assert record.model == "gpt-4o-mini"
        assert record.provider == "OpenAIProvider"
        assert record.prompt_tokens == 100
        assert record.completion_tokens == 50
        assert record.cost_usd > 0
        assert record.agent_id == "test-agent"
        assert record.task_id == "task-1"

    def test_record_usage_appends_to_log(self, tracker, tmp_results):
        tracker.record_usage("gpt-4o-mini", "openai", 100, 50)
        tracker.record_usage("gpt-4o-mini", "openai", 200, 100)

        log_path = os.path.join(tmp_results, "cost_log.jsonl")
        assert os.path.exists(log_path)
        with open(log_path) as f:
            lines = f.readlines()
        assert len(lines) == 2

    def test_record_usage_accumulates_cost(self, tracker):
        tracker.record_usage("gpt-4o-mini", "openai", 100, 50)
        first_cost = tracker._task_cost
        tracker.record_usage("gpt-4o-mini", "openai", 100, 50)
        assert tracker._task_cost == pytest.approx(first_cost * 2, abs=0.0001)


class TestBudget:
    def test_budget_check_within_limits(self, tracker_with_budget):
        allowed, reason = tracker_with_budget.check_budget()
        assert allowed is True
        assert reason == "OK"

    def test_budget_check_daily_exceeded(self, tracker_with_budget):
        tracker_with_budget._daily_cost = 1.5
        allowed, reason = tracker_with_budget.check_budget()
        assert allowed is False
        assert "Daily budget exceeded" in reason

    def test_budget_check_task_exceeded(self, tracker_with_budget):
        tracker_with_budget._task_cost = 0.6
        allowed, reason = tracker_with_budget.check_budget()
        assert allowed is False
        assert "Task budget exceeded" in reason

    def test_budget_disabled(self, tmp_results):
        budget = BudgetConfig(enabled=False)
        tracker = CostTracker(results_dir=tmp_results, budget=budget)
        tracker._daily_cost = 999.0
        allowed, reason = tracker.check_budget()
        assert allowed is True

    def test_reset_task_cost(self, tracker):
        tracker.record_usage("gpt-4o-mini", "openai", 100, 50)
        assert tracker._task_cost > 0
        tracker.reset_task_cost()
        assert tracker._task_cost == 0.0


class TestSummary:
    def test_summary_empty(self, tracker):
        summary = tracker.get_summary()
        assert summary["total_calls"] == 0
        assert summary["total_tokens"] == 0
        assert summary["total_cost_usd"] == 0.0

    def test_summary_with_usage(self, tracker):
        tracker.record_usage("gpt-4o-mini", "openai", 100, 50)
        tracker.record_usage("gpt-4o-mini", "openai", 200, 100)

        summary = tracker.get_summary()
        assert summary["total_calls"] == 2
        assert summary["total_tokens"] > 0
        assert "gpt-4o-mini" in summary["by_model"]
        assert summary["by_model"]["gpt-4o-mini"]["calls"] == 2
