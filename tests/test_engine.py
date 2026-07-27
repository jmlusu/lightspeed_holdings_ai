import pytest

from lightspeed_agents.memory.engine import MemoryEngine
from lightspeed_agents.memory.consolidation import ConsolidationConfig


@pytest.fixture
def engine(tmp_path):
    config = ConsolidationConfig(tick_interval=100)
    return MemoryEngine(str(tmp_path), config)


def test_record_task_outcome(engine):
    entry = engine.record_task_outcome(
        task_id="t-001",
        agent_id="cto",
        content="Deployed API",
        status="completed",
        department="engineering",
        tags=["deploy"],
    )
    assert entry.memory_type == "episodic"
    assert entry.task_id == "t-001"

    entries = engine.get_entries("episodic")
    assert len(entries) == 1
    assert entries[0].content == "Deployed API"


def test_record_knowledge(engine):
    entry = engine.record_knowledge(
        content="Contract approved",
        agent_id="cfo",
        tags=["contract"],
    )
    assert entry.memory_type == "semantic"

    entries = engine.get_entries("semantic")
    assert len(entries) == 1


def test_record_procedure(engine):
    entry = engine.record_procedure(
        content="Step 1: Build, Step 2: Test",
        agent_id="cto",
    )
    assert entry.memory_type == "procedural"
    assert len(engine.get_entries("procedural")) == 1


def test_record_relationship(engine):
    entry = engine.record_relationship(
        content="CTO reports to CEO",
        agent_id="cto",
    )
    assert entry.memory_type == "relational"
    assert len(engine.get_entries("relational")) == 1


def test_record_temporal(engine):
    entry = engine.record_temporal(
        content="Meeting at 3pm",
        agent_id="coo",
    )
    assert entry.memory_type == "temporal"
    assert len(engine.get_entries("temporal")) == 1


def test_recall_context(engine):
    engine.record_task_outcome(
        task_id="t-001", agent_id="cto",
        content="Deployed authentication API to staging",
    )
    engine.record_knowledge(
        content="Database migration completed",
        agent_id="cto",
    )

    results = engine.recall_context("deployed", agent_id="cto")
    assert len(results) > 0
    assert any("deploy" in e.content.lower() for e in results)


def test_recall_increments_access(engine):
    entry = engine.record_knowledge(
        content="Important fact about deployment",
    )
    assert entry.access_count == 0

    engine.recall_context("deployment")

    entries = engine.get_entries("semantic")
    assert entries[0].access_count > 0


def test_search_across_types(engine):
    engine.record_task_outcome(
        task_id="t-001", agent_id="cto",
        content="Deployed API",
    )
    engine.record_knowledge(
        content="API documentation updated",
        agent_id="cto",
    )

    results = engine.search("API")
    assert len(results) == 2


def test_get_stats(engine):
    engine.record_task_outcome(
        task_id="t-001", agent_id="cto",
        content="task done",
    )
    engine.record_knowledge(
        content="knowledge",
        agent_id="cto",
    )

    stats = engine.get_stats()
    assert stats["episodic"] == 1
    assert stats["semantic"] == 1
    assert stats["total"] == 2


def test_clear_type(engine):
    engine.record_task_outcome(
        task_id="t-001", agent_id="cto", content="task",
    )
    engine.record_knowledge(content="knowledge")

    engine.clear("episodic")
    assert len(engine.get_entries("episodic")) == 0
    assert len(engine.get_entries("semantic")) == 1


def test_clear_all(engine):
    engine.record_task_outcome(
        task_id="t-001", agent_id="cto", content="task",
    )
    engine.record_knowledge(content="knowledge")

    engine.clear()
    stats = engine.get_stats()
    assert stats["total"] == 0


def test_consolidate(engine):
    for i in range(3):
        engine.record_task_outcome(
            task_id=f"t-{i}", agent_id="cto",
            content=f"task {i}",
        )

    engine.consolidate()
    entries = engine.get_entries("episodic")
    assert len(entries) == 3
