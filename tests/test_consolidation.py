import pytest
from datetime import datetime, timezone, timedelta

from lightspeed_agents.memory.models import MemoryEntry
from lightspeed_agents.memory.filestore import FileStore
from lightspeed_agents.memory.consolidation import (
    ConsolidationScheduler,
    ConsolidationConfig,
)


@pytest.fixture
def store(tmp_path):
    return FileStore(str(tmp_path))


@pytest.fixture
def config():
    return ConsolidationConfig(
        tick_interval=5,
        entry_threshold=5,
        capacity_cap=10,
        age_prune_days=30,
    )


def test_prune_old_episodic(store, config):
    old = MemoryEntry(content="old", memory_type="episodic")
    old.created_at = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    new = MemoryEntry(content="new", memory_type="episodic")

    store.save("episodic.json", [old, new])

    scheduler = ConsolidationScheduler(store, config)
    scheduler.prune("episodic")

    entries = store.load("episodic.json")
    assert len(entries) == 1
    assert entries[0].content == "new"


def test_deduplicate_semantic(store, config):
    entries = [
        MemoryEntry(content="Contract approved", memory_type="semantic"),
        MemoryEntry(content="contract  approved", memory_type="semantic"),
        MemoryEntry(content="Different fact", memory_type="semantic"),
    ]
    store.save("semantic.json", entries)

    scheduler = ConsolidationScheduler(store, config)
    scheduler.consolidate()

    loaded = store.load("semantic.json")
    assert len(loaded) == 2


def test_enforce_cap(store, config):
    entries = []
    for i in range(15):
        e = MemoryEntry(content=f"entry {i}", memory_type="episodic")
        e.access_count = i
        entries.append(e)
    store.save("episodic.json", entries)

    scheduler = ConsolidationScheduler(store, config)
    scheduler.consolidate()

    loaded = store.load("episodic.json")
    assert len(loaded) == 10


def test_aggregate_generation(store, config):
    entries = [
        MemoryEntry(
            content="task done",
            memory_type="episodic",
            agent_id="cto",
            department="engineering",
            tags=["deploy"],
        ),
        MemoryEntry(
            content="knowledge gained",
            memory_type="semantic",
            agent_id="cfo",
            department="finance",
            tags=["finance"],
        ),
    ]
    store.save("episodic.json", [entries[0]])
    store.save("semantic.json", [entries[1]])

    scheduler = ConsolidationScheduler(store, config)
    scheduler.consolidate()

    aggregates = store.load("aggregate.json")
    assert len(aggregates) > 0
    tag_agg = [a for a in aggregates if "tags" in a.tags]
    assert len(tag_agg) > 0


def test_tick_trigger(store, config):
    config.tick_interval = 2
    scheduler = ConsolidationScheduler(store, config)

    store.save(
        "episodic.json",
        [
            MemoryEntry(content="a", memory_type="episodic"),
        ],
    )

    scheduler.on_tick()
    entries = store.load("episodic.json")
    assert len(entries) == 1

    scheduler.on_tick()
    entries = store.load("episodic.json")
    assert len(entries) == 1


def test_prune_all(store, config):
    old = MemoryEntry(content="old", memory_type="episodic")
    old.created_at = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    store.save("episodic.json", [old])

    scheduler = ConsolidationScheduler(store, config)
    scheduler.prune()

    assert len(store.load("episodic.json")) == 0
