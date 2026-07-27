# Sprint 4 Planning: Workflow Orchestration Improvements

## Sprint Overview

**Sprint Name:** MVP 4 — Workflow Orchestration Improvements  
**Duration:** Weeks 7-8 (August 11 - August 24, 2026)  
**Sprint Goal:** Deliver robust multi-step workflow orchestration with parallel execution, error recovery, rollback capabilities, and enhanced observability — enabling agents to coordinate complex cross-department tasks reliably.

---

## Current State Assessment

### What Exists (from Sprints 1-3)
- ✅ WorkflowEngine with sequential step execution and dependency resolution
- ✅ WorkflowRun model with status tracking (CREATED → RUNNING → COMPLETED/FAILED/CANCELLED)
- ✅ MessageBus with full task lifecycle (PENDING → IN_PROGRESS → COMPLETED/FAILED/ESCALATED/WAITING_APPROVAL/CANCELLED)
- ✅ Executor with tick-based task processing and DLQ integration
- ✅ DeadLetterQueue with stale task detection (30-min timeout)
- ✅ AuditStore with correlation-based tracing and cost logging
- ✅ Permission system with 5 tiers (T0-T4) and HITL approval gates
- ✅ 4 pre-defined workflows (daily-executive-briefing, software-development, incident-response, hiring)
- ✅ CLI commands: `workflows list|show|start|runs|status|approve|complete|cancel`
- ✅ 248+ tests passing across all modules

### What's Missing for Sprint 4
- ❌ Parallel step execution for independent tasks
- ❌ Workflow versioning and migration support
- ❌ Rollback mechanism for failed workflow steps
- ❌ Automatic retry with exponential backoff
- ❌ Workflow-specific observability (metrics, tracing dashboards)
- ❌ Cross-department coordination workflows
- ❌ Event-driven agent communication patterns
- ❌ Workflow pause/resume with state preservation
- ❌ Enhanced CLI for workflow management (pause, resume, retry, inspect)

---

## Sprint 4 Goals

### Primary Goal
Enable reliable multi-step workflow orchestration with parallel execution, automatic error recovery, and rollback capabilities — so agents can coordinate complex cross-department tasks without manual intervention.

### Success Criteria
- [ ] Workflows execute independent steps in parallel
- [ ] Failed steps auto-retry with configurable backoff
- [ ] Failed workflows can be rolled back to a checkpoint
- [ ] Workflow observability provides real-time execution insights
- [ ] Cross-department workflows coordinate reliably
- [ ] All existing tests continue passing
- [ ] New test coverage ≥ 90% for workflow orchestration code

---

## Sprint 4 Backlog (Prioritized)

### Epic 1: Parallel Step Execution (HIGH Priority)

| Task ID | Task | Owner | Est. Hours | Priority | Status |
|---------|------|-------|------------|----------|--------|
| W4-001 | Design parallel execution model (DAG-based) | chief-architect | 4 | P0 | TODO |
| W4-002 | Implement WorkflowDAG with topological sort | lead-engineer | 8 | P0 | TODO |
| W4-003 | Add parallel step dispatch to WorkflowEngine | backend-engineer | 8 | P0 | TODO |
| W4-004 | Implement parallel task claiming in Executor | backend-engineer | 6 | P0 | TODO |
| W4-005 | Add parallel step completion synchronization | backend-engineer | 6 | P0 | TODO |
| W4-006 | Update MessageBus for concurrent task operations | backend-engineer | 4 | P1 | TODO |
| W4-007 | Add `max_parallel` config to workflow definitions | lead-engineer | 2 | P1 | TODO |
| W4-008 | Write unit tests for parallel execution | qa-engineer | 6 | P0 | TODO |
| W4-009 | Write integration tests for parallel workflows | qa-engineer | 6 | P0 | TODO |

**Exit Criteria for Epic 1:**
- Workflows with independent steps execute concurrently
- Parallel steps synchronize correctly at join points
- `max_parallel` limits concurrent execution
- All parallel execution tests pass

---

### Epic 2: Error Recovery & Retry Mechanisms (HIGH Priority)

