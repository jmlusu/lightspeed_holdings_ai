# LightSpeed Holdings — System Architecture

## 1. Overview

LightSpeed Holdings is an AI Enterprise Operating System that generates, operates, and governs autonomous AI companies from configuration. The system models an organization as a team of AI agents, each with a role, department, tools, permissions, and a reporting line. Tasks flow through a message bus, are orchestrated by workflows, enforced by permissions, and recalled from memory.

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI (Typer)                            │
│  agents · company · run · tasks · workflows · permissions   │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌──────────────┐
   │ Executor  │   │ Workflow │   │  Prompt      │
   │  (poll)   │   │ Engine   │   │  Builder     │
   └─────┬─────┘   └────┬─────┘   └──────┬───────┘
         │              │                 │
         ▼              ▼                 ▼
   ┌──────────┐   ┌──────────┐   ┌──────────────┐
   │ Message   │   │ Message  │   │ Model        │
   │ Bus       │◄──│ Bus      │   │ Resolver     │
   │ (tasks)   │   │ (send)   │   │ (tier→LLM)  │
   └─────┬─────┘   └──────────┘   └──────┬───────┘
         │                                │
         ▼                                ▼
   ┌──────────┐                    ┌──────────────┐
   │ Memory   │                    │ Providers    │
   │ Engine   │                    │ ollama/openai│
   └──────────┘                    └──────────────┘
         │
         ▼
   ┌──────────────┐    ┌──────────────┐
   │ Permissions  │    │ Audit Store  │
   │ Checker+Gate │    │ (file-backed)│
   └──────────────┘    └──────────────┘
```

---

## 2. Enterprise Architecture

### 2.1 Company Constitution

The system is governed by an AI Company Constitution that defines:

**10 Foundational Principles:**
1. Truth over Opinion
2. Automation before Manual Work
3. Documentation before Memory
4. Quality before Speed
5. Security by Design
6. Continuous Improvement
7. Ownership with Accountability
8. Cost Awareness
9. Transparency and Auditability
10. Scalability and Resilience

**Decision Order:**
```
human-ceo → chief-of-staff → cfo/cto/coo → department heads → specialists
```

**Escalation Protocol:**
1. Specialist → Executive (within 15 minutes)
2. Executive → chief-of-staff (if cross-department)
3. chief-of-staff → human-ceo (if business-critical)

### 2.2 AI Company Maturity Model

| Domain | Score | Status |
|--------|-------|--------|
| Vision & Strategy | 98/100 | Exceptional |
| Business Architecture | 90/100 | Strong |
| Organizational Design | 94/100 | Excellent |
| Enterprise Architecture | 90/100 | Strong |
| Software Architecture | 84/100 | Good |
| AI Platform | 72/100 | Emerging |
| Product Readiness | 55/100 | In Progress |
| DevOps & Operations | 48/100 | Early |
| Governance & Security | 58/100 | Foundation |
| Market Validation | 30/100 | Not Started |

**Overall Maturity: 66/100 — Emerging AI Enterprise Platform**

### 2.3 Enterprise Governance

| Level | Authority | Scope |
|-------|-----------|-------|
| CEO | Final decision on all matters | Strategic direction, budget, production |
| CoS | Cross-department coordination | Sprint planning, roadmap, blockers |
| CTO | Technology decisions | Architecture, code, tools, security |
| CFO | Budget and financial | Cost tracking, resource allocation |
| COO | Operational decisions | Process optimization, incidents |
| Department Heads | Department decisions | Team management, task assignment |
| Specialists | Task-level decisions | Implementation, testing, documentation |

---

## 2. Company Bootstrapping

### 3.1 Agent Registry

Agents are defined in `company/agent-registry.json`:

```json
{
  "agents": {
    "agents": [
      {
        "id": "backend-engineer",
        "name": "Backend Engineer",
        "role": "Backend Developer",
        "type": "Specialist",
        "department": "engineering",
        "reportsTo": "lead-engineer",
        "tools": ["python"],
        "permissions": ["edit"],
        "model_tier": "standard",
        "responsibilities": ["Backend implementation", "APIs", "database", "testing"]
      }
    ]
  }
}
```

**Fields:**
| Field | Purpose |
|-------|---------|
| `id` | Unique identifier (kebab-case) |
| `name` | Display name |
| `role` | Human-readable title |
| `type` | `Executive` or `Specialist` |
| `department` | Department key (matches `departments.yaml`) |
| `reportsTo` | Parent agent `id` (null for CEO) |
| `tools` | Tool names this agent may use |
| `permissions` | Permission strings (`read`, `edit`, `approve`, etc.) |
| `model_tier` | Model tier (fast/standard/premium) |
| `responsibilities` | List of agent responsibilities |

**Loading:** `agents/loader.py` reads the JSON and populates the global `registry` (a `Registry` instance). Every CLI command and the `AgentRunner` call `load_agents()` first.

### 3.2 Organizational Hierarchy

```
human-ceo (executive)
├── chief-of-staff (executive)
├── cto (engineering)
│   ├── chief-architect
│   ├── lead-engineer
│   │   ├── backend-engineer
│   │   └── frontend-engineer
│   ├── ai-engineer (ai)
│   ├── data-engineer (data)
│   └── security-engineer
├── cfo (finance)
│   └── financial-analyst
├── coo (operations)
│   ├── devops-engineer
│   └── operations-manager
├── cmo (marketing)
│   ├── product-manager
│   ├── technical-writer
│   └── content-writer
├── chro (human-resources)
│   └── recruiter
└── clo (legal)
    └── legal-counsel
