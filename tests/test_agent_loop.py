import pytest

from lightspeed_agents.core.agent_loop import AgentLoop, LoopConfig
from lightspeed_agents.core.tool_runner import ToolRunner, ToolResult
from lightspeed_agents.core.cost_tracker import CostTracker
from lightspeed_agents.providers.base import LLMProvider


class MockProvider(LLMProvider):
    def __init__(self, responses=None):
        self.responses = responses or []
        self._call_count = 0
        self.calls = []

    def complete(self, prompt, system="", model="", temperature=0.7, max_tokens=2048):
        self.calls.append({"prompt": prompt, "system": system, "model": model})
        if self._call_count < len(self.responses):
            resp = self.responses[self._call_count]
            self._call_count += 1
            return resp
        self._call_count += 1
        return '{"thought": "done", "action": "finish", "final_answer": "done"}'


class MockToolRunner(ToolRunner):
    def __init__(self):
        self.executed = []

    def run_plan(self, plan):
        self.executed.append(plan)
        if plan.tool == "search":
            return ToolResult(tool="search", success=True, output="Found: test result")
        elif plan.tool == "python":
            return ToolResult(tool="python", success=True, output="42")
        elif plan.tool == "read":
            return ToolResult(tool="read", success=True, output="file content")
        return ToolResult(tool=plan.tool, success=True, output="ok")


@pytest.fixture
def mock_provider():
    return MockProvider()


@pytest.fixture
def mock_runner():
    return MockToolRunner()


@pytest.fixture
def cost_tracker(tmp_path):
    return CostTracker(results_dir=str(tmp_path / "results"))


@pytest.fixture
def loop(mock_provider, mock_runner, cost_tracker):
    config = LoopConfig(max_iterations=5, max_tokens_per_call=512)
    return AgentLoop(
        provider=mock_provider,
        tool_runner=mock_runner,
        cost_tracker=cost_tracker,
        config=config,
    )


class TestAgentLoopBasic:
    def test_single_iteration_finish(self, loop, mock_provider):
        mock_provider.responses = [
            '{"thought": "I know the answer", "action": "finish", "final_answer": "42"}'
        ]
        result = loop.run(task="What is 6*7?", task_id="t1")
        assert result.success is True
        assert "42" in result.response
        assert result.iterations == 1
        assert result.tool_calls == 0

    def test_multi_iteration_with_tool(self, loop, mock_provider, mock_runner):
        mock_provider.responses = [
            '{"thought": "Need to search", "action": "search", "action_input": {"query": "test"}}',
            '{"thought": "Got result", "action": "finish", "final_answer": "Found it"}',
        ]
        result = loop.run(task="Find test", task_id="t2")
        assert result.success is True
        assert result.iterations == 2
        assert result.tool_calls == 1
        assert len(mock_runner.executed) == 1
        assert mock_runner.executed[0].tool == "search"

    def test_three_iterations(self, loop, mock_provider, mock_runner):
        mock_provider.responses = [
            '{"thought": "step 1", "action": "python", "action_input": {"code": "1+1"}}',
            '{"thought": "step 2", "action": "read", "action_input": {"path": "file.txt"}}',
            '{"thought": "done", "action": "finish", "final_answer": "complete"}',
        ]
        result = loop.run(task="Multi-step", task_id="t3")
        assert result.iterations == 3
        assert result.tool_calls == 2
        assert len(mock_runner.executed) == 2