| Task ID | Task | Owner | Est. Hours | Priority | Status |
|---------|------|-------|------------|----------|--------|
| W4-010 | Design retry policy model (max_retries, backoff, jitter) | lead-engineer | 3 | P0 | TODO |
| W4-011 | Implement RetryPolicy on WorkflowStep | backend-engineer | 4 | P0 | TODO |
| W4-012 | Add automatic retry logic to Executor | backend-engineer | 6 | P0 | TODO |
| W4-013 | Implement exponential backoff with jitter | backend-engineer | 4 | P0 | TODO |
| W4-014 | Add retry state tracking to Task model | backend-engineer | 3 | P0 | TODO |
| W4-015 | Enhance DLQ with retry-aware processing | backend-engineer | 4 | P1 | TODO |
| W4-016 | Add configurable retry policies per workflow | lead-engineer | 3 | P1 | TODO |
| W4-017 | Write unit tests for retry mechanisms | qa-engineer | 6 | P0 | TODO |
| W4-018 | Write integration tests for retry flows | qa-engineer | 4 | P0 | TODO |

**Exit Criteria for Epic 2:**
- Failed steps retry automatically up to `max_retries`
- Exponential backoff with jitter prevents thundering herd
- Retry state is tracked and auditable
- DLQ handles retry-aware processing

---

### Epic 3: Workflow Rollback & Checkpointing (HIGH Priority)

| Task ID | Task | Owner | Est. Hours | Priority | Status |
|---------|------|-------|------------|----------|--------|
| W4-019 | Design checkpoint/rollback model | chief-architect | 4 | P0 | TODO |
| W4-020 | Implement WorkflowCheckpoint model | backend-engineer | 4 | P0 | TODO |
| W4-021 | Add checkpoint creation at step boundaries | backend-engineer | 6 | P0 | TODO |
| W4-022 | Implement rollback to checkpoint | backend-engineer | 8 | P0 | TODO |
| W4-023 | Add compensating action support for step rollback | backend-engineer | 6 | P1 | TODO |
| W4-024 | Integrate rollback with failure handling | backend-engineer | 4 | P0 | TODO |
| W4-025 | Add rollback CLI command | frontend-engineer | 3 | P1 | TODO |
| W4-026 | Write unit tests for checkpoint/rollback | qa-engineer | 6 | P0 | TODO |
| W4-027 | Write integration tests for rollback flows | qa-engineer | 6 | P0 | TODO |

**Exit Criteria for Epic 3:**
- Checkpoints are created at each step boundary
- Failed workflows can roll back to last successful checkpoint
- Compensating actions execute during rollback
- Rollback is auditable and recorded in memory

---

### Epic 4: Workflow Observability (MEDIUM Priority)

| Task ID | Task | Owner | Est. Hours | Priority | Status |
|---------|------|-------|------------|----------|--------|
| W4-028 | Design workflow metrics model | data-engineer | 4 | P1 | TODO |
| W4-029 | Implement WorkflowMetrics collector | data-engineer | 6 | P1 | TODO |
| W4-030 | Add workflow execution tracing | data-engineer | 6 | P1 | TODO |
| W4-031 | Create workflow performance dashboard endpoint | frontend-engineer | 6 | P2 | TODO |
| W4-032 | Add workflow health scoring | data-engineer | 4 | P2 | TODO |
| W4-033 | Implement workflow SLA tracking | data-engineer | 4 | P2 | TODO |
| W4-034 | Add workflow execution timeline visualization | frontend-engineer | 6 | P2 | TODO |
| W4-035 | Write tests for observability metrics | qa-engineer | 4 | P1 | TODO |

**Exit Criteria for Epic 4:**
- Workflow metrics (duration, success rate, cost) are collected
- Execution traces are available for debugging
- Dashboard shows workflow health and performance
- SLA violations are detected and reported

---

### Epic 5: Cross-Department Coordination (MEDIUM Priority)

| Task ID | Task | Owner | Est. Hours | Priority | Status |
|---------|------|-------|------------|----------|--------|
| W4-036 | Design cross-department workflow patterns | chief-of-staff | 4 | P1 | TODO |
| W4-037 | Implement department-aware task routing | lead-engineer | 6 | P1 | TODO |
| W4-038 | Add department handoff protocols | backend-engineer | 6 | P1 | TODO |
| W4-039 | Create cross-department escalation workflows | backend-engineer | 4 | P1 | TODO |
| W4-040 | Implement department coordination events | backend-engineer | 4 | P2 | TODO |
| W4-041 | Add 2 new cross-department workflow definitions | chief-of-staff | 3 | P1 | TODO |
| W4-042 | Write tests for cross-department flows | qa-engineer | 6 | P1 | TODO |

