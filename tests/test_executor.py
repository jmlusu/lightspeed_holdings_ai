import pytest

from lightspeed_agents.message_bus.message_bus import MessageBus
from lightspeed_agents.message_bus.executor import Executor
from lightspeed_agents.memory.engine import MemoryEngine
from lightspeed_agents.message_bus.task_status import TaskStatus


@pytest.fixture
def setup(tmp_path):
    bus = MessageBus(str(tmp_path))
    memory = MemoryEngine(str(tmp_path / "memory"))
    executor = Executor(bus=bus, memory=memory)
    return bus, memory, executor


def test_tick_processes_pending(setup):
    bus, memory, executor = setup
    bus.send_task(instruction="test task", receiver_id="cto")

    processed = executor.tick()
    assert len(processed) == 1
    assert processed[0].status == TaskStatus.COMPLETED


def test_tick_with_executor_fn(setup):
    bus, memory, executor = setup

    def run_task(task):
        return f"Result for {task.instruction}"

    executor.agent_runner_fn = run_task
    bus.send_task(instruction="deploy API", receiver_id="cto")

    processed = executor.tick()
    assert len(processed) == 1
    assert processed[0].status == TaskStatus.COMPLETED
    assert "Result for" in processed[0].result


def test_tick_records_to_memory(setup):
    bus, memory, executor = setup
    bus.send_task(instruction="deploy API", receiver_id="cto")

    executor.tick()

    entries = memory.get_entries("episodic")
    assert len(entries) > 0


def test_tick_records_to_audit(setup):
    bus, memory, executor = setup
    bus.send_task(instruction="test", receiver_id="cto")

    executor.tick()

    entries = executor.audit.get_entries()
    assert len(entries) >= 2


def test_tick_handles_executor_error(setup):
    bus, memory, executor = setup

    def fail_task(task):
        raise RuntimeError("LLM timeout")

    executor.agent_runner_fn = fail_task
    bus.send_task(instruction="test", receiver_id="cto")

    processed = executor.tick()
    assert len(processed) == 1
    assert processed[0].status == TaskStatus.FAILED
    assert "LLM timeout" in processed[0].error


def test_tick_empty_queue(setup):
    bus, memory, executor = setup
    processed = executor.tick()
    assert len(processed) == 0


def test_tick_multiple_tasks(setup):
    bus, memory, executor = setup
    bus.send_task(instruction="task 1", receiver_id="cto")
    bus.send_task(instruction="task 2", receiver_id="cfo")

    processed = executor.tick()
    assert len(processed) == 2


def test_executor_run_loop_max_ticks(setup):
    bus, memory, executor = setup
    bus.send_task(instruction="task 1", receiver_id="cto")
    bus.send_task(instruction="task 2", receiver_id="cfo")

    executor.run_loop(max_ticks=2)
    all_tasks = bus.get_all_tasks()
    for task in all_tasks:
        assert task.status == TaskStatus.COMPLETED