```

**21 agents across 9 departments.**

### 3.3 Departments

Defined in `company/departments.yaml`. 9 departments, each with an executive and agent list:

| Department | Executive | Agents |
|------------|-----------|--------|
| executive | human-ceo | chief-of-staff |
| engineering | cto | chief-architect, lead-engineer, backend-engineer, frontend-engineer |
| ai | cto | ai-engineer |
| data | cto | data-engineer |
| finance | cfo | financial-analyst |
| operations | coo | devops-engineer, operations-manager |
| marketing | cmo | product-manager, technical-writer, content-writer |
| human-resources | chro | recruiter |
| legal | clo | legal-counsel |

The PromptBuilder uses this to inject team context into system prompts.

### 3.4 Model Tiers

Defined in `company/models.yaml`. Each tier maps to a provider+model pair with a fallback chain:

| Tier | Use Case | Provider Priority |
|------|----------|-------------------|
| `fast` | Simple tasks, drafts | ollama→openai |
| `standard` | General work | openai→ollama |
| `premium` | Complex reasoning | openai→ollama |

Agent overrides map specific agents to tiers (e.g., `cto: premium`, `content-writer: fast`).

`ModelResolver.resolve(agent_id)` walks the override → tier → provider chain and returns a `ResolvedModel(provider, model, tier, description)`.

### 3.5 KPIs

Defined in `company/config/kpis.yaml`. Each department has 1–3 KPIs with targets, units, and measurement frequency. The PromptBuilder injects these into system prompts so agents know their success metrics.

---

## 4. Orchestration: Task Flow

### 4.1 Message Bus

The `MessageBus` is the central task routing layer backed by `FileStore` (JSON files with atomic writes and cross-process locking).

**Task lifecycle:**

```
PENDING → IN_PROGRESS → COMPLETED
    │          │
    │          ├→ FAILED
    │          ├→ ESCALATED
    │          └→ WAITING_APPROVAL → IN_PROGRESS (on approve)
    │
    └→ CANCELLED