**Exit Criteria for Epic 4:**
- Tasks route correctly across departments
- Handoff protocols transfer context between departments
- Escalation workflows follow organizational hierarchy
- At least 2 new cross-department workflows are operational

---

### Epic 6: Enhanced CLI & State Management (LOW Priority)

| Task ID | Task | Owner | Est. Hours | Priority | Status |
|---------|------|-------|------------|----------|--------|
| W4-043 | Add `workflows pause` CLI command | frontend-engineer | 3 | P2 | TODO |
| W4-044 | Add `workflows resume` CLI command | frontend-engineer | 3 | P2 | TODO |
| W4-045 | Add `workflows retry` CLI command | frontend-engineer | 3 | P2 | TODO |
| W4-046 | Add `workflows inspect` CLI command (full details) | frontend-engineer | 4 | P2 | TODO |
| W4-047 | Add `workflows history` CLI command | frontend-engineer | 3 | P2 | TODO |
| W4-048 | Improve workflow state persistence (atomic writes) | backend-engineer | 4 | P1 | TODO |
| W4-049 | Add workflow version field to models | backend-engineer | 2 | P1 | TODO |
| W4-050 | Write tests for new CLI commands | qa-engineer | 4 | P2 | TODO |

**Exit Criteria for Epic 6:**
- All new CLI commands work correctly
- Workflow state persists reliably across restarts
- Version tracking is enabled for workflow definitions

---

## Task Dependency Graph

```
W4-001 (DAG Design) ──┬──→ W4-002 (DAG Implementation) ──→ W4-003 (Engine Parallel)
                       │                                      ↓
                       │                              W4-004 (Executor Parallel)
                       │                                      ↓
                       │                              W4-005 (Synchronization)
                       │                                      ↓
                       └──→ W4-006 (Concurrent MessageBus) ←── W4-007 (max_parallel config)

W4-010 (Retry Design) ──→ W4-011 (RetryPolicy Model) ──→ W4-012 (Auto Retry)
                           ↓                              ↓
                     W4-013 (Backoff)              W4-014 (Retry State)
                           ↓                              ↓
                     W4-015 (DLQ Enhancement)     W4-016 (Configurable Policies)

W4-019 (Checkpoint Design) ──→ W4-020 (Checkpoint Model) ──→ W4-021 (Checkpoint Creation)
                               ↓                              ↓
                         W4-022 (Rollback) ←──────── W4-023 (Compensating Actions)
                               ↓
                         W4-024 (Rollback Integration) ──→ W4-025 (CLI Rollback)

W4-028 (Metrics Design) ──→ W4-029 (Metrics Collector) ──→ W4-030 (Tracing)
                           ↓                              ↓
                     W4-031 (Dashboard)           W4-032 (Health Scoring)
                           ↓                              ↓
                     W4-033 (SLA Tracking)        W4-034 (Timeline Visualization)

W4-036 (Cross-Dept Design) ──→ W4-037 (Dept Routing) ──→ W4-038 (Handoff Protocols)
                               ↓                              ↓
                         W4-039 (Escalation)         W4-040 (Coordination Events)
                               ↓
                         W4-041 (New Workflow Definitions)
```

---

## Sprint 4 Task Assignments

### Executive Layer

| Agent | Tasks | Responsibilities |
|-------|-------|------------------|
| human-ceo | — | Final approval on architecture decisions, production readiness |
| ceo-advisor | — | Strategic alignment review, risk assessment |
| chief-of-staff | W4-036, W4-041 | Cross-department workflow design, coordination protocols |
| cto | Architecture Review | Review DAG design, checkpoint model, parallel execution architecture |
| cfo | — | Monitor sprint budget, LLM cost impact of parallel execution |
| coo | — | Operational readiness review, process optimization |

### Engineering Layer