class TestAgentLoopBudget:
    def test_budget_exceeded(self, loop, mock_provider, cost_tracker):
        cost_tracker.budget.task_limit_usd = 0.0
        mock_provider.responses = [
            '{"thought": "try", "action": "search", "action_input": {"query": "x"}}',
        ]
        result = loop.run(task="Budget test", task_id="t4")
        assert result.success is False
        assert "exceeded" in result.error.lower()

    def test_budget_check_before_each_iteration(self, mock_provider, mock_runner):
        tmp_tracker = CostTracker(results_dir="results")
        tmp_tracker.budget.task_limit_usd = 0.00001
        config = LoopConfig(max_iterations=5, max_tokens_per_call=512)
        test_loop = AgentLoop(mock_provider, mock_runner, tmp_tracker, config)
        mock_provider.responses = [
            '{"thought": "step1", "action": "search", "action_input": {"query": "a"}}',
            '{"thought": "step2", "action": "search", "action_input": {"query": "b"}}',
            '{"thought": "step3", "action": "search", "action_input": {"query": "c"}}',
        ]
        result = test_loop.run(task="Budget test", task_id="t5", model="gpt-4o")
        assert result.success is False
        assert "exceeded" in result.error.lower()
        assert result.iterations < 3


class TestAgentLoopMaxIterations:
    def test_stops_at_max(self, mock_provider, mock_runner, cost_tracker):
        config = LoopConfig(max_iterations=2)
        loop = AgentLoop(mock_provider, mock_runner, cost_tracker, config)
        mock_provider.responses = [
            '{"thought": "keep going", "action": "search", "action_input": {"query": "a"}}',
            '{"thought": "still going", "action": "python", "action_input": {"code": "1"}}',
        ]
        result = loop.run(task="Loop forever", task_id="t6")
        assert result.iterations == 2
        assert len(mock_runner.executed) == 2


class TestAgentLoopParsing:
    def test_handles_plain_text_response(self, loop, mock_provider):
        mock_provider.responses = ["This is just a plain text response"]
        result = loop.run(task="Plain text", task_id="t7")
        assert result.success is True
        assert result.iterations == 1

    def test_handles_malformed_json(self, loop, mock_provider):
        mock_provider.responses = ["{invalid json"]
        result = loop.run(task="Bad JSON", task_id="t8")
        assert result.success is True

    def test_handles_json_with_extra_text(self, loop, mock_provider):
        mock_provider.responses = [
            'Here is my response: {"thought": "ok", "action": "finish", "final_answer": "yes"}'
        ]
        result = loop.run(task="Extra text", task_id="t9")
        assert result.success is True
        assert "yes" in result.response


class TestAgentLoopAudit:
    def test_iteration_history_recorded(self, loop, mock_provider, mock_runner):
        mock_provider.responses = [
            '{"thought": "search first", "action": "search", "action_input": {"query": "q"}}',
            '{"thought": "now finish", "action": "finish", "final_answer": "done"}',
        ]
        result = loop.run(task="Audit test", task_id="t10")
        assert len(result.iteration_history) == 2

        first = result.iteration_history[0]
        assert first.iteration == 1
        assert "search first" in first.thought
        assert first.action == "search"
        assert "Success" in first.observation

    def test_total_cost_tracked(self, loop, cost_tracker):
        result = loop.run(task="Cost test", task_id="t11")
        assert result.total_cost_usd >= 0


class TestAgentLoopToolRunner:
    def test_tool_execution_called(self, loop, mock_provider, mock_runner):
        mock_provider.responses = [
            '{"thought": "run code", "action": "python", "action_input": {"code": "print(1)"}}',
            '{"thought": "done", "action": "finish", "final_answer": "ok"}',
        ]
        result = loop.run(task="Run code", task_id="t12")
        assert len(mock_runner.executed) == 1
        assert mock_runner.executed[0].tool == "python"
        assert mock_runner.executed[0].args["code"] == "print(1)"

    def test_tool_failure_fed_back(self, loop, mock_provider):
        class FailingRunner(ToolRunner):
            def run_plan(self, plan):
                return ToolResult(
                    tool=plan.tool, success=False, output="", error="Permission denied"
                )

        loop.tool_runner = FailingRunner()
        mock_provider.responses = [
            '{"thought": "try", "action": "python", "action_input": {"code": "1"}}',
            '{"thought": "failed, try finish", "action": "finish", "final_answer": "failed"}',
        ]
        result = loop.run(task="Fail test", task_id="t13")
        assert result.success is True
        assert result.iterations == 2