```

**Key operations:**
- `send_task()` — create task, append to inbox, broadcast event
- `claim_task()` — atomically set status to IN_PROGRESS
- `complete_task()` / `fail_task()` — terminal states
- `park_for_approval()` — set WAITING_APPROVAL (for T2+ tools)
- `approve_task()` — resume to IN_PROGRESS
- `delegate()` — create child task with parent_task_id

**Priority queue:** Tasks are sorted by `TaskPriority` (URGENT > HIGH > MEDIUM > LOW).

### 4.2 Executor

The `Executor` is the task consumer loop:

```
tick():
  1. dlq.process()          — retry dead-lettered tasks
  2. get_pending_tasks()    — sorted by priority
  3. for each task:
     a. claim_task()
     b. audit record
     c. memory recall (episodic context)
     d. permission check (if tool specified)
        ├→ FAIL if not authorized
        ├→ PARK if needs approval (T2+)
        └→ CONTINUE
     e. call agent_runner_fn(task)  [LLM call]
     f. complete_task(result)
     g. audit + memory record
```

**Integration points:**
- `agent_runner_fn` — injectable callable (defaults to `AgentRunner.run`)
- `permission_checker` — `PermissionChecker` instance
- `hitl_gate` — lazily created `HITLGate` for T2+ approvals
- `agent_lookup_fn` — resolves agent_id → Agent model for permission checks

### 4.3 AgentRunner

`AgentRunner` is the LLM execution layer:

```
run(agent_id, task):
  1. registry.find(agent_id)          — get Agent model
  2. resolver.resolve(agent_id)       — get provider+model
  3. prompt_builder.build(agent)       — generate system prompt
  4. memory.recall_context(query)      — fetch relevant memory
  5. provider.complete(prompt, system) — call LLM
  6. memory.record_task_outcome()      — store result
  7. return {agent, response, model_info}
```

### 4.4 Workflow Engine

Workflows are YAML-defined multi-step orchestration scripts (`company/workflows.yaml`).

**4 workflows defined:**

| Workflow | Owner | Steps | Description |
|----------|-------|-------|-------------|
| `daily-executive-briefing` | chief-of-staff | 3 | Collect metrics → Analyze → Report |
| `software-development` | cto | 5 | Define → Assign → Implement → Review → Deploy |
| `incident-response` | cto | 5 | Detect → Escalate → Investigate → Resolve → Postmortem |
| `hiring` | chief-of-staff | 4 | Review → Register → Generate → Validate |

**Step model:**
```yaml
- id: execute
  instruction: "Implement the solution"
  assignee: backend-engineer
  tier: T0                    # permission tier
  depends_on: [assign_agent]  # dependency graph
  tags: [execution, engineering]
```

**Engine behavior:**
1. `start_workflow()` — create `WorkflowRun`, advance to first unlocked steps
2. `_advance_steps()` — for each step whose dependencies are met:
   - `send_task()` with metadata `{workflow_id, run_id, step_id, tier}`
   - If `requires_approval` → `park_for_approval()`, pause advancement
3. `complete_step()` — mark step done, advance to next unlocked steps
4. `approve_step()` — resume a paused approval step
5. `cancel_workflow()` — cancel all pending/in-progress tasks

---

## 5. Permissions Enforcement

### 5.1 Tier System

Five tiers of increasing sensitivity:

| Tier | Name | Approval | Example Tools |
|------|------|----------|---------------|
| T0 | Auto | None | read, search, grep, dashboard |
| T1 | Soft | None (logged) | write, edit, planning, finance |
| T2 | Gate | Single human | python, git, javascript, sql, llm |
| T3 | Dual | Two humans | docker, shell, deploy, execute |
| T4 | Board | Board approval | legal, budget, approve, decide |

### 5.2 Validation Flow

```
Agent has tools: ["python", "git"]
Tool "python" maps to T2_GATE

PermissionChecker.validate_action(agent, "python"):
  1. Check agent.permissions contains required_permission
  2. Check tool tier allows the action
  3. Return (approved, tier, error)

PermissionChecker.requires_approval(agent, "python"):
  1. Get tier for tool
  2. If T2+ → needs approval
  3. Return (needs_approval, tier)
