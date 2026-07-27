# Sprint 3 Planning: Memory & Knowledge

## Sprint Overview

**Sprint Name:** MVP 3 — Memory & Knowledge  
**Duration:** Weeks 5-6 (July 28 - August 10, 2026)  
**Sprint Goal:** Persistent organizational memory that enables learning and knowledge sharing across all agents.

---

## Current State Assessment

### What Exists (from Sprint 1-2)
- ✅ MemoryEngine with basic record/recall capabilities
- ✅ FileStore for JSON persistence
- ✅ ConsolidationScheduler with tick-based consolidation
- ✅ MemoryEntry model with metadata support
- ✅ keyword_search for basic retrieval
- ✅ Memory types: episodic, semantic, procedural, relational, temporal, aggregate

### What's Missing for Sprint 3
- ❌ Embeddings-based semantic search
- ❌ Vector storage for similarity search
- ❌ Knowledge graph relationships
- ❌ Cross-agent memory sharing protocol
- ❌ Memory analytics and insights

---

## Sprint 3 Goals

### Primary Goal
Enable agents to recall relevant context through semantic search and maintain organizational knowledge through a knowledge graph.

### Success Criteria
- [ ] Agents can search memory using semantic similarity (not just keywords)
- [ ] Knowledge graph tracks relationships between concepts, agents, and decisions
- [ ] Memory consolidation runs automatically and maintains quality
- [ ] Cross-agent memory sharing works without data loss
- [ ] Memory analytics provide actionable insights

---

## Sprint 3 Tasks

### Epic 1: Embeddings System (HIGH Priority)

| Task ID | Task | Owner | Est. Hours | Status | Dependencies |
|---------|------|-------|------------|--------|--------------|
| M3-001 | Design embedding provider abstraction | ai-engineer | 4 | TODO | None — **START HERE** |
| M3-002 | Implement OpenAI embedding integration | ai-engineer | 6 | TODO | ⚠️ M3-001 |
| M3-003 | Implement local embedding fallback (sentence-transformers) | ai-engineer | 8 | TODO | ⚠️ M3-001 |
| M3-004 | Create VectorStore interface | ai-engineer | 4 | TODO | None — can parallel with M3-001 |
| M3-005 | Implement FAISS vector store | ai-engineer | 8 | TODO | ⚠️ M3-004 |
| M3-006 | Add embedding generation to MemoryEngine | ai-engineer | 4 | TODO | 🔴 M3-001, M3-002 or M3-003 |
| M3-007 | Implement semantic search function | ai-engineer | 6 | TODO | 🔴 M3-005, M3-006 |
| M3-008 | Add embedding caching layer | backend-engineer | 4 | TODO | ⚠️ M3-001 |

**Exit Criteria for Epic 1:**
- Embedding generation works with OpenAI and local models
- Vector store persists embeddings alongside memory entries
- Semantic search returns relevant results with similarity scores

**Critical Path:** M3-001 → M3-002 → M3-006 → M3-007

---

### Epic 2: Memory Consolidation Enhancement (HIGH Priority)

| Task ID | Task | Owner | Est. Hours | Status | Dependencies |
|---------|------|-------|------------|--------|--------------|
| M3-009 | Enhance consolidation with embedding-aware dedup | ai-engineer | 6 | TODO | 🔴 M3-007 (semantic search), M3-001 (abstraction) |
| M3-010 | Implement importance scoring for memories | data-engineer | 6 | TODO | None — can parallel with Epic 1 |
| M3-011 | Add temporal decay for episodic memories | data-engineer | 4 | TODO | None — can parallel with Epic 1 |
| M3-012 | Create consolidation metrics tracking | data-engineer | 4 | TODO | None — can parallel with Epic 1 |
| M3-013 | Implement memory compression for old entries | backend-engineer | 6 | TODO | None — can parallel with Epic 1 |
| M3-014 | Add consolidation scheduling (cron-like) | devops-engineer | 4 | TODO | ⚠️ M3-013 (compression should be in place first) |

**Exit Criteria for Epic 2:**
- Consolidation deduplicates based on semantic similarity, not just text
- Important memories persist longer than trivial ones
- Consolidation metrics are tracked and reportable

**Critical Path:** M3-007 → M3-009

---

### Epic 3: Knowledge Graph Foundation (MEDIUM Priority)

| Task ID | Task | Owner | Est. Hours | Status | Dependencies |
|---------|------|-------|------------|--------|--------------|
| M3-015 | Design knowledge graph schema | data-engineer | 6 | TODO | None — **can start parallel to Epic 1** |
| M3-016 | Implement GraphNode and GraphEdge models | data-engineer | 4 | TODO | ⚠️ M3-015 |
| M3-017 | Create KnowledgeGraph class | data-engineer | 8 | TODO | 🔴 M3-016 |
| M3-018 | Implement relationship extraction from memories | ai-engineer | 8 | TODO | 🔴 M3-017, M3-001 (embedding abstraction for entity similarity) |
| M3-019 | Add graph traversal queries | data-engineer | 6 | TODO | ⚠️ M3-017 |
| M3-020 | Create graph persistence layer | backend-engineer | 4 | TODO | ⚠️ M3-017 |
| M3-021 | Integrate knowledge graph with MemoryEngine | ai-engineer | 4 | TODO | 🔴 M3-017, M3-006 (embedding generation in MemoryEngine) |

