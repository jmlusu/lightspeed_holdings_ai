import pytest

from lightspeed_agents.message_bus.audit import AuditStore


@pytest.fixture
def audit(tmp_path):
    return AuditStore(directory=str(tmp_path))


class TestAuditRecord:
    def test_record_basic(self, audit, tmp_path):
        audit.record(task_id="t1", event="task_claimed", agent_id="agent-a")
        entries = audit.get_entries(task_id="t1")
        assert len(entries) == 1
        assert entries[0]["event"] == "task_claimed"
        assert entries[0]["agent_id"] == "agent-a"
        assert "timestamp" in entries[0]

    def test_record_with_details(self, audit):
        audit.record(
            task_id="t2",
            event="task_completed",
            agent_id="agent-b",
            details={"result": "success"},
        )
        entries = audit.get_entries(task_id="t2")
        assert entries[0]["details"]["result"] == "success"

    def test_record_with_correlation_id(self, audit):
        audit.record(task_id="t3", event="start", correlation_id="corr-1")
        audit.record(task_id="t4", event="next", correlation_id="corr-1")
        entries = audit.get_entries(correlation_id="corr-1")
        assert len(entries) == 2


class TestToolCallLogging:
    def test_log_tool_call(self, audit):
        audit.log_tool_call(
            task_id="t1",
            agent_id="agent-a",
            tool="python",
            args={"code": "print(1)"},
            result="1",
            success=True,
        )
        entries = audit.get_entries(task_id="t1", event="tool_call")
        assert len(entries) == 1
        assert entries[0]["details"]["tool"] == "python"
        assert entries[0]["details"]["success"] is True

    def test_log_tool_call_failure(self, audit):
        audit.log_tool_call(
            task_id="t1",
            agent_id="agent-a",
            tool="git",
            args={"args": "push"},
            result="",
            success=False,
        )
        entries = audit.get_entries(task_id="t1")
        assert entries[0]["details"]["success"] is False


class TestDecisionLogging:
    def test_log_decision(self, audit):
        audit.log_decision(
            task_id="t1",
            agent_id="cto",
            decision="Use PostgreSQL",
            rationale="Team expertise + existing infra",
            tier="department",
            approved=True,
        )
        entries = audit.get_entries(task_id="t1", event="decision")
        assert len(entries) == 1
        assert entries[0]["details"]["decision"] == "Use PostgreSQL"
        assert entries[0]["details"]["approved"] is True


class TestPermissionCheckLogging:
    def test_log_permission_check_approved(self, audit):
        audit.log_permission_check(
            task_id="t1",
            agent_id="backend-engineer",
            tool="python",
            approved=True,
            tier="T2_GATE",
        )
        entries = audit.get_entries(task_id="t1", event="permission_check")
        assert len(entries) == 1
        assert entries[0]["details"]["approved"] is True
        assert entries[0]["details"]["tier"] == "T2_GATE"

    def test_log_permission_check_denied(self, audit):
        audit.log_permission_check(
            task_id="t1",
            agent_id="content-writer",
            tool="deploy",
            approved=False,
            tier="T3_DUAL",
            reason="Insufficient permissions",
        )
        entries = audit.get_entries(task_id="t1")
        assert entries[0]["details"]["approved"] is False
        assert entries[0]["details"]["reason"] == "Insufficient permissions"


class TestIterationLogging:
    def test_log_iteration(self, audit):
        audit.log_iteration(
            task_id="t1",
            agent_id="backend-engineer",
            iteration=1,
            thought="Need to search for files",
            action="search",
            observation="Found 5 files",
        )
        entries = audit.get_entries(task_id="t1", event="iteration")
        assert len(entries) == 1
        assert entries[0]["details"]["iteration"] == 1
        assert entries[0]["details"]["action"] == "search"


class TestCostLogging:
    def test_log_cost(self, audit):
        audit.log_cost(
            task_id="t1",
            agent_id="cto",
            model="gpt-4o",
            tokens=1500,
            cost_usd=0.025,
        )
        entries = audit.get_entries(task_id="t1", event="cost")
        assert len(entries) == 1
        assert entries[0]["details"]["cost_usd"] == 0.025


class TestQueryFilters:
    def test_filter_by_agent(self, audit):
        audit.record(task_id="t1", event="e1", agent_id="agent-a")
        audit.record(task_id="t2", event="e2", agent_id="agent-b")
        audit.record(task_id="t3", event="e3", agent_id="agent-a")

        entries = audit.get_entries(agent_id="agent-a")
        assert len(entries) == 2

    def test_filter_by_event(self, audit):
        audit.record(task_id="t1", event="start")
        audit.record(task_id="t2", event="complete")
        audit.record(task_id="t3", event="start")

        entries = audit.get_entries(event="start")
        assert len(entries) == 2

    def test_limit(self, audit):
        for i in range(20):
            audit.record(task_id=f"t{i}", event="e")
        entries = audit.get_entries(limit=5)
        assert len(entries) == 5


class TestTraces:
    def test_task_trace(self, audit):
        audit.record(task_id="t1", event="claimed")
        audit.record(task_id="t1", event="completed")
        audit.record(task_id="t2", event="claimed")

        trace = audit.get_task_trace("t1")
        assert len(trace) == 2

    def test_correlation_trace(self, audit):
        audit.record(task_id="t1", event="start", correlation_id="c1")
        audit.record(task_id="t2", event="next", correlation_id="c1")
        audit.record(task_id="t3", event="other", correlation_id="c2")

        trace = audit.get_correlation_trace("c1")
        assert len(trace) == 2

    def test_agent_history(self, audit):
        audit.record(task_id="t1", event="e1", agent_id="agent-x")
        audit.record(task_id="t2", event="e2", agent_id="agent-x")
        audit.record(task_id="t3", event="e3", agent_id="agent-y")

        history = audit.get_agent_history("agent-x")
        assert len(history) == 2
