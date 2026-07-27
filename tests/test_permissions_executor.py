import pytest
from lightspeed_agents.message_bus.message_bus import MessageBus
from lightspeed_agents.message_bus.task_status import TaskStatus, TaskPriority
from lightspeed_agents.memory.engine import MemoryEngine
from lightspeed_agents.message_bus.audit import AuditStore
from lightspeed_agents.message_bus.executor import Executor
from lightspeed_agents.models.agent import Agent
from lightspeed_agents.permissions.checker import PermissionChecker
from lightspeed_agents.permissions.hitl_gate import HITLGate
from lightspeed_agents.permissions.tiers import ActionTier
from lightspeed_agents.registry.registry import AgentRegistry


@pytest.fixture
def tmp_bus(tmp_path):
    return MessageBus(bus_dir=str(tmp_path))


@pytest.fixture
def tmp_memory(tmp_path):
    return MemoryEngine(memory_dir=str(tmp_path))


@pytest.fixture
def tmp_audit(tmp_path):
    return AuditStore(directory=str(tmp_path))


def make_agent(**kwargs):
    defaults = {
        "id": "test-agent",
        "name": "Test Agent",
        "role": "tester",
        "type": "Specialist",
        "tools": ["read", "python"],
        "permissions": ["read", "edit"],
    }
    defaults.update(kwargs)
    return Agent(**defaults)


def make_task(bus, **kwargs):
    defaults = {
        "instruction": "Test task",
        "receiver_id": "test-agent",
        "priority": TaskPriority.MEDIUM,
    }
    defaults.update(kwargs)
    return bus.send_task(**defaults)


class TestExecutorPermissions:

    def test_auto_tier_no_approval_needed(self, tmp_bus, tmp_memory, tmp_audit):
        agent = make_agent(tools=["read"], permissions=["read"])
        registry = AgentRegistry()
        registry.register(agent)

        checker = PermissionChecker()
        gate = HITLGate(tmp_bus, tmp_memory, bus_dir=tmp_bus.store.directory)

        executor = Executor(
            bus=tmp_bus,
            memory=tmp_memory,
            audit=tmp_audit,
            permission_checker=checker,
            hitl_gate=gate,
            agent_lookup_fn=registry.find,
        )

        task = make_task(tmp_bus, receiver_id="test-agent", metadata={"tool": "read"})

        result = executor.tick()
        assert len(result) == 1
        assert result[0].status == TaskStatus.COMPLETED

    def test_tier2_parked_for_approval(self, tmp_bus, tmp_memory, tmp_audit):
        agent = make_agent(tools=["python"], permissions=["read", "edit"])
        registry = AgentRegistry()
        registry.register(agent)

        checker = PermissionChecker()
        gate = HITLGate(tmp_bus, tmp_memory, bus_dir=tmp_bus.store.directory)

        executor = Executor(
            bus=tmp_bus,
            memory=tmp_memory,
            audit=tmp_audit,
            permission_checker=checker,
            hitl_gate=gate,
            agent_lookup_fn=registry.find,
        )

        task = make_task(tmp_bus, receiver_id="test-agent", metadata={"tool": "python"})

        result = executor.tick()
        assert len(result) == 1
        assert result[0].status == TaskStatus.WAITING_APPROVAL

        pending = gate.get_pending()
        assert len(pending) == 1
        assert pending[0].tool_name == "python"

    def test_permission_denied(self, tmp_bus, tmp_memory, tmp_audit):
        agent = make_agent(tools=["read"], permissions=["read"])
        registry = AgentRegistry()
        registry.register(agent)

        checker = PermissionChecker()
        gate = HITLGate(tmp_bus, tmp_memory, bus_dir=tmp_bus.store.directory)

        executor = Executor(
            bus=tmp_bus,
            memory=tmp_memory,
            audit=tmp_audit,
            permission_checker=checker,
            hitl_gate=gate,
            agent_lookup_fn=registry.find,
        )

        task = make_task(tmp_bus, receiver_id="test-agent", metadata={"tool": "shell"})

        result = executor.tick()
        assert len(result) == 1
        assert result[0].status == TaskStatus.FAILED
        assert "does not have access" in result[0].error

    def test_no_agent_lookup_still_executes(self, tmp_bus, tmp_memory, tmp_audit):
        executor = Executor(
            bus=tmp_bus,
            memory=tmp_memory,
            audit=tmp_audit,
            agent_lookup_fn=None,
        )

        task = make_task(tmp_bus, receiver_id="test-agent")
        result = executor.tick()
        assert len(result) == 1
        assert result[0].status == TaskStatus.COMPLETED

    def test_approval_unblocks_task(self, tmp_bus, tmp_memory, tmp_audit):
        agent = make_agent(tools=["python"], permissions=["read", "edit"])
        registry = AgentRegistry()
        registry.register(agent)

        checker = PermissionChecker()
        gate = HITLGate(tmp_bus, tmp_memory, bus_dir=tmp_bus.store.directory)

        executor = Executor(
            bus=tmp_bus,
            memory=tmp_memory,
            audit=tmp_audit,
            permission_checker=checker,
            hitl_gate=gate,
            agent_lookup_fn=registry.find,
        )

        task = make_task(tmp_bus, receiver_id="test-agent", metadata={"tool": "python"})

        executor.tick()
        task = tmp_bus.get_task(task.id)
        assert task.status == TaskStatus.WAITING_APPROVAL

        pending = gate.get_pending()
        gate.approve(pending[0].id, "human-ceo", "Approved")

        task = tmp_bus.get_task(task.id)
        assert task.status == TaskStatus.IN_PROGRESS

    def test_tier2_in_metadata(self, tmp_bus, tmp_memory, tmp_audit):
        agent = make_agent(tools=["python"], permissions=["read", "edit"])
        registry = AgentRegistry()
        registry.register(agent)

        checker = PermissionChecker()
        gate = HITLGate(tmp_bus, tmp_memory, bus_dir=tmp_bus.store.directory)

        executor = Executor(
            bus=tmp_bus,
            memory=tmp_memory,
            audit=tmp_audit,
            permission_checker=checker,
            hitl_gate=gate,
            agent_lookup_fn=registry.find,
        )

        task = make_task(
            tmp_bus, receiver_id="test-agent", metadata={"tool_name": "python"}
        )

        result = executor.tick()
        assert result[0].status == TaskStatus.WAITING_APPROVAL