```

### 5.3 HITLGate

When a T2+ task is claimed:
1. `HITLGate.park_task()` creates an `ApprovalRequest` and parks the task → records to memory
2. Human reviews via `permissions approve <request_id>` CLI
3. `HITLGate.approve_task()` records decision to memory, resumes task
4. `HITLGate.reject_task()` records rejection to memory, fails the task
5. `check_expired()` auto-rejects expired requests, records expiry to memory

---

## 6. Memory System

### 6.1 Six Memory Types

| Type | Purpose | Example |
|------|---------|---------|
| `episodic` | Task outcomes and events | "Completed deploy to prod" |
| `semantic` | Knowledge and facts | "Our stack uses PostgreSQL 15" |
| `procedural` | How-to knowledge | "Deploy steps: build→test→push" |
| `relational` | Agent relationships | "CTO reports to CEO" |
| `temporal` | Time-based patterns | "Deploy frequency increased 20%" |
| `aggregate` | Summaries | Consolidated department metrics |

### 6.2 Lifecycle

- **Record:** Every task claim, completion, and failure writes to `episodic.json`
- **Recall:** Before executing a task, `recall_context()` searches episodic/semantic/procedural memory
- **Consolidation:** Every N ticks, old episodic entries aggregate into semantic/procedural
- **Pruning:** Low-relevance entries removed after configurable TTL
- **Dedup:** Near-duplicate entries merged during consolidation

---

## 7. Prompt System

`PromptBuilder.build(agent)` generates a system prompt from 7 sections:

1. **Identity** — "You are X, serving as Y at LightSpeed Holdings"
2. **Role** — type, department, tools, permissions
3. **Department** — executive, teammates
4. **KPIs** — department-specific success metrics
5. **Workflows** — owned workflow step sequences
6. **Hierarchy** — reporting line
7. **Guidelines** — behavioral instructions

---

## 8. Config Alignment Rules

The following rules keep config files consistent:

1. Every agent in `agent-registry.json` must have a `department` that exists in `departments.yaml`
2. Every department in `departments.yaml` must list agents that exist in `agent-registry.json`
3. Executive agents (CEO, CTO, CFO, etc.) should be in their own `executive` department or their functional department
4. Cross-department agents (ai-engineer, data-engineer) report to the functional executive (cto) but live in their own department

---

## 9. File Layout

```
company/
├── agent-registry.json     ← 21 agent definitions
├── departments.yaml        ← 9 department mappings
├── models.yaml             ← 3 model tiers + agent overrides
├── workflows.yaml          ← 4 orchestration workflows
└── config/
    └── kpis.yaml           ← per-department KPIs

src/lightspeed_agents/
├── agents/                 ← loader.py (reads agent-registry.json)
├── builder/                ← code generation for new agents
├── cli/commands/           ← Typer CLI subcommands
├── core/                   ← AgentLoop, ToolRunner, CostTracker, AgentRunner
├── memory/                 ← 6-type memory engine
├── message_bus/            ← MessageBus, Executor, FileStore, Audit, DLQ
├── models/                 ← Agent model, ModelResolver
├── permissions/            ← Tiers, ToolRegistry, Checker, HITLGate, Approval
├── prompts/                ← PromptBuilder
├── providers/              ← OllamaProvider, OpenAIProvider
├── registry/               ← global agent registry
└── workflow/               ← WorkflowEngine, models, loader

tests/
├── test_permissions_*.py   ← 63 tests for permissions
├── test_workflow_*.py      ← workflow engine tests
├── test_engine.py          ← memory engine tests
├── test_message_bus.py     ← message bus tests
├── test_cost_tracker.py    ← 11 tests for CostTracker
├── test_tool_runner.py     ← 18 tests for ToolRunner
├── test_agent_loop.py      ← 14 tests for AgentLoop
├── test_audit_enhanced.py  ← 16 tests for enhanced AuditStore
└── ...                     ← 248+ tests total
```

---

## 12. Sprint 2: Agentic Core

### 12.1 AgentLoop

The `AgentLoop` implements a ReAct (Reasoning + Acting) pattern for multi-turn agent execution:

```
AgentLoop.run(task):
  1. reset_task_cost()
  2. for each iteration (max: MAX_ITERATIONS):
     a. Check budget (cost_tracker.check_budget())
     b. Build prompt with task + history
     c. Call LLM (provider.complete())
     d. Parse response for actions
     e. If action found:
        - Execute via ToolRunner
        - Add observation to history
        - Log iteration to audit
     f. If no action: return final response
  3. Return max iterations exceeded error