**Exit Criteria for Epic 3:**
- Knowledge graph stores entities and relationships
- Relationships are extracted from memory entries
- Graph queries return connected concepts

**Critical Path:** M3-015 → M3-016 → M3-017 → M3-018

---

### Epic 4: Cross-Agent Memory Sharing (MEDIUM Priority)

| Task ID | Task | Owner | Est. Hours | Status | Dependencies |
|---------|------|-------|------------|--------|--------------|
| M3-022 | Design memory sharing protocol | lead-engineer | 4 | TODO | None — can start parallel to other epics |
| M3-023 | Implement memory scope (private/shared/global) | backend-engineer | 6 | TODO | 🔴 M3-022 |
| M3-024 | Add agent-specific memory filtering | backend-engineer | 4 | TODO | ⚠️ M3-023 |
| M3-025 | Create memory access controls | security-engineer | 4 | TODO | ⚠️ M3-023 (scope definition needed) |
| M3-026 | Implement memory conflict resolution | ai-engineer | 6 | TODO | 🔴 M3-023, M3-024 |
| M3-027 | Add memory versioning for shared entries | backend-engineer | 4 | TODO | ⚠️ M3-023 |

**Exit Criteria for Epic 4:**
- Agents can share relevant memories with permissions
- Memory conflicts are resolved automatically
- Access controls prevent unauthorized memory access

**Critical Path:** M3-022 → M3-023 → M3-026

---

### Epic 5: Memory Analytics (LOW Priority)

| Task ID | Task | Owner | Est. Hours | Status | Dependencies |
|---------|------|-------|------------|--------|--------------|
| M3-028 | Create memory usage metrics collector | data-engineer | 4 | TODO | None — can start parallel |
| M3-029 | Implement memory quality scoring | data-engineer | 4 | TODO | ⚠️ M3-028 |
| M3-030 | Add memory retrieval performance tracking | data-engineer | 3 | TODO | ⚠️ M3-028 |
| M3-031 | Create memory analytics dashboard endpoint | frontend-engineer | 4 | TODO | 🔴 M3-028, M3-029, M3-030 |
| M3-032 | Generate weekly memory health report | ceo-advisor | 2 | TODO | 🔴 M3-028, M3-029, M3-030 |

**Exit Criteria for Epic 5:**
- Memory metrics are collected and stored
- Analytics dashboard shows memory health
- Weekly reports are generated automatically

**Critical Path:** M3-028 → M3-029/M3-030 → M3-031

---

## Sprint 3 Milestones

| Milestone | Target Date | Deliverable |
|-----------|-------------|-------------|
| M3-M1: Embeddings MVP | Week 5, Day 3 | Semantic search working |
| M3-M2: Vector Store | Week 5, Day 5 | FAISS integration complete |
| M3-M3: Consolidation v2 | Week 6, Day 2 | Enhanced consolidation running |
| M3-M4: Knowledge Graph | Week 6, Day 4 | Graph queries working |
| M3-M5: Sprint Review | Week 6, Day 5 | Demo and retrospective |

---

## Sprint 3 Dependencies

### External Dependencies
- OpenAI API access for embeddings (or local model fallback)
- FAISS library installation
- sentence-transformers for local embeddings

### Internal Dependencies
- Sprint 2 (AgentLoop) must be complete
- MemoryEngine already exists and is functional
- FileStore abstraction is stable

### Blockers to Watch
1. **Embedding model availability** — If OpenAI is down, need local fallback ready
2. **Vector store performance** — FAISS may need tuning for large datasets
3. **Knowledge graph complexity** — May need to simplify schema if time-constrained

---

## Sprint 3 Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Embedding API costs exceed budget | Medium | High | Implement local fallback, cache aggressively |
| Vector store too slow for real-time | Low | High | Use approximate nearest neighbor, add caching |
| Knowledge graph too complex to finish | Medium | Medium | Deliver MVP graph, defer advanced queries |
| Cross-agent sharing creates conflicts | Low | Medium | Implement conflict resolution early |
| Consolidation loses important memories | Low | High | Add importance scoring before pruning |

---

## Sprint 3 Team Assignments

| Agent | Primary Tasks | Secondary Tasks |
|-------|---------------|-----------------|
| ai-engineer | M3-001 to M3-008, M3-018, M3-021, M3-026 | M3-009 |
| data-engineer | M3-010 to M3-012, M3-015 to M3-017, M3-028 to M3-030 | M3-020 |
| backend-engineer | M3-008, M3-013, M3-020, M3-023, M3-024, M3-027 | M3-014 |
| security-engineer | M3-025 | Review all memory access controls |
| lead-engineer | M3-022 | Architecture review, code review |
| devops-engineer | M3-014 | Memory consolidation scheduling |
| frontend-engineer | M3-031 | Memory analytics dashboard |
| ceo-advisor | M3-032 | Weekly memory health reports |