| Agent | Primary Tasks | Secondary Tasks |
|-------|---------------|-----------------|
| chief-architect | W4-001, W4-019 | Architecture reviews for all epics |
| lead-engineer | W4-002, W4-007, W4-010, W4-016, W4-037 | Code reviews, sprint coordination |
| backend-engineer | W4-003, W4-004, W4-005, W4-006, W4-011-W4-015, W4-020-W4-024, W4-038-W4-040, W4-048-W4-049 | Core implementation |
| frontend-engineer | W4-025, W4-031, W4-034, W4-043-W4-047 | CLI commands, dashboard |
| ai-engineer | — | Memory integration for checkpoint state |
| data-engineer | W4-028, W4-029, W4-030, W4-032, W4-033 | Metrics and observability |

### Operations Layer

| Agent | Tasks | Responsibilities |
|-------|-------|------------------|
| devops-engineer | — | CI/CD updates for new tests, deployment readiness |
| security-engineer | Security Review | Review parallel execution for race conditions, checkpoint integrity |

### Product Layer

| Agent | Tasks | Responsibilities |
|-------|-------|------------------|
| product-manager | — | Acceptance criteria validation, user story prioritization |
| technical-writer | — | Document new workflow patterns, CLI usage guides |
| qa-engineer | W4-008, W4-009, W4-017, W4-018, W4-026, W4-027, W4-035, W4-042, W4-050 | Test strategy, test implementation |

---

## Sprint 4 Timeline

### Week 7 (August 11-15, 2026)

| Day | Focus | Key Activities | Milestone |
|-----|-------|----------------|-----------|
| **Mon 8/11** | Sprint Kickoff | Sprint planning, architecture review, task assignment | M4-M0: Sprint Kickoff Complete |
| **Tue 8/12** | DAG Design | W4-001 (chief-architect), W4-010 (lead-engineer), W4-019 (chief-architect), W4-028 (data-engineer) | Design documents complete |
| **Wed 8/13** | Core Implementation | W4-002 (lead-engineer), W4-011 (backend-engineer), W4-020 (backend-engineer), W4-029 (data-engineer) | Models and interfaces defined |
| **Thu 8/14** | Engine Enhancement | W4-003 (backend-engineer), W4-012 (backend-engineer), W4-021 (backend-engineer), W4-030 (data-engineer) | Core engine features working |
| **Fri 8/15** | Week 1 Review | Integration testing, code review, blockers review | M4-M1: Core Orchestration MVP |

### Week 8 (August 18-22, 2026)

| Day | Focus | Key Activities | Milestone |
|-----|-------|----------------|-----------|
| **Mon 8/18** | Parallel & Retry | W4-004, W4-005 (backend), W4-013, W4-014 (backend), W4-022, W4-023 (backend) | Parallel execution and retry working |
| **Tue 8/19** | Integration | W4-006, W4-015, W4-024 (backend), W4-036, W4-037, W4-038 (cross-dept) | Cross-department coordination |
| **Wed 8/20** | CLI & Dashboard | W4-025, W4-031, W4-034, W4-043-W4-047 (frontend) | CLI and dashboard complete |
| **Thu 8/21** | Testing | W4-008, W4-009, W4-017, W4-018, W4-026, W4-027, W4-035, W4-042, W4-050 (qa-engineer) | All tests passing |
| **Fri 8/22** | Sprint Review | Final integration, demo, retrospective | M4-M2: Sprint 4 Complete |

---

## Sprint 4 Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| Parallel execution introduces race conditions in FileStore | Medium | High | Implement file locking for concurrent writes, add integration tests | backend-engineer |
| Checkpoint state grows too large for JSON persistence | Low | Medium | Implement checkpoint compression, add size limits | backend-engineer |
| Retry thundering herd overwhelms LLM providers | Medium | High | Implement jitter in backoff, add rate limiting | lead-engineer |
| Cross-department workflows create circular dependencies | Low | High | DAG validation prevents cycles, add dependency linting | chief-architect |
| Parallel execution increases LLM costs significantly | Medium | Medium | Add `max_parallel` limits, monitor cost per workflow | cfo |
| Rollback compensating actions fail | Medium | High | Implement rollback dry-run mode, add rollback tests | qa-engineer |
| Existing tests break from parallel execution changes | Low | High | Run full test suite after each epic, maintain backward compatibility | lead-engineer |
| Sprint scope creep from 50 tasks | Medium | Medium | Strict P0/P1 priority enforcement, defer P2 if behind | chief-of-staff |

