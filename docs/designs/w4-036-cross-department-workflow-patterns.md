# W4-036: Cross-Department Workflow Patterns — Design Document

## Problem

All existing workflows are single-department. Complex tasks (feature delivery, incident response) require coordination across multiple departments but currently lack structured handoff protocols, escalation paths, or department-aware routing.

## Organization Structure

```
┌─────────────────────────────────────────┐
│           EXECUTIVE LAYER               │
│  human-ceo, ceo-advisor, chief-of-staff │
│  cto, cfo, coo                          │
├─────────────┬──────────────┬────────────┤
│ ENGINEERING │  OPERATIONS  │  PRODUCT   │
│ chief-arch  │ devops-eng   │ product-mgr│
│ lead-eng    │ security-eng │ tech-writer│
│ backend-eng │              │ qa-eng     │
│ frontend-eng│              │            │
│ ai-engineer │              │            │
│ data-engineer│             │            │
└─────────────┴──────────────┴────────────┘
```

## Department Model

### Department Enum

```python
class Department(str, Enum):
    EXECUTIVE = "executive"
    ENGINEERING = "engineering"
    OPERATIONS = "operations"
    PRODUCT = "product"
```

### Agent-to-Department Mapping

| Department | Agents |
|-----------|--------|
| EXECUTIVE | human-ceo, ceo-advisor, chief-of-staff, cto, cfo, coo |
| ENGINEERING | chief-architect, lead-engineer, backend-engineer, frontend-engineer, ai-engineer, data-engineer |
| OPERATIONS | devops-engineer, security-engineer |
| PRODUCT | product-manager, technical-writer, qa-engineer |

## Handoff Protocol

### HandoffContext Model

| Field | Type | Description |
|-------|------|-------------|
| from_dept | Department | Source department |
| to_dept | Department | Target department |
| payload | dict | Context data transferred |
| timestamp | str | ISO timestamp |
| status | HandoffStatus | PENDING → ACCEPTED → COMPLETED |
| sender_agent | str | Agent initiating handoff |
| receiver_agent | str | Agent receiving handoff |

### Handoff Flow

```
Sender Agent ──▶ HandoffContext ──▶ Receiver Agent
    │                │                    │
    │          Status: PENDING            │
    │                │                    │
    │          Status: ACCEPTED ◀─────────┘
    │                │
    └──▶ Status: COMPLETED
```

### Cross-Department Handoffs

All department pairs can handoff bi-directionally. The `can_handoff()` function validates the routing.

## Escalation Levels

| Level | Trigger | Route |
|-------|---------|-------|
| DEPARTMENT | Issue within single department | Dept head resolves |
| CROSS_DEPARTMENT | Issue spans departments | chief-of-staff coordinates |
| BUSINESS_CRITICAL | Revenue/safety impact | human-ceo decides |

### Escalation Matrix

| From | To | Level |
|------|-----|-------|
| Any specialist | Dept executive | DEPARTMENT |
| Any dept | chief-of-staff | CROSS_DEPARTMENT |
| chief-of-staff | human-ceo | BUSINESS_CRITICAL |

## Workflow Patterns

### Pattern 1: Sequential Handoff

A finishes → B starts. Simplest cross-department pattern.

```
trigger ──▶ [Dept A: do work] ──▶ [Dept B: receive & continue]
```

**Use case:** Feature spec (Product → Engineering)

### Pattern 2: Parallel Execution

Multiple departments work simultaneously, merge at join point.

```
              ┌──▶ [Engineering: implement] ──┐
trigger ──────┤                               ├──▶ [QA: validate]
              └──▶ [Product: spec work] ──────┘
```

**Use case:** Feature delivery (Engineering + Product in parallel → QA merge)

### Pattern 3: Review Gate

Department A produces → Department B reviews → approval → Department C implements.

```
trigger ──▶ [Dept A: produce] ──▶ [Dept B: review] ──▶ [Dept C: implement]
```

**Use case:** Security review (Engineering → Security → Engineering)

### Pattern 4: Incident Response

Operations detects → Executive notifies → Engineering investigates → Operations verifies.

```
[Ops: detect] ──▶ [Exec: notify] ──▶ [Eng: investigate] ──▶ [Eng: fix] ──▶ [Ops: verify]
```

**Use case:** Production incidents

## Integration with WorkflowEngine

1. `WorkflowEngine._advance_steps()` uses `get_department(assignee)` for routing
2. `HandoffContext` is created when step assignee changes department
3. Department-aware task routing ensures tasks go to correct department queue
4. Escalation triggers when step fails and escalation level is determined

## File Structure

New file: `src/lightspeed_agents/workflow/cross_dept.py`

| Export | Type | Purpose |
|--------|------|---------|
| Department | enum | Department identifiers |
| DEPARTMENT_AGENTS | dict | Agent-to-department mapping |
| get_department() | function | Lookup agent's department |
| get_department_agents() | function | List agents in a department |
| can_handoff() | function | Validate cross-dept routing |
| HandoffContext | model | Handoff state tracking |
| EscalationLevel | enum | Escalation classification |
| get_cross_dept_workflows() | function | Return pattern templates |