---

## Cross-Epic Dependency Map

```
Epic 1 (Embeddings)          Epic 3 (Knowledge Graph)
  M3-001 ──┬──► M3-002       M3-015 ──► M3-016 ──► M3-017
            ├──► M3-003                              │
            └──► M3-008                          ┌───┴───┐
                 │                               ▼       ▼
                 ▼                          M3-018   M3-019
            M3-006 ──────────────────────────►M3-021
                 │
                 ▼
Epic 2 (Consolidation)       Epic 4 (Cross-Agent)
  M3-007 ──► M3-009           M3-022 ──► M3-023 ──┬──► M3-024
                                                   ├──► M3-025
                                                   ├──► M3-026
                                                   └──► M3-027

Epic 5 (Analytics)
  M3-028 ──┬──► M3-029
            └──► M3-030 ──► M3-031, M3-032
```

### Cross-Epic Dependencies

| From | To | Relationship |
|------|----|--------------|
| M3-001 (abstraction) | M3-009 (consolidation dedup) | Embedding abstraction needed for semantic dedup |
| M3-006 (MemoryEngine) | M3-021 (graph integration) | Embedding generation must be in MemoryEngine |
| M3-001 (abstraction) | M3-018 (relationship extraction) | Entity similarity uses embeddings |
| M3-007 (semantic search) | M3-009 (consolidation dedup) | Dedup uses semantic similarity |
| M3-028 (metrics collector) | M3-032 (health report) | Report needs metrics data |

---

## Sprint 3 Ceremonies

| Ceremony | Date | Time | Attendees |
|----------|------|------|-----------|
| Sprint Planning | July 28, 2026 | 10:00 AM | All agents |
| Daily Standup | Daily | 9:00 AM | All agents |
| Sprint Review | August 10, 2026 | 2:00 PM | All agents + human-ceo |
| Sprint Retrospective | August 10, 2026 | 3:00 PM | All agents |

---

## Sprint 3 Definition of Done

A task is considered done when:
- [ ] Code is written and passes Ruff linting
- [ ] Code is formatted with Black
- [ ] Unit tests are written and passing
- [ ] Integration tests are written (if applicable)
- [ ] Code review is approved by lead-engineer or cto
- [ ] Documentation is updated
- [ ] No regression in existing functionality

---

## Sprint 3 Acceptance Criteria

The sprint is complete when:
1. **Embeddings System**
   - Semantic search returns relevant results
   - Embedding generation works with 2+ providers
   - Vector store persists and retrieves embeddings

2. **Memory Consolidation**
   - Consolidation runs automatically on schedule
   - Deduplication uses semantic similarity
   - Important memories persist longer

3. **Knowledge Graph**
   - Graph stores entities and relationships
   - Relationships are extracted from memories
   - Basic graph queries work

4. **Cross-Agent Sharing**
   - Agents can share memories with permissions
   - Conflict resolution works
   - Access controls are enforced

5. **Analytics**
   - Memory metrics are collected
   - Dashboard shows memory health
   - Weekly reports are generated

---

## Dependency Legend

| Symbol | Meaning |
|--------|---------|
| None | No dependencies — can start immediately |
| ⚠️ | Soft dependency — can start but needs predecessor to finish |
| 🔴 | Hard dependency — cannot start until predecessor is complete |
| **START HERE** | Recommended first task in epic |

---

## Critical Path Analysis

### Overall Sprint Critical Path
```
M3-001 → M3-002 → M3-006 → M3-007 → M3-009 → M3-031/M3-032
         (4h)     (6h)      (4h)      (6h)      (6h)
```

**Total Critical Path Hours:** 26 hours

### Parallel Work Streams

| Stream | Tasks | Can Start Day 1 |
|--------|-------|-----------------|
| Embeddings Core | M3-001, M3-004 | ✅ Yes |
| Knowledge Graph Design | M3-015 | ✅ Yes |
| Cross-Agent Protocol | M3-022 | ✅ Yes |
| Analytics Foundation | M3-028 | ✅ Yes |
| Consolidation (independent) | M3-010, M3-011, M3-012, M3-013 | ✅ Yes |

### Bottlenecks to Watch

1. **M3-007 (semantic search)** — Blocks Epic 2 consolidation dedup and is on critical path
2. **M3-017 (KnowledgeGraph class)** — Blocks all graph queries and integration
3. **M3-023 (memory scope)** — Blocks all cross-agent sharing features
4. **ai-engineer overload** — Assigned to 12 tasks across 4 epics; may need redistribution

---

*Document Version: 1.1*
*Created: July 27, 2026*
*Last Updated: July 27, 2026*
*Owner: Office of the CEO, Light Speed Holdings, Inc.*
*Approved by: human-ceo*
