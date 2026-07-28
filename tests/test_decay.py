"""
Tests for temporal decay functionality in memory consolidation.
"""

import pytest
from datetime import datetime, UTC, timedelta
from lightspeed_agents.memory.models import MemoryEntry
from lightspeed_agents.memory.decay import (
    DecayFunction,
    DecayConfig,
    DEFAULT_DECAY_CONFIG,
    calculate_age_days,
    get_half_life,
    calculate_decay_factor,
    calculate_decayed_importance,
    apply_decay_to_entry,
    apply_decay_to_entries,
    should_prune_by_decay,
)


class TestDecayConfig:
    def test_default_config(self):
        config = DecayConfig()
        assert config.function == DecayFunction.EXPONENTIAL
        assert config.min_importance == 0.01
        # no_decay_threshold is now > 1.0 so all memories can decay
        assert config.no_decay_threshold == 1.01
        assert config.initial_importance == 1.0
        assert "episodic" in config.half_life_days
        assert "semantic" in config.half_life_days

    def test_custom_config(self):
        config = DecayConfig(
            function=DecayFunction.LINEAR,
            half_life_days={"episodic": 3.0, "semantic": 30.0},
            min_importance=0.05,
            no_decay_threshold=0.8,
            initial_importance=1.0,
        )
        assert config.function == DecayFunction.LINEAR
        assert config.half_life_days["episodic"] == 3.0
        assert config.half_life_days["semantic"] == 30.0
        assert config.min_importance == 0.05
        assert config.no_decay_threshold == 0.8


class TestCalculateAgeDays:
    def test_new_entry(self):
        entry = MemoryEntry(content="new")
        age = calculate_age_days(entry)
        assert age < 0.01  # Less than a minute old

    def test_old_entry(self):
        entry = MemoryEntry(content="old")
        entry.created_at = (datetime.now(UTC) - timedelta(days=10)).isoformat()
        age = calculate_age_days(entry)
        assert 9.9 < age < 10.1

    def test_very_old_entry(self):
        entry = MemoryEntry(content="ancient")
        entry.created_at = (datetime.now(UTC) - timedelta(days=100)).isoformat()
        age = calculate_age_days(entry)
        assert 99.9 < age < 100.1


class TestGetHalfLife:
    def test_known_types(self):
        config = DEFAULT_DECAY_CONFIG
        assert get_half_life("episodic", config) == 7.0
        assert get_half_life("semantic", config) == 90.0
        assert get_half_life("procedural", config) == 180.0
        assert get_half_life("relational", config) == 60.0
        assert get_half_life("temporal", config) == 30.0
        assert get_half_life("aggregate", config) == 365.0

    def test_unknown_type_defaults_to_episodic(self):
        config = DEFAULT_DECAY_CONFIG
        assert get_half_life("unknown_type", config) == 7.0


class TestCalculateDecayFactor:
    def test_no_decay_above_threshold(self):
        entry = MemoryEntry(content="important")
        entry.metadata["importance_score"] = 0.95
        factor = calculate_decay_factor(entry, DEFAULT_DECAY_CONFIG)
        assert factor == 1.0

    def test_exponential_decay_episodic(self):
        config = DecayConfig(
            function=DecayFunction.EXPONENTIAL,
            half_life_days={"episodic": 7.0},
        )
        entry = MemoryEntry(content="test", memory_type="episodic")
        entry.created_at = (datetime.now(UTC) - timedelta(days=7)).isoformat()
        factor = calculate_decay_factor(entry, config)
        # After one half-life, factor should be ~0.5
        assert 0.49 < factor < 0.51

    def test_exponential_decay_semantic(self):
        config = DecayConfig(
            function=DecayFunction.EXPONENTIAL,
            half_life_days={"semantic": 90.0},
        )
        entry = MemoryEntry(content="test", memory_type="semantic")
        entry.created_at = (datetime.now(UTC) - timedelta(days=90)).isoformat()
        factor = calculate_decay_factor(entry, config)
        # After one half-life, factor should be ~0.5
        assert 0.49 < factor < 0.51

    def test_linear_decay(self):
        config = DecayConfig(
            function=DecayFunction.LINEAR,
            half_life_days={"episodic": 10.0},
        )
        entry = MemoryEntry(content="test", memory_type="episodic")
        entry.created_at = (datetime.now(UTC) - timedelta(days=10)).isoformat()
        factor = calculate_decay_factor(entry, config)
        # After half_life days, linear decay factor = 1 - 10/(2*10) = 0.5
        assert 0.49 < factor < 0.51

    def test_step_decay(self):
        config = DecayConfig(
            function=DecayFunction.STEP,
            half_life_days={"episodic": 7.0},
        )
        entry = MemoryEntry(content="test", memory_type="episodic")
        entry.created_at = (datetime.now(UTC) - timedelta(days=21)).isoformat()  # 3 half-lives
        factor = calculate_decay_factor(entry, config)
        # 3 steps of half-life: 0.5^3 = 0.125
        assert abs(factor - 0.125) < 0.01

    def test_min_importance_floor(self):
        config = DecayConfig(
            function=DecayFunction.EXPONENTIAL,
            half_life_days={"episodic": 1.0},
            min_importance=0.1,
            initial_importance=1.0,
        )
        entry = MemoryEntry(content="test", memory_type="episodic")
        entry.created_at = (datetime.now(UTC) - timedelta(days=100)).isoformat()
        factor = calculate_decay_factor(entry, config)
        # Should not go below min_importance / initial_importance = 0.1
        assert factor >= 0.1


