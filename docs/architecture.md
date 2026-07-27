# LightSpeed Holdings — System Architecture

## 1. Overview

LightSpeed Holdings is a corporate simulation framework where an organization is modeled as a team of AI agents. Each agent has a role, department, tools, permissions, and a reporting line. Tasks flow through a message bus, are orchestrated by workflows, enforced by permissions, and recalled from memory.

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

## 2. Company Bootstrapping

### 2.1 Agent Registry

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
        "permissions": ["edit"]
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

**Loading:** `agents/loader.py` reads the JSON and populates the global `registry` (a `Registry` instance). Every CLI command and the `AgentRunner` call `load_agents()` first.

### 2.2 Organizational Hierarchy

```
human-ceo (executive)
├── chief-of-staff (executive)
├── cto (engineering)
│   ├── lead-engineer
│   │   ├── backend-engineer
│   │   └── frontend-engineer
│   ├── ai-engineer (ai)
│   └── data-engineer (data)
├── cfo (finance)
│   ├── financial-analyst
│   └── accountant
├── coo (operations)
│   └── operations-manager
├── cmo (marketing)
│   └── content-writer
├── chro (human-resources)
│   └── recruiter
└── clo (legal)
    └── legal-counsel
```

**17 agents across 9 departments.**

### 2.3 Departments

Defined in `company/departments.yaml`. 9 departments, each with an executive and agent list:

| Department | Executive | Agents |
|------------|-----------|--------|
| executive | human-ceo | chief-of-staff |
| engineering | cto | lead-engineer, backend-engineer, frontend-engineer |
| ai | cto | ai-engineer |
| data | cto | data-engineer |
| finance | cfo | financial-analyst, accountant |
| operations | coo | operations-manager |
| marketing | cmo | content-writer |
| human-resources | chro | recruiter |
| legal | clo | legal-counsel |

The PromptBuilder uses this to inject team context into system prompts.

### 2.4 Model Tiers

Defined in `company/models.yaml`. Each tier maps to a provider+model pair with a fallback chain:

| Tier | Use Case | Provider Priority |
|------|----------|-------------------|
| `fast` | Simple tasks, drafts | ollama→openai |
| `standard` | General work | openai→ollama |
| `premium` | Complex reasoning | openai→ollama |

Agent overrides map specific agents to tiers (e.g., `cto: premium`, `content-writer: fast`).

`ModelResolver.resolve(agent_id)` walks the override → tier → provider chain and returns a `ResolvedModel(provider, model, tier, description)`.

### 2.5 KPIs

Defined in `company/config/kpis.yaml`. Each department has 1–3 KPIs with targets, units, and measurement frequency. The PromptBuilder injects these into system prompts so agents know their success metrics.

---

## 3. Orchestration: Task Flow

### 3.1 Message Bus

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

### 3.2 Executor

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

### 3.3 AgentRunner

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

### 3.4 Workflow Engine

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

## 4. Permissions Enforcement

### 4.1 Tier System

Five tiers of increasing sensitivity:

| Tier | Name | Approval | Example Tools |
|------|------|----------|---------------|
| T0 | Auto | None | read, search, grep, dashboard |
| T1 | Soft | None (logged) | write, edit, planning, finance |
| T2 | Gate | Single human | python, git, javascript, sql, llm |
| T3 | Dual | Two humans | docker, shell, deploy, execute |
| T4 | Board | Board approval | legal, budget, approve, decide |

### 4.2 Validation Flow

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

### 4.3 HITLGate

When a T2+ task is claimed:
1. `HITLGate.park_task()` creates an `ApprovalRequest` and parks the task → records to memory
2. Human reviews via `permissions approve <request_id>` CLI
3. `HITLGate.approve_task()` records decision to memory, resumes task
4. `HITLGate.reject_task()` records rejection to memory, fails the task
5. `check_expired()` auto-rejects expired requests, records expiry to memory

---

## 5. Memory System

### 5.1 Six Memory Types

| Type | Purpose | Example |
|------|---------|---------|
| `episodic` | Task outcomes and events | "Completed deploy to prod" |
| `semantic` | Knowledge and facts | "Our stack uses PostgreSQL 15" |
| `procedural` | How-to knowledge | "Deploy steps: build→test→push" |
| `relational` | Agent relationships | "CTO reports to CEO" |
| `temporal` | Time-based patterns | "Deploy frequency increased 20%" |
| `aggregate` | Summaries | Consolidated department metrics |

### 5.2 Lifecycle

- **Record:** Every task claim, completion, and failure writes to `episodic.json`
- **Recall:** Before executing a task, `recall_context()` searches episodic/semantic/procedural memory
- **Consolidation:** Every N ticks, old episodic entries aggregate into semantic/procedural
- **Pruning:** Low-relevance entries removed after configurable TTL
- **Dedup:** Near-duplicate entries merged during consolidation

---

## 6. Prompt System

`PromptBuilder.build(agent)` generates a system prompt from 7 sections:

1. **Identity** — "You are X, serving as Y at LightSpeed Holdings"
2. **Role** — type, department, tools, permissions
3. **Department** — executive, teammates
4. **KPIs** — department-specific success metrics
5. **Workflows** — owned workflow step sequences
6. **Hierarchy** — reporting line
7. **Guidelines** — behavioral instructions

---

## 7. Config Alignment Rules

The following rules keep config files consistent:

1. Every agent in `agent-registry.json` must have a `department` that exists in `departments.yaml`
2. Every department in `departments.yaml` must list agents that exist in `agent-registry.json`
3. Executive agents (CEO, CTO, CFO, etc.) should be in their own `executive` department or their functional department
4. Cross-department agents (ai-engineer, data-engineer) report to the functional executive (cto) but live in their own department

---

## 8. File Layout

```
company/
├── agent-registry.json     ← 17 agent definitions
├── departments.yaml        ← 6 department mappings
├── models.yaml             ← 3 model tiers + agent overrides
├── workflows.yaml          ← 4 orchestration workflows
└── config/
    └── kpis.yaml           ← per-department KPIs

src/lightspeed_agents/
├── agents/                 ← loader.py (reads agent-registry.json)
├── builder/                ← code generation for new agents
├── cli/commands/           ← Typer CLI subcommands
├── core/                   ← AgentRunner (LLM execution)
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
└── ...                     ← 248 tests total
```

---

## 9. Data Flow: End-to-End Example

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

## 10. Extensibility Points

| Extension | How |
|-----------|-----|
| New agent | Add to `agent-registry.json`, run `load_agents()` |
| New tool | Register in `ToolRegistry` with tier |
| New workflow | Add YAML to `workflows.yaml` |
| New provider | Implement `LLMProvider`, register in provider registry |
| New memory type | Add to `MEMORY_TYPES`, create `record_*()` method |
| New CLI command | Add Typer subcommand in `cli/commands/` |
| Custom executor hook | Inject `agent_runner_fn` into `Executor` |
