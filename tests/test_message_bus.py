import pytest

from lightspeed_agents.message_bus.message_bus import MessageBus
from lightspeed_agents.message_bus.task_status import TaskStatus, TaskPriority


@pytest.fixture
def bus(tmp_path):
    return MessageBus(str(tmp_path))


def test_send_task(bus):
    task = bus.send_task(
        instruction="deploy API",
        receiver_id="cto",
    )
    assert task.status == TaskStatus.PENDING
    assert task.receiver_id == "cto"
    assert task.instruction == "deploy API"


def test_get_all_tasks(bus):
    bus.send_task(instruction="task 1", receiver_id="cto")
    bus.send_task(instruction="task 2", receiver_id="cfo")
    tasks = bus.get_all_tasks()
    assert len(tasks) == 2


def test_get_task(bus):
    task = bus.send_task(instruction="test", receiver_id="cto")
    found = bus.get_task(task.id)
    assert found is not None
    assert found.id == task.id


def test_get_task_not_found(bus):
    assert bus.get_task("nonexistent") is None


def test_get_pending_tasks_priority_order(bus):
    bus.send_task(instruction="low", receiver_id="cto", priority=TaskPriority.LOW)
    bus.send_task(
        instruction="critical", receiver_id="cto", priority=TaskPriority.CRITICAL
    )
    bus.send_task(instruction="medium", receiver_id="cto", priority=TaskPriority.MEDIUM)
    bus.send_task(instruction="high", receiver_id="cto", priority=TaskPriority.HIGH)

    pending = bus.get_pending_tasks()
    assert pending[0].priority == TaskPriority.CRITICAL
    assert pending[1].priority == TaskPriority.HIGH
    assert pending[2].priority == TaskPriority.MEDIUM
    assert pending[3].priority == TaskPriority.LOW


def test_claim_task(bus):
    task = bus.send_task(instruction="test", receiver_id="cto")
    claimed = bus.claim_task(task.id)
    assert claimed.status == TaskStatus.IN_PROGRESS
    assert claimed.claimed_at != ""


def test_complete_task(bus):
    task = bus.send_task(instruction="test", receiver_id="cto")
    bus.claim_task(task.id)
    completed = bus.complete_task(task.id, result="done")
    assert completed.status == TaskStatus.COMPLETED
    assert completed.result == "done"


def test_fail_task(bus):
    task = bus.send_task(instruction="test", receiver_id="cto")
    bus.claim_task(task.id)
    failed = bus.fail_task(task.id, error="timeout")
    assert failed.status == TaskStatus.FAILED
    assert failed.error == "timeout"


def test_escalate_task(bus):
    task = bus.send_task(instruction="test", receiver_id="cto")
    escalated = bus.escalate_task(task.id)
    assert escalated.status == TaskStatus.ESCALATED


def test_cancel_task(bus):
    task = bus.send_task(instruction="test", receiver_id="cto")
    cancelled = bus.cancel_task(task.id)
    assert cancelled.status == TaskStatus.CANCELLED


def test_approve_task(bus):
    task = bus.send_task(instruction="test", receiver_id="cto")
    bus.park_for_approval(task.id)
    approved = bus.approve_task(task.id)
    assert approved.status == TaskStatus.IN_PROGRESS


def test_park_for_approval(bus):
    task = bus.send_task(instruction="test", receiver_id="cto")
    parked = bus.park_for_approval(task.id)
    assert parked.status == TaskStatus.WAITING_APPROVAL


def test_get_tasks_by_receiver(bus):
    bus.send_task(instruction="t1", receiver_id="cto")
    bus.send_task(instruction="t2", receiver_id="cfo")
    bus.send_task(instruction="t3", receiver_id="cto")

    cto_tasks = bus.get_tasks_by_receiver("cto")
    assert len(cto_tasks) == 2

    cfo_tasks = bus.get_tasks_by_receiver("cfo")
    assert len(cfo_tasks) == 1


def test_get_tasks_by_status(bus):
    bus.send_task(instruction="t1", receiver_id="cto")
    task2 = bus.send_task(instruction="t2", receiver_id="cto")
    bus.claim_task(task2.id)

    pending = bus.get_tasks_by_status(TaskStatus.PENDING)
    assert len(pending) == 1

    in_progress = bus.get_tasks_by_status(TaskStatus.IN_PROGRESS)
    assert len(in_progress) == 1


def test_delegate(bus):
    parent = bus.send_task(instruction="parent task", receiver_id="cto")
    subtask = bus.delegate(
        parent_task_id=parent.id,
        instruction="subtask",
        receiver_id="engineering-manager",
    )
    assert subtask.parent_task_id == parent.id
    assert subtask.receiver_id == "engineering-manager"

    subtasks = bus.get_subtasks(parent.id)
    assert len(subtasks) == 1


def test_broadcast_callback(bus):
    events = []
    bus.set_broadcast_callback(lambda task, event: events.append(event))

    task = bus.send_task(instruction="test", receiver_id="cto")
    assert "task_created" in events

    bus.claim_task(task.id)
    assert "task_claimed" in events


def test_task_lifecycle_full(bus):
    task = bus.send_task(instruction="full lifecycle", receiver_id="cto")
    assert task.status == TaskStatus.PENDING

    task = bus.claim_task(task.id)
    assert task.status == TaskStatus.IN_PROGRESS

    task = bus.complete_task(task.id, result="finished")
    assert task.status == TaskStatus.COMPLETED
    assert task.result == "finished"
