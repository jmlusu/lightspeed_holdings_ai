# Changelog

All notable changes to Light Speed Holdings will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- Sprint 4 Plan: Workflow Orchestration Improvements (docs/sprint-4-plan.md)
  - 6 epics: Parallel Execution, Error Recovery, Rollback, Observability, Cross-Department, Enhanced CLI
  - 50 tasks across all agent roles
  - 2 new cross-department workflow definitions
  - Day-by-day timeline for Weeks 7-8
  - Risk register with 8 identified risks and mitigations
  - Success metrics and KPIs for workflow orchestration
  - Per-task dependency flags (BLOCKED BY, SHOULD WAIT, Cross-Epic Risk)
  - Cross-epic dependency map with 8 inter-epic dependencies flagged
  - 5 HIGH-risk dependency conflicts identified (parallel+retry, rollback+retry ordering, pause+sync, file locking)
- Updated roadmap to reflect Sprint 3 in progress, Sprint 4 in planning

### In Progress (Sprint 3 — Memory & Knowledge)
- Embeddings system for semantic search
- Memory consolidation with embedding-aware dedup
- Knowledge graph foundation
- Cross-agent memory sharing protocol
- Memory analytics dashboard

---

## [0.3.0] — 2026-07-28 (Sprint 3 Start)

### Planned
- Semantic search via embeddings (OpenAI + local fallback)
- FAISS vector store integration
- Knowledge graph with entity/relationship extraction
- Cross-agent memory sharing with access controls
- Memory analytics and health reporting

---

## [0.2.0] — 2026-07-14 (Sprint 2 Complete)

### Added
- AgentLoop with ReAct pattern for multi-turn reasoning
- ToolRunner with sandboxed execution (read, write, edit, search, grep, python, git)
- CostTracker with daily/task budget enforcement
- Enhanced AuditStore with correlation-based tracing
- Executor with tick-based task processing
- Permission system with 5 tiers (T0-T4) and HITL approval gates
- DeadLetterQueue for stale task detection
- 248+ tests passing

---

## [0.1.0] — 2026-06-30 (Sprint 1 Complete)

### Added
- Python package with src layout
- CLI foundation (Typer) with 12 subcommands
- Agent registry (21 agents across 9 departments)
- Configuration system (YAML) for departments, models, KPIs, workflows
- Pydantic models for Agent, Task, Workflow
- Department hierarchy and executive reporting lines
- Model tier system (fast/standard/premium) with provider fallback
- Ruff linting + Black formatting + Pytest
- GitHub Actions CI pipeline
- 248+ tests passing