---

## Sprint 4 Definition of Done

### Task-Level Done Criteria
A task is considered done when:
- [ ] Code is written and passes Ruff linting
- [ ] Code is formatted with Black
- [ ] Unit tests are written and passing
- [ ] Integration tests are written (if applicable)
- [ ] Code review is approved by lead-engineer or cto
- [ ] Documentation is updated (docstrings, README if needed)
- [ ] No regression in existing functionality
- [ ] Task status updated to COMPLETED in tracking system

### Epic-Level Done Criteria
An epic is considered done when:
- [ ] All P0 tasks in the epic are complete
- [ ] All exit criteria for the epic are met
- [ ] Integration tests pass for the epic
- [ ] Architecture review is complete
- [ ] Security review is complete (if applicable)

### Sprint-Level Done Criteria
The sprint is considered done when:
- [ ] All P0 epics are complete (Parallel Execution, Error Recovery, Rollback)
- [ ] P1 epics are ≥ 80% complete (Observability, Cross-Department)
- [ ] All existing tests continue passing (248+ baseline)
- [ ] New test coverage ≥ 90% for workflow orchestration code
- [ ] Demo successfully shows parallel execution, retry, and rollback
- [ ] Sprint retrospective is conducted
- [ ] Sprint 5 planning is prepared

---

## Sprint 4 Success Metrics / KPIs

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Parallel execution speedup | ≥ 40% faster for independent steps | Benchmark: compare sequential vs parallel for 5-step workflow |
| Retry success rate | ≥ 80% of transient failures recovered | Count retried tasks that eventually succeed |
| Rollback success rate | 100% of rollback attempts succeed | Count successful rollbacks / total rollback attempts |
| Workflow completion rate | ≥ 95% (up from ~85% baseline) | Count completed workflows / total started |
| Mean time to recovery (MTTR) | ≤ 2 minutes for auto-recovery | Average time from failure to successful retry |
| Test coverage (new code) | ≥ 90% | pytest-cov report |
| Existing test regression | 0 regressions | Full test suite passes |
| LLM cost per workflow | ≤ 15% increase over sequential | Cost tracker comparison |
| Cross-department handoff success | ≥ 95% | Count successful handoffs / total handoffs |
| Audit trail completeness | 100% of workflow events logged | Audit log entry count vs expected events |

---

## Sprint 4 Ceremonies

| Ceremony | Date | Time | Attendees | Duration |
|----------|------|------|-----------|----------|
| Sprint Planning | August 11, 2026 | 10:00 AM | All agents | 2 hours |
| Daily Standup | Daily (Mon-Fri) | 9:00 AM | All agents | 15 minutes |
| Mid-Sprint Review | August 15, 2026 | 2:00 PM | All agents + human-ceo | 1 hour |
| Sprint Review | August 22, 2026 | 2:00 PM | All agents + human-ceo | 1 hour |
| Sprint Retrospective | August 22, 2026 | 3:30 PM | All agents | 1 hour |
| Sprint 5 Pre-Planning | August 22, 2026 | 4:30 PM | chief-of-staff + lead-engineer | 30 minutes |

### Daily Standup Format
Each agent reports:
1. **Yesterday:** What I completed (task ID + status)
2. **Today:** What I'm working on (task ID + expected progress)
3. **Blockers:** Any impediments (with escalation path if needed)

---

## New Workflow Definitions (W4-041)

### 1. Cross-Department Feature Delivery

