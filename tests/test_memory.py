import json
import pytest

from lightspeed_agents.memory.memory import MemoryEntry, AgentMemory


def test_memory_entry_defaults():
    entry = MemoryEntry(role="user", content="hello")
    assert entry.role == "user"
    assert entry.content == "hello"
    assert entry.timestamp != ""


def test_memory_entry_with_timestamp():
    entry = MemoryEntry(role="user", content="hi", timestamp="2025-01-01T00:00:00")
    assert entry.timestamp == "2025-01-01T00:00:00"


def test_agent_memory_add(tmp_path):
    mem = AgentMemory("test-agent", str(tmp_path))
    mem.add("user", "hello")
    mem.add("assistant", "hi there")

    entries = mem.get_history()
    assert len(entries) == 2
    assert entries[0].role == "user"
    assert entries[1].role == "assistant"


def test_agent_memory_persistence(tmp_path):
    mem = AgentMemory("test-agent", str(tmp_path))
    mem.add("user", "hello")
    mem.add("assistant", "hi")

    mem2 = AgentMemory("test-agent", str(tmp_path))
    entries = mem2.get_history()
    assert len(entries) == 2
    assert entries[0].content == "hello"


def test_agent_memory_limit(tmp_path):
    mem = AgentMemory("test-agent", str(tmp_path))
    for i in range(5):
        mem.add("user", f"msg {i}")

    limited = mem.get_history(limit=2)
    assert len(limited) == 2
    assert limited[0].content == "msg 3"
    assert limited[1].content == "msg 4"


def test_agent_memory_context(tmp_path):
    mem = AgentMemory("test-agent", str(tmp_path))
    mem.add("user", "hello")
    mem.add("assistant", "hi there")

    context = mem.get_context()
    assert "user: hello" in context
    assert "assistant: hi there" in context


def test_agent_memory_context_empty(tmp_path):
    mem = AgentMemory("test-agent", str(tmp_path))
    assert mem.get_context() == ""


def test_agent_memory_clear(tmp_path):
    mem = AgentMemory("test-agent", str(tmp_path))
    mem.add("user", "hello")
    mem.clear()
    assert mem.get_history() == []


def test_agent_memory_file_created(tmp_path):
    mem = AgentMemory("test-agent", str(tmp_path))
    mem.add("user", "hello")
    assert (tmp_path / "test-agent.json").exists()


def test_agent_memory_empty_when_no_file(tmp_path):
    mem = AgentMemory("nonexistent", str(tmp_path))
    assert mem.get_history() == []
