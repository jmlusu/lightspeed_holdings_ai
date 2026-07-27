import pytest

from lightspeed_agents.memory.models import MemoryEntry


def test_memory_entry_defaults():
    entry = MemoryEntry(content="hello")
    assert entry.id != ""
    assert entry.content == "hello"
    assert entry.access_count == 0
    assert entry.created_at != ""


def test_memory_entry_touch():
    entry = MemoryEntry(content="hello")
    entry.touch()
    assert entry.access_count == 1
    entry.touch()
    assert entry.access_count == 2


def test_memory_entry_unique_ids():
    e1 = MemoryEntry(content="a")
    e2 = MemoryEntry(content="b")
    assert e1.id != e2.id


def test_memory_entry_serialization():
    entry = MemoryEntry(content="test", tags=["a"])
    data = entry.model_dump()
    restored = MemoryEntry(**data)
    assert restored.content == "test"
    assert restored.tags == ["a"]
    assert restored.id == entry.id
