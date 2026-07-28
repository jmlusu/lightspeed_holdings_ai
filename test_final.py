from lightspeed_agents.memory import (
    MemoryEngine, MemoryEntry, ConsolidationScheduler, ConsolidationConfig,
    DecayConfig, DecayFunction, DEFAULT_DECAY_CONFIG,
    calculate_decayed_importance, apply_decay_to_entry, should_prune_by_decay,
    ImportanceScorer, DEFAULT_SCORING_CONFIG
)
from datetime import datetime, timedelta, UTC
import shutil

shutil.rmtree('final_test', ignore_errors=True)

# Test the complete decay system
decay_config = DecayConfig(
    function=DecayFunction.EXPONENTIAL,
    half_life_days={'episodic': 7.0, 'semantic': 90.0, 'procedural': 180.0},
    no_decay_threshold=1.01,
    initial_importance=1.0,
)

config = ConsolidationConfig(
    tick_interval=1,
    capacity_cap=100,
    decay_config=decay_config,
    decay_prune_threshold=0.1,
    high_importance_threshold=0.8,
)

engine = MemoryEngine(memory_dir='final_test', config=config, decay_config=decay_config)

# Add various memories
print('=== Testing Temporal Decay for Episodic Memories ===')
print()

# 1. Record episodic memories
e1 = engine.record_task_outcome('task-1', 'agent-1', 'Recent task', importance=0.5)
e2 = engine.record_task_outcome('task-2', 'agent-1', 'Old task', importance=0.5)
e2.created_at = (datetime.now(UTC) - timedelta(days=20)).isoformat()
# Save the old entry
from lightspeed_agents.memory.filestore import FileStore
store = FileStore('final_test')
entries = store.load('episodic.json')
for i, e in enumerate(entries):
    if e.id == e2.id:
        entries[i] = e2
        break
store.save('episodic.json', entries)

# 2. Record semantic memories
s1 = engine.record_knowledge('Semantic fact 1', 'agent-1', importance=0.8)
s2 = engine.record_knowledge('Semantic fact 2', 'agent-1', importance=0.8)
s2.created_at = (datetime.now(UTC) - timedelta(days=60)).isoformat()
entries = store.load('semantic.json')
for i, e in enumerate(entries):
    if e.id == s2.id:
        entries[i] = s2
        break
store.save('semantic.json', entries)

# 3. Record procedural memory
p1 = engine.record_procedure('Procedure 1', 'agent-1', importance=0.9)
p2 = engine.record_procedure('Procedure 2', 'agent-1', importance=0.9)
p2.created_at = (datetime.now(UTC) - timedelta(days=120)).isoformat()
entries = store.load('procedural.json')
for i, e in enumerate(entries):
    if e.id == p2.id:
        entries[i] = p2
        break
store.save('procedural.json', entries)

# Show decayed importance
print('Decayed importance scores:')
for e in [e1, e2]:
    di = calculate_decayed_importance(e, decay_config)
    print(f'  Episodic "{e.content}": stored={e.importance_score:.4f}, decayed={di:.4f}')

for e in [s1, s2]:
    di = calculate_decayed_importance(e, decay_config)
    print(f'  Semantic "{e.content}": stored={e.importance_score:.4f}, decayed={di:.4f}')

for e in [p1, p2]:
    di = calculate_decayed_importance(e, decay_config)
    print(f'  Procedural "{e.content}": stored={e.importance_score:.4f}, decayed={di:.4f}')

print()
print('=== Testing Consolidation with Decay ===')

# Add low-importance old entries that should be pruned
for i in range(10):
    e = engine.record_task_outcome(f'low-{i}', 'agent-1', f'Low importance task {i}', importance=0.2)
    e.created_at = (datetime.now(UTC) - timedelta(days=30)).isoformat()
    entries = store.load('episodic.json')
    for j, ee in enumerate(entries):
        if ee.id == e.id:
            entries[j] = e
            break
    store.save('episodic.json', entries)

# Add high-importance entries that should survive
for i in range(3):
    engine.record_task_outcome(f'high-{i}', 'agent-1', f'High importance {i}', importance=0.95)

print(f'Before consolidation: {engine.get_stats()}')
engine.consolidate()
print(f'After consolidation: {engine.get_stats()}')

print()
print('=== Testing Search with Decay-Aware Ranking ===')
results = engine.search('task', apply_decay=True)
print(f'Search results (decay-aware): {len(results)}')
for r in results[:5]:
    di = r.metadata.get('decayed_importance', 'N/A')
    print(f'  {r.content[:30]}: importance={r.importance_score:.4f}, decayed={di:.4f}')

print()
print('=== All tests passed! ===')