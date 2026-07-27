from datetime import datetime, timezone, timedelta

from lightspeed_agents.memory.models import MemoryEntry


def test_entry_defaults():
    entry = MemoryEntry(content="test content")
    assert entry.id != ""
    assert entry.content == "test content"
    assert entry.memory_type == "episodic"
    assert entry.access_count == 0
    assert entry.created_at != ""
    assert entry.updated_at != ""


def test_entry_custom_fields():
    entry = MemoryEntry(
        content="knowledge",
        memory_type="semantic",
        agent_id="cto",
        task_id="t-001",
        department="engineering",
        tags=["test", "knowledge"],
    )
    assert entry.memory_type == "semantic"
    assert entry.agent_id == "cto"
    assert entry.tags == ["test", "knowledge"]


def test_entry_touch():
    entry = MemoryEntry(content="test")
    assert entry.access_count == 0
    entry.touch()
    assert entry.access_count == 1
    entry.touch()
    assert entry.access_count == 2


def test_entry_is_older_than_days():
    entry = MemoryEntry(content="old")
    entry.created_at = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
    assert entry.is_older_than_days(90) is True
    assert entry.is_older_than_days(101) is False


def test_entry_is_not_old():
    entry = MemoryEntry(content="new")
    assert entry.is_older_than_days(90) is False


def test_entry_unique_ids():
    e1 = MemoryEntry(content="a")
    e2 = MemoryEntry(content="b")
    assert e1.id != e2.id


def test_entry_serialization():
    entry = MemoryEntry(content="test", tags=["a"])
    data = entry.model_dump()
    restored = MemoryEntry(**data)
    assert restored.content == "test"
    assert restored.tags == ["a"]
    assert restored.id == entry.id