class TestCalculateDecayedImportance:
    def test_no_decay_above_threshold(self):
        entry = MemoryEntry(content="important")
        entry.importance_score = 1.0  # At max, above threshold
        importance = calculate_decayed_importance(entry, DEFAULT_DECAY_CONFIG)
        assert importance == 1.0

    def test_decay_applied(self):
        config = DecayConfig(
            function=DecayFunction.EXPONENTIAL,
            half_life_days={"episodic": 7.0},
            initial_importance=1.0,
        )
        entry = MemoryEntry(content="test", memory_type="episodic")
        entry.metadata["importance_score"] = 1.0
        entry.created_at = (datetime.now(UTC) - timedelta(days=7)).isoformat()
        importance = calculate_decayed_importance(entry, config)
        assert 0.49 < importance < 0.51

    def test_min_importance_floor(self):
        config = DecayConfig(
            function=DecayFunction.EXPONENTIAL,
            half_life_days={"episodic": 1.0},
            min_importance=0.05,
            initial_importance=1.0,
        )
        entry = MemoryEntry(content="test", memory_type="episodic")
        entry.metadata["importance_score"] = 1.0
        entry.created_at = (datetime.now(UTC) - timedelta(days=100)).isoformat()
        importance = calculate_decayed_importance(entry, config)
        assert importance == 0.05


class TestApplyDecayToEntry:
    def test_creates_new_entry_with_updated_metadata(self):
        config = DecayConfig(
            function=DecayFunction.EXPONENTIAL,
            half_life_days={"episodic": 7.0},
        )
        entry = MemoryEntry(content="test", memory_type="episodic")
        entry.importance_score = 1.0
        entry.created_at = (datetime.now(UTC) - timedelta(days=7)).isoformat()

        updated = apply_decay_to_entry(entry, config)

        assert updated.id == entry.id
        assert updated.content == entry.content
        assert updated.memory_type == entry.memory_type
        assert "decay_factor" in updated.metadata
        assert "last_decay_applied" in updated.metadata
        assert updated.metadata["importance_score"] < 1.0

    def test_preserves_original_entry(self):
        config = DEFAULT_DECAY_CONFIG
        entry = MemoryEntry(content="test", memory_type="episodic")
        entry.importance_score = 1.0
        entry.created_at = (datetime.now(UTC) - timedelta(days=30)).isoformat()  # Old entry
        original_importance = entry.importance_score
        original_updated_at = entry.updated_at

        updated = apply_decay_to_entry(entry, config)

        # Original entry unchanged
        assert entry.importance_score == original_importance
        assert entry.updated_at == original_updated_at
        # Updated entry has decay applied
        assert updated.importance_score < original_importance


