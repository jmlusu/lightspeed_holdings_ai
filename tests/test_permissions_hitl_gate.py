import pytest

from lightspeed_agents.message_bus.message_bus import MessageBus
from lightspeed_agents.message_bus.task_status import TaskStatus, TaskPriority
from lightspeed_agents.memory.engine import MemoryEngine
from lightspeed_agents.permissions.tiers import ActionTier
from lightspeed_agents.permissions.hitl_gate import HITLGate
from lightspeed_agents.permissions.approval import ApprovalStatus


@pytest.fixture
def tmp_bus(tmp_path):
    return MessageBus(bus_dir=str(tmp_path))


@pytest.fixture
def tmp_memory(tmp_path):
    return MemoryEngine(memory_dir=str(tmp_path))


@pytest.fixture
def gate(tmp_bus, tmp_memory):
    return HITLGate(bus=tmp_bus, memory=tmp_memory, bus_dir=tmp_bus.store.directory)


def make_task(bus, **kwargs):
    defaults = {
        "instruction": "Test task",
        "receiver_id": "test-agent",
        "priority": TaskPriority.MEDIUM,
    }
    defaults.update(kwargs)
    return bus.send_task(**defaults)


class TestHITLGate:

    def test_park_task(self, gate, tmp_bus):
        task = make_task(tmp_bus)
        request = gate.park_task(
            task_id=task.id,
            agent_id="test-agent",
            tool_name="python",
            tier=ActionTier.T2_GATE,
            instruction="Run build script",
        )
        assert request.task_id == task.id
        assert request.tool_name == "python"
        assert request.tier == ActionTier.T2_GATE
        assert request.required_approvals == 1
        assert request.status == ApprovalStatus.PENDING

        task = tmp_bus.get_task(task.id)
        assert task.status == TaskStatus.WAITING_APPROVAL

    def test_park_task_dual_approval(self, gate, tmp_bus):
        task = make_task(tmp_bus)
        request = gate.park_task(
            task_id=task.id,
            agent_id="test-agent",
            tool_name="shell",
            tier=ActionTier.T3_DUAL,
        )
        assert request.required_approvals == 2

    def test_approve_request(self, gate, tmp_bus):
        task = make_task(tmp_bus)
        request = gate.park_task(
            task_id=task.id,
            agent_id="test-agent",
            tool_name="python",
            tier=ActionTier.T2_GATE,
        )

        approved = gate.approve(request.id, "human-ceo", "Go ahead")
        assert approved.status == ApprovalStatus.APPROVED
        assert approved.approval_count == 1

        task = tmp_bus.get_task(task.id)
        assert task.status == TaskStatus.IN_PROGRESS

    def test_reject_request(self, gate, tmp_bus):
        task = make_task(tmp_bus)
        request = gate.park_task(
            task_id=task.id,
            agent_id="test-agent",
            tool_name="python",
            tier=ActionTier.T2_GATE,
        )

        rejected = gate.reject(request.id, "human-ceo", "Too risky")
        assert rejected.status == ApprovalStatus.REJECTED
        assert rejected.is_rejected is True

        task = tmp_bus.get_task(task.id)
        assert task.status == TaskStatus.FAILED

    def test_dual_approval_flow(self, gate, tmp_bus):
        task = make_task(tmp_bus)
        request = gate.park_task(
            task_id=task.id,
            agent_id="test-agent",
            tool_name="shell",
            tier=ActionTier.T3_DUAL,
        )

        gate.approve(request.id, "cto", "Technical OK")
        request = gate.get_request(request.id)
        assert request.approval_count == 1
        assert request.status == ApprovalStatus.PENDING

        gate.approve(request.id, "cfo", "Budget OK")
        request = gate.get_request(request.id)
        assert request.approval_count == 2
        assert request.status == ApprovalStatus.APPROVED

        task = tmp_bus.get_task(task.id)
        assert task.status == TaskStatus.IN_PROGRESS

    def test_approve_nonexistent_raises(self, gate):
        with pytest.raises(ValueError, match="not found"):
            gate.approve("nonexistent", "approver")

    def test_approve_already_resolved_raises(self, gate, tmp_bus):
        task = make_task(tmp_bus)
        request = gate.park_task(
            task_id=task.id,
            agent_id="test-agent",
            tool_name="python",
            tier=ActionTier.T2_GATE,
        )
        gate.approve(request.id, "approver")

        with pytest.raises(ValueError, match="already approved"):
            gate.approve(request.id, "another")

    def test_reject_nonexistent_raises(self, gate):
        with pytest.raises(ValueError, match="not found"):
            gate.reject("nonexistent", "approver")

    def test_get_pending(self, gate, tmp_bus):
        t1 = make_task(tmp_bus)
        t2 = make_task(tmp_bus)
        r1 = gate.park_task(t1.id, "agent", "python", ActionTier.T2_GATE)
        r2 = gate.park_task(t2.id, "agent", "shell", ActionTier.T3_DUAL)

        pending = gate.get_pending()
        assert len(pending) == 2

        gate.approve(r1.id, "approver")
        pending = gate.get_pending()
        assert len(pending) == 1

    def test_get_by_task(self, gate, tmp_bus):
        task = make_task(tmp_bus)
        gate.park_task(task.id, "agent", "python", ActionTier.T2_GATE)

        requests = gate.get_by_task(task.id)
        assert len(requests) == 1
        assert requests[0].task_id == task.id

    def test_check_expired(self, gate, tmp_bus):
        task = make_task(tmp_bus)
        request = gate.park_task(
            task_id=task.id,
            agent_id="agent",
            tool_name="python",
            tier=ActionTier.T2_GATE,
        )

        expired = gate.check_expired()
        assert len(expired) == 0

    def test_memory_recorded_on_park(self, gate, tmp_bus):
        task = make_task(tmp_bus)
        gate.park_task(task.id, "agent", "python", ActionTier.T2_GATE)

        results = gate.memory.recall_context(
            query="Parked for approval",
            agent_id="agent",
        )
        assert len(results) >= 1
        assert any("Parked for approval" in e.content for e in results)