```

**Key features:**
- Configurable iteration limit (default: 10)
- Budget enforcement per task
- Tool execution with sandboxing
- Full audit trail of iterations

### 12.2 ToolRunner

The `ToolRunner` provides sandboxed execution of agent tool calls:

| Tool | Permission | Description |
|------|------------|-------------|
| read | T0 | Read file contents |
| write | T1 | Write file contents |
| edit | T1 | Edit file contents |
| search | T0 | Search files by pattern |
| grep | T0 | Search file contents |
| python | T2 | Execute Python code |
| git | T2 | Execute Git commands |

**Safety features:**
- Path validation (prevents directory traversal)
- Dangerous tool blocking (rm, sudo, etc.)
- Timeout enforcement (30s default)
- Output size limits

### 12.3 CostTracker

The `CostTracker` manages LLM costs with budget enforcement:

```python
cost_tracker = CostTracker(
    daily_budget=10.0,      # $10/day
    task_budget=1.0,         # $1/task
    model_pricing={
        "gpt-4o": {"input": 0.0025, "output": 0.005},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    }
)

# Track costs
cost_tracker.record_cost(
    model="gpt-4o",
    input_tokens=1500,
    output_tokens=500,
    task_id="task-123"
)

# Check budgets
within_budget = cost_tracker.check_budget()
summary = cost_tracker.get_summary()
```

### 12.4 Enhanced AuditStore

The `AuditStore` now supports correlation-based tracing:

```python
# Log with correlation
audit_store.log_task_claimed(task_id, agent_id, correlation_id="trace-123")
audit_store.log_tool_call(task_id, agent_id, "python", "print('hello')", correlation_id="trace-123")
audit_store.log_cost(task_id, agent_id, 0.025, correlation_id="trace-123")

# Trace a task
trace = audit_store.get_task_trace(task_id)

# Trace a correlation
trace = audit_store.get_correlation_trace("trace-123")
```

---

## 13. Data Flow: End-to-End Example

**Scenario:** CEO requests daily briefing

```
1. CLI: lightspeed company run daily-executive-briefing
2. WorkflowEngine.start_workflow("daily-executive-briefing")
3. Creates WorkflowRun, calls _advance_steps()
4. Step "collect_metrics" (assignee: coo, tier: T0)
   → send_task() to MessageBus
   → Executor.tick() picks it up
   → PermissionChecker: T0, no approval needed
   → AgentRunner.run("coo", "Collect KPI metrics...")
     → ModelResolver: coo → standard → openai/gpt-4o-mini
     → PromptBuilder.build(coo) → system prompt with KPIs
     → OllamaProvider.complete() → LLM response
   → complete_task(result)
   → MemoryEngine.record_task_outcome()
5. WorkflowEngine.complete_step("collect_metrics")
6. Next step "analyze_status" unlocked (depends: collect_metrics)
7. Repeats until workflow COMPLETED
8. Final briefing stored in memory, available for recall
```

---

## 14. Extensibility Points

| Extension | How |
|-----------|-----|
| New agent | Add to `agent-registry.json`, run `load_agents()` |
| New tool | Register in `ToolRegistry` with tier |
| New workflow | Add YAML to `workflows.yaml` |
| New provider | Implement `LLMProvider`, register in provider registry |
| New memory type | Add to `MEMORY_TYPES`, create `record_*()` method |
| New CLI command | Add Typer subcommand in `cli/commands/` |
| Custom executor hook | Inject `agent_runner_fn` into `Executor` |
