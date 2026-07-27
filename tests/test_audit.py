import pytest

from lightspeed_agents.message_bus.audit import AuditStore


@pytest.fixture
def audit(tmp_path):
    return AuditStore(str(tmp_path))


def test_audit_record(audit):
    audit.record(task_id="t-001", event="task_claimed", agent_id="cto")
    entries = audit.get_entries(task_id="t-001")
    assert len(entries) == 1
    assert entries[0]["event"] == "task_claimed"
    assert entries[0]["agent_id"] == "cto"


def test_audit_append(audit):
    audit.record(task_id="t-001", event="task_created")
    audit.record(task_id="t-001", event="task_claimed")
    audit.record(task_id="t-001", event="task_completed")
    entries = audit.get_entries(task_id="t-001")
    assert len(entries) == 3


def test_audit_filter_by_agent(audit):
    audit.record(task_id="t-001", event="task_created", agent_id="cto")
    audit.record(task_id="t-002", event="task_created", agent_id="cfo")
    entries = audit.get_entries(agent_id="cto")
    assert len(entries) == 1
    assert entries[0]["agent_id"] == "cto"


def test_audit_limit(audit):
    for i in range(10):
        audit.record(task_id=f"t-{i}", event="task_created")
    entries = audit.get_entries(limit=3)
    assert len(entries) == 3


def test_audit_empty(audit):
    entries = audit.get_entries(task_id="nonexistent")
    assert len(entries) == 0


def test_audit_with_details(audit):
    audit.record(
        task_id="t-001",
        event="task_completed",
        details={"result": "deployed"},
    )
    entries = audit.get_entries(task_id="t-001")
    assert entries[0]["details"]["result"] == "deployed"
