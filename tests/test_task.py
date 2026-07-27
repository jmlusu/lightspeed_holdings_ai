import pytest

from lightspeed_agents.message_bus.task import Task
from lightspeed_agents.message_bus.task_status import TaskStatus, TaskPriority


def test_task_defaults():
    task = Task(instruction="do something")
    assert task.id != ""
    assert task.instruction == "do something"
    assert task.status == TaskStatus.PENDING
    assert task.priority == TaskPriority.MEDIUM
    assert task.created_at != ""
    assert task.updated_at != ""


def test_task_with_fields():
    task = Task(
        instruction="deploy",
        assignee="cto",
        sender_id="ceo",
        receiver_id="cto",
        priority=TaskPriority.HIGH,
        tags=["deploy"],
    )
    assert task.assignee == "cto"
    assert task.priority == TaskPriority.HIGH
    assert task.tags == ["deploy"]


def test_task_is_terminal():
    task = Task(instruction="test")
    assert task.is_terminal is False
    task.status = TaskStatus.COMPLETED
    assert task.is_terminal is True
    task.status = TaskStatus.FAILED
    assert task.is_terminal is True
    task.status = TaskStatus.CANCELLED
    assert task.is_terminal is True
    task.status = TaskStatus.DELETED
    assert task.is_terminal is True


def test_task_touch():
    task = Task(instruction="test")
    old = task.updated_at
    task.touch()
    assert task.updated_at >= old


def test_task_kebab_receiver_validation():
    with pytest.raises(ValueError, match="kebab-case"):
        Task(instruction="test", receiver_id="Not Valid")


def test_task_valid_kebab_receiver():
    task = Task(instruction="test", receiver_id="financial-analyst")
    assert task.receiver_id == "financial-analyst"


def test_task_unique_ids():
    t1 = Task(instruction="a")
    t2 = Task(instruction="b")
    assert t1.id != t2.id


def test_task_correlation_id():
    task = Task(instruction="test")
    assert task.correlation_id != ""
    assert len(task.correlation_id) == 36


def test_task_serialization():
    task = Task(instruction="test", tags=["a"])
    data = task.model_dump(mode="json")
    restored = Task(**data)
    assert restored.instruction == "test"
    assert restored.id == task.id