```yaml
- id: cross-department-feature
  name: Cross-Department Feature Delivery
  description: Deliver a feature requiring multiple departments
  owner: chief-of-staff
  steps:
    - id: define_requirements
      instruction: "Define feature requirements and acceptance criteria"
      assignee: product-manager
      tier: T1
      tags: [requirements, product]

    - id: architecture_review
      instruction: "Review architecture and identify cross-department impacts"
      assignee: chief-architect
      tier: T1
      depends_on: [define_requirements]
      tags: [architecture, engineering]

    - id: engineering_plan
      instruction: "Create engineering implementation plan"
      assignee: lead-engineer
      tier: T0
      depends_on: [architecture_review]
      tags: [planning, engineering]

    - id: implement_backend
      instruction: "Implement backend components"
      assignee: backend-engineer
      tier: T0
      depends_on: [engineering_plan]
      tags: [execution, engineering]

    - id: implement_frontend
      instruction: "Implement frontend components"
      assignee: frontend-engineer
      tier: T0
      depends_on: [engineering_plan]
      tags: [execution, engineering]

    - id: integration_testing
      instruction: "Run integration tests across all components"
      assignee: qa-engineer
      tier: T0
      depends_on: [implement_backend, implement_frontend]
      tags: [testing, quality]

    - id: security_review
      instruction: "Security review and compliance check"
      assignee: security-engineer
      tier: T1
      depends_on: [integration_testing]
      tags: [security, compliance]

    - id: deployment
      instruction: "Deploy to production"
      assignee: devops-engineer
      tier: T3
      depends_on: [security_review]
      tags: [deployment, operations]
```

### 2. Incident Escalation & Resolution

```yaml
- id: incident-escalation
  name: Incident Escalation & Resolution
  description: Handle critical incidents with proper escalation
  owner: coo
  steps:
    - id: detect_classify
      instruction: "Detect incident and classify severity (P0-P3)"
      assignee: devops-engineer
      tier: T0
      tags: [detection, operations]

    - id: notify_stakeholders
      instruction: "Notify relevant stakeholders based on severity"
      assignee: chief-of-staff
      tier: T1
      depends_on: [detect_classify]
      tags: [notification, communication]

    - id: assign_response_team
      instruction: "Assign response team based on incident type"
      assignee: lead-engineer
      tier: T0
      depends_on: [notify_stakeholders]
      tags: [assignment, engineering]

    - id: investigate
      instruction: "Investigate root cause and document findings"
      assignee: backend-engineer
      tier: T0
      depends_on: [assign_response_team]
      tags: [investigation, engineering]

    - id: implement_fix
      instruction: "Implement and test the fix"
      assignee: backend-engineer
      tier: T2
      depends_on: [investigate]
      tags: [resolution, engineering]

    - id: verify_resolution
      instruction: "Verify fix resolves the incident"
      assignee: qa-engineer
      tier: T0
      depends_on: [implement_fix]
      tags: [verification, quality]

    - id: postmortem
      instruction: "Write postmortem and update runbooks"
      assignee: lead-engineer
      tier: T1
      depends_on: [verify_resolution]
      tags: [postmortem, documentation]
```

---

## Appendix: Code Changes Summary

### New Files to Create
```
src/lightspeed_agents/workflow/
├── dag.py                    # WorkflowDAG with topological sort
├── retry.py                  # RetryPolicy, exponential backoff
├── checkpoint.py             # WorkflowCheckpoint model and management
├── rollback.py               # Rollback engine with compensating actions
├── metrics.py                # WorkflowMetrics collector
├── parallel.py               # Parallel step executor
└── cross_dept.py             # Cross-department coordination

tests/
├── test_workflow_dag.py
├── test_workflow_retry.py
├── test_workflow_checkpoint.py
├── test_workflow_rollback.py
├── test_workflow_metrics.py
├── test_workflow_parallel.py
└── test_workflow_cross_dept.py
```

### Files to Modify
```
src/lightspeed_agents/workflow/
├── engine.py                 # Add parallel execution, retry, rollback hooks
├── models.py                 # Add retry_policy, version, checkpoint fields
└── loader.py                 # Parse new YAML fields

src/lightspeed_agents/message_bus/
├── message_bus.py            # Concurrent task operations, file locking
├── executor.py               # Retry logic, parallel processing
├── task.py                   # Add retry_count, last_error fields
└── dead_letter.py            # Retry-aware processing

src/lightspeed_agents/cli/commands/
└── workflows.py              # Add pause, resume, retry, inspect, history commands

company/workflows.yaml        # Add 2 new cross-department workflows
```

---

*Document Version: 1.0*  
*Created: July 27, 2026*  
*Owner: Office of the CEO, Light Speed Holdings, Inc.*  
*Approved by: human-ceo*
