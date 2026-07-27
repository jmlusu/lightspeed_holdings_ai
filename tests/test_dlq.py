import pytest
from datetime import datetime, timezone, timedelta

from lightspeed_agents.message_bus.message_bus import MessageBus
from lightspeed_agents.message_bus.dead_letter import DeadLetterQueue
from lightspeed_agents.message_bus.task_status import TaskStatus


@pytest.fixture
def bus(tmp_path):
    return MessageBus(str(tmp_path))


@pytest.fixture
def dlq(bus):
    return DeadLetterQueue(bus, stale_minutes=30)


def test_no_stale_tasks(bus, dlq):
    task = bus.send_task(instruction="test", receiver_id="cto")
    assert dlq.detect_stale_tasks() == []


def test_detect_stale_tasks(bus, dlq):
    task = bus.send_task(instruction="stale", receiver_id="cto")
    bus.claim_task(task.id)

    bus.store.update_entry(
        "inbox.json",
        task.id,
        {"claimed_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()},
    )

    stale = dlq.detect_stale_tasks()
    assert len(stale) == 1
    assert stale[0].id == task.id


def test_move_to_dlq(bus, dlq):
    task = bus.send_task(instruction="stale", receiver_id="cto")
    bus.claim_task(task.id)

    bus.store.update_entry(
        "inbox.json",
        task.id,
        {"claimed_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()},
    )

    dlq.move_to_dlq(task)
    updated = bus.get_task(task.id)
    assert updated.status == TaskStatus.FAILED
    assert "Stale" in updated.error


def test_process_finds_and_fails_stale(bus, dlq):
    task = bus.send_task(instruction="stale", receiver_id="cto")
    bus.claim_task(task.id)

    bus.store.update_entry(
        "inbox.json",
        task.id,
        {"claimed_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()},
    )

    stale = dlq.process()
    assert len(stale) == 1

    updated = bus.get_task(task.id)
    assert updated.status == TaskStatus.FAILED


def test_dlq_tasks(bus, dlq):
    task = bus.send_task(instruction="fail", receiver_id="cto")
    bus.fail_task(task.id, error="test")

    dlq_tasks = dlq.get_dlq_tasks()
    assert len(dlq_tasks) == 1