class TestApplyDecayToEntries:
    def test_applies_to_multiple_entries(self):
        config = DecayConfig(
            function=DecayFunction.EXPONENTIAL,
            half_life_days={"episodic": 7.0, "semantic": 90.0},
        )
        entries = [
            MemoryEntry(content="epi1", memory_type="episodic", metadata={"importance_score": 1.0}),
            MemoryEntry(content="epi2", memory_type="episodic", metadata={"importance_score": 0.5}),
            MemoryEntry(content="sem1", memory_type="semantic", metadata={"importance_score": 1.0}),
        ]
        # Make episodic entries old
        for e in entries[:2]:
            e.created_at = (datetime.now(UTC) - timedelta(days=14)).isoformat()
        # Semantic entry new
        entries[2].created_at = datetime.now(UTC).isoformat()

        updated = apply_decay_to_entries(entries, config)

        assert len(updated) == 3
        # Episodic should have decayed more
        assert updated[0].metadata["importance_score"] < 0.5
        assert updated[1].metadata["importance_score"] < 0.5
        # Semantic should have minimal decay (new)
        assert updated[2].metadata["importance_score"] > 0.9


class TestShouldPruneByDecay:
    def test_prunes_low_importance(self):
        config = DecayConfig(
            function=DecayFunction.EXPONENTIAL,
            half_life_days={"episodic": 1.0},
        )
        entry = MemoryEntry(content="test", memory_type="episodic")
        entry.metadata["importance_score"] = 1.0
        entry.created_at = (datetime.now(UTC) - timedelta(days=10)).isoformat()

        should_prune = should_prune_by_decay(entry, config, prune_threshold=0.1)
        assert should_prune is True

    def test_keeps_high_importance(self):
        config = DecayConfig(
            function=DecayFunction.EXPONENTIAL,
            half_life_days={"episodic": 7.0},
        )
        entry = MemoryEntry(content="test", memory_type="episodic")
        entry.metadata["importance_score"] = 1.0
        entry.created_at = (datetime.now(UTC) - timedelta(days=7)).isoformat()

        should_prune = should_prune_by_decay(entry, config, prune_threshold=0.1)
        assert should_prune is False

    def test_no_prune_above_threshold(self):
        entry = MemoryEntry(content="important")
        entry.metadata["importance_score"] = 0.95
        should_prune = should_prune_by_decay(entry, DEFAULT_DECAY_CONFIG, prune_threshold=0.05)
        assert should_prune is False


class TestMemoryEntryImportanceMethods:
    def test_get_importance_default(self):
        entry = MemoryEntry(content="test")
        assert entry.get_importance() == 1.0

    def test_get_importance_custom(self):
        entry = MemoryEntry(content="test", metadata={"importance_score": 0.75})
        assert entry.get_importance() == 0.75

    def test_set_importance(self):
        entry = MemoryEntry(content="test")
        entry.set_importance(0.8)
        assert entry.get_importance() == 0.8

    def test_set_importance_clamped(self):
        entry = MemoryEntry(content="test")
        entry.set_importance(1.5)
        assert entry.get_importance() == 1.0
        entry.set_importance(-0.5)
        assert entry.get_importance() == 0.0


class TestDifferentDecayRatesPerMemoryType:
    def test_episodic_decays_faster_than_semantic(self):
        config = DEFAULT_DECAY_CONFIG
        age_days = 14

        epi_entry = MemoryEntry(content="epi", memory_type="episodic", metadata={"importance_score": 1.0})
        epi_entry.created_at = (datetime.now(UTC) - timedelta(days=age_days)).isoformat()

        sem_entry = MemoryEntry(content="sem", memory_type="semantic", metadata={"importance_score": 1.0})
        sem_entry.created_at = (datetime.now(UTC) - timedelta(days=age_days)).isoformat()

        epi_importance = calculate_decayed_importance(epi_entry, config)
        sem_importance = calculate_decayed_importance(sem_entry, config)

        # Episodic should decay more (lower importance)
        assert epi_importance < sem_importance

    def test_procedural_decays_slowest(self):
        config = DEFAULT_DECAY_CONFIG
        age_days = 30

        proc_entry = MemoryEntry(content="proc", memory_type="procedural", metadata={"importance_score": 1.0})
        proc_entry.created_at = (datetime.now(UTC) - timedelta(days=age_days)).isoformat()

        epi_entry = MemoryEntry(content="epi", memory_type="episodic", metadata={"importance_score": 1.0})
        epi_entry.created_at = (datetime.now(UTC) - timedelta(days=age_days)).isoformat()

        proc_importance = calculate_decayed_importance(proc_entry, config)
        epi_importance = calculate_decayed_importance(epi_entry, config)

        # Procedural should decay less (higher importance)
        assert proc_importance > epi_importance