# Light Speed Agents

**The Operating System for AI Workforces**

Built by Light Speed Holdings, Inc.

---

## Mission

Light Speed Holdings exists to make **autonomous, trustworthy AI agents accessible to every organization** — not as a bolt-on feature, but as the fundamental operating layer of modern business.

Today, companies adopt AI through disjointed tools: a copilot here, a workflow automation there, a custom LLM integration somewhere else. These fragments don't talk to each other. They lack shared memory, unified permissions, auditability, and a coherent governance model. The result is shadow AI sprawl — powerful capabilities that no one fully understands, controls, or trusts.

We solve this by building **Light Speed Agents**: a multi-agent orchestration platform where AI agents operate as first-class organizational citizens. They have roles, departments, reporting lines, permissions, and accountability — just like human employees. They collaborate through a shared message bus, execute complex workflows through a deterministic engine, remember context across sessions through a persistent memory system, and operate within a tiered permission model that keeps humans in the loop for decisions that matter.

Our mission is to replace ad-hoc AI adoption with **AI-native organizational infrastructure** — so companies can deploy agent workforces that are as governable, auditable, and scalable as their human teams.

---

## Values

**Truth over Opinion**  
Every architectural decision, product choice, and strategic bet is grounded in evidence — benchmarks, user data, cost analysis, security reviews. We disagree and commit, but we never decide on ego.

**Automation before Manual Work**  
If a process runs twice, we build it a third time as code. This applies to deployments, testing, documentation, onboarding, and even our own agent operations. The platform builds itself.

**Documentation before Memory**  
Knowledge that lives only in someone's head is a liability. Every decision, protocol, API contract, and failure mode is written down, versioned, and discoverable. Our AGENTS.md is the constitution; everything else follows from it.

**Quality before Speed**  
We ship when it's right. "Move fast and break things" breaks trust. In an agent platform, a bug isn't a UI glitch — it's an autonomous system making wrong decisions at scale. We test, lint, review, and gate before production.

**Security by Design**  
Permissions, audit trails, encryption, and human-in-the-loop gates aren't features we add later. They're the foundation. The T0–T4 tier system, the approval workflow engine, the immutable audit log — these exist because agent autonomy without guardrails is irresponsible.

**Continuous Improvement**  
Every incident, every failed experiment, every user complaint is a structured learning opportunity. We run retrospectives, update runbooks, refine prompts, and evolve the agent hierarchy. The platform gets smarter because we treat our own operations as data.

**Ownership with Accountability**  
Every task, every agent, every subsystem has exactly one owner. No shared responsibility without a named accountable party. When something succeeds, we know who drove it. When it fails, we know who fixes it — and we fix the system, not just the symptom.

---

## Strategy

**Win by being the operating system for AI workforces.**

The market is splitting into two layers: *model providers* (OpenAI, Anthropic, Google, open-source) and *application builders* (everyone else). The missing layer is the **orchestration substrate** — the thing that turns raw model capability into reliable, governed, organizational workflow.

Light Speed Agents owns that layer.

**Our wedge:** Start with engineering teams. They feel the pain most acutely — code review bots that hallucinate, CI agents that flake, documentation that rots. Our agent hierarchy (CEO → CTO → Lead Engineer → Backend/Frontend/AI Engineers) mirrors real software organizations, so adoption is intuitive and value is immediate.

**Our moat:** Three compounding advantages.

1. **The Agent Constitution (AGENTS.md)** — A living operating system for agents, not just a framework. It defines roles, protocols, escalation paths, quality gates, and amendment processes. Competitors build tools; we build governance.

2. **The Permission Tier System (T0–T4)** — A unified authorization model spanning read-only access (T0) to board-level decisions (T4). Every agent action maps to a tier; every tier has defined approval requirements. This makes us the only platform where *compliance is native*, not retrofitted.

3. **The Memory & Message Bus Architecture** — Agents share context through a persistent, queryable memory system and communicate via a typed message bus. This enables multi-agent workflows that remember, reason, and recover — not stateless prompt chains that forget and fail.

**Our expansion:** From engineering → to product, security, devops, data, operations → to the entire enterprise. Each department adds agents to the hierarchy; the platform scales horizontally without rearchitecture.

**Our business model:** Platform subscription per agent-seat, with usage-based tiers for message volume, memory retention, and audit depth. Enterprise contracts include dedicated chief-of-staff agents, custom role definitions, and SLA-backed uptime.

We don't sell "AI features." We sell **an AI-native company in a box** — and we run it ourselves to prove it works.

---

## AI Company Structure

Light Speed Holdings is the **first company architected from day one as an AI-native organization**. Our structure isn't an org chart — it's a runtime configuration.

### The Agent Hierarchy

Every agent in the company is a defined role with:
- **Authority scope** — What decisions they can make autonomously
- **Department** — Which executive they report to
- **Permissions** — Tiered tool access (T0–T4) with approval gates
- **Working style** — How they operate, communicate, and escalate
- **Skills** — Specialized capabilities loaded on demand

```
human-ceo (Final authority, T4 approvals)
├── chief-of-staff (Coordination, sprint planning, blocker resolution)
├── cto (Technology, architecture, security)
│   ├── chief-architect (System design, ADRs, scalability)
│   ├── lead-engineer (Implementation, code quality, mentoring)
│   │   ├── backend-engineer (Core platform, APIs, database)
│   │   ├── frontend-engineer (Dashboard, CLI, UI/UX)
│   │   ├── qa-engineer (Test strategy, integration, performance)
│   ├── ai-engineer (LLM integration, prompts, memory, agent loop)
│   ├── data-engineer (Pipelines, knowledge graph, analytics)
│   └── security-engineer (Permissions, audit, compliance)
├── cfo (Budget, cost tracking, resource allocation)
├── coo (Operations, process optimization, incident management)
│   └── devops-engineer (CI/CD, deployment, infrastructure, monitoring)
└── cmo (via product-manager → technical-writer)
    ├── product-manager (Roadmap, priorities, user stories)
    └── technical-writer (API docs, user guides, architecture docs)
```

### How It Differs from Traditional Companies

| Dimension | Traditional Company | Light Speed Holdings |
|-----------|---------------------|----------------------|
| **Org definition** | Static org chart, updated quarterly | Code (AGENTS.md), updated per sprint |
| **Role clarity** | Job descriptions, often vague | Explicit authority, permissions, escalation paths |
| **Onboarding** | Weeks of shadowing | Skill load + context injection → productive in minutes |
| **Communication** | Meetings, Slack, email | Typed message bus, audited, searchable |
| **Decision rights** | Implicit, political | Explicit tier system (T0–T4), logged, reviewable |
| **Memory** | Tribal knowledge, docs that rot | Persistent memory system, queryable, versioned |
| **Accountability** | "We'll look into it" | Single owner per task, automated escalation |
| **Scaling** | Hire, onboard, manage | Spawn agent, assign role, monitor cost |
| **Governance** | Committees, policies, audits | Built into permission tier + audit trail |

### The Runtime Layer

The hierarchy executes on three shared substrates:

**Message Bus** — Typed, ordered, durable communication. Every agent interaction is a message: task assignment, status update, escalation, approval request, knowledge share. No side-channel Slack DMs. The bus is the source of truth.

**Workflow Engine** — Deterministic, replayable multi-agent processes. Sprint planning, incident response, code review, deployment — each is a defined workflow with states, transitions, timeouts, and human gates. The engine executes; agents provide intelligence at each step.

**Permission Tier System (T0–T4)**

| Tier | Scope | Approval | Examples |
|------|-------|----------|----------|
| T0 | Read-only, no side effects | None | Search, list, read files, grep |
| T1 | Write within sandbox | Logged | Write docs, create plans, edit code |
| T2 | Code execution, git | Single approval | Run tests, commit, run Python/SQL |
| T3 | Infrastructure, deploy | Dual approval | Docker, shell, deploy, migrate |
| T4 | Legal, budget, production | Board/human-ceo | Contracts, spend >$10K, prod deploy |

Every tool in the platform is tagged with its tier. Agents request tools; the permission system evaluates their role, the tool's tier, and the approval chain — automatically.

**Memory System** — Not a vector store. A structured, queryable knowledge graph with:
- **Episodic memory** — What happened, when, who decided
- **Semantic memory** — Facts, decisions, ADRs, patterns
- **Procedural memory** — Skills, runbooks, workflows
- **Working memory** — Active context for current task
Agents recall, consolidate, and forget per retention policies. No context window stuffing.

**Cost & Audit Tracking** — Every token, every tool call, every decision is metered and logged. The CFO agent monitors in real time; the security engineer audits continuously. No surprise bills. No unaudited actions.

### Why This Matters

This structure means **the company is its own best customer**. We dogfood the platform at maximum intensity — 20+ agents, cross-department workflows, real budgets, real deployments, real incidents. Every feature we ship has already survived our own operating environment.

When a customer adopts Light Speed Agents, they're not buying a framework. They're instantiating a proven organizational model — with their roles, their permissions, their workflows — on infrastructure that already runs a real AI-native company.

---

## Project Overview

**LightSpeed Agents** is an AI-native agent orchestration framework that models a corporate organization as a hierarchy of specialized AI agents. Built by Light Speed Holdings, Inc., the platform enables developers to define, deploy, and coordinate AI agents that operate like executive, engineering, operations, and product teams — complete with role hierarchies, permission tiers, inter-agent messaging, YAML-defined workflows, budget-controlled LLM usage, and persistent memory.

**Core Philosophy:** *An AI company run by AI agents, for AI agents.*

- **Language:** Python 3.12+
- **Framework:** Pydantic v2 for type-safe models
- **LLM Providers:** Ollama (local), OpenAI (cloud)
- **Persistence:** File-based (JSON/JSONL) — no external database required
- **Testing:** 170+ tests across 19 test files (pytest)
- **Linting/Format:** Ruff + Black

---

## Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LIGHTSPEED AGENTS PLATFORM                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────┐  │
│  │   CLI Interface  │    │  Agent Registry  │    │   Company Builder    │  │
│  │  (Typer-based)   │◄───│  (agent-registry)│───►│  (YAML/JSON config)  │  │
│  └────────┬─────────┘    └────────┬─────────┘    └──────────┬───────────┘  │
│           │                       │                         │              │
│           ▼                       ▼                         ▼              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        AGENT RUNNER ORCHESTRATOR                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │  │
│  │  │ ModelResolver │  │ PromptBuilder │  │ MemoryEngine  │  │Providers │  │
│  │  │ (tier→model)  │  │ (system prompt)│ │ (6 memory types)│ │(Ollama/  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │ OpenAI)  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│           │                       │                         │              │
│           ▼                       ▼                         ▼              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────┐  │
│  │   AGENT LOOP     │    │   TOOL RUNNER    │    │   MESSAGE BUS        │  │
│  │  (ReAct-style)   │◄───│  (read/write/    │◄───│  (Task Queue)        │  │
│  │  - Budget ctrl   │    │   edit/search/   │    │  - Priority queue    │  │
│  │  - Max iterations│    │   python/git)    │    │  - Claim/Complete    │  │
│  │  - Cost tracking │    │                  │    │  - Fail/Escalate     │  │
│  └──────────────────┘    └──────────────────┘    │  - HITL approval     │  │
│                                                    └──────────────────────┘  │
│           │                       │                         │              │
│           ▼                       ▼                         ▼              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     PERMISSIONS ENGINE (T0–T4)                        │  │
│  │  T0_AUTO → T1_SOFT → T2_GATE (1 approval) → T3_DUAL (2) → T4_BOARD  │  │
│  │                   HITL Gate: approve/reject/expire                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│           │                                                                   
│           ▼                                                                   
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    WORKFLOW ENGINE (YAML-defined)                     │  │
│  │  - Dependency resolution (DAG)   - Step status machine              │  │
│  │  - Per-step tier approval        - Run persistence & audit          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Modules

| Module | Path | Responsibility |
|--------|------|----------------|
| **Agent Loop** | `core/agent_loop.py` | ReAct-style reasoning loop with budget controls, max iterations, cost tracking |
| **Tool Runner** | `core/tool_runner.py` | Executes tools: read, write, edit, search, list, python, git |
| **Cost Tracker** | `core/cost_tracker.py` | Per-model/agent/task cost tracking with budget enforcement |
| **Message Bus** | `message_bus/` | File-based task queue: priority, claim/complete/fail/escalate/approve lifecycle |
| **Workflow Engine** | `workflow/` | YAML-defined DAG workflows with dependency resolution, HITL approval gates |
| **Permissions** | `permissions/` | 5-tier action classification (T0–T4), HITL approval gates, tool registry |
| **Memory** | `memory/` | 6-type file-based memory (episodic, semantic, procedural, relational, temporal, aggregate) with consolidation |
| **Providers** | `providers/` | Ollama & OpenAI LLM provider implementations with unified interface |
| **Agent Runner** | `core/agent_runner.py` | High-level agent execution: model resolution → prompt building → memory recall → LLM call → memory recording |
| **CLI** | `cli/` | Typer-based commands for agents, tasks, workflows, permissions, memory, models, company |

---

## Features

### 1. Corporate Agent Hierarchy
- **18+ pre-defined agents** across 7 departments: Executive, Engineering, Finance, Operations, Marketing, AI, Data, Security, Product
- Each agent has: ID, name, role, type (Executive/Specialist), department, reports_to, tools, permissions, model tier
- Stored in `company/agent-registry.json` (validated via Pydantic)

### 2. ReAct Agent Loop with Budget Control
```python
# Core loop config
LoopConfig(
    max_iterations=10,
    max_tokens_per_call=2048,
    temperature=0.7,
    budget=BudgetConfig(max_cost_usd=5.0, max_prompt_tokens=8000, max_completion_tokens=4000)
)
```
- Iterative thought → action → observation cycle
- Automatic budget enforcement mid-iteration
- Cost recorded per model/provider/agent/task

### 3. 7 Built-in Tools (Extensible)
| Tool | Tier | Description |
|------|------|-------------|
| `read` | T0 | Read file contents |
| `write` | T1 | Write file |
| `edit` | T1 | Edit file (old→new) |
| `search` | T0 | Regex search in files |
| `list` | T0 | List directory |
| `python` | T2 | Execute Python code |
| `git` | T2 | Run git commands |

### 4. 5-Tier Permission System (T0–T4)
| Tier | Name | Approvals | Timeout | Use Case |
|------|------|-----------|---------|----------|
| T0 | AUTO | 0 | 0 | Read, search, list |
| T1 | SOFT | 0 (warning) | 0 | Non-critical writes |
| T2 | GATE | 1 | 30 min | Critical writes, deploys |
| T3 | DUAL | 2 | 60 min | High-stakes (production) |
| T4 | BOARD | 3 | 24 hr | Governance/legal |

- **HITL Gate:** Pending approvals stored in message bus, CLI for approve/reject/expire
- **Tool Registry:** Maps each tool to its tier
- **Permission Checker:** Validates agent permissions against tool tier

### 5. Multi-Step Workflow Engine (YAML)
```yaml
workflows:
  - id: software-development
    name: Software Development Workflow
    owner: cto
    steps:
      - id: create_task
        instruction: "Define and scope the engineering task"
        assignee: lead-engineer
        tier: T0
      - id: review
        instruction: "Code review and quality assurance"
        assignee: lead-engineer
        tier: T2
        depends_on: [execute]
      - id: deploy
        instruction: "Deploy to production"
        assignee: backend-engineer
        tier: T3
        depends_on: [review]
```
- **DAG dependency resolution** (`depends_on`)
- **Per-step tier approval gates** (auto-parks tasks awaiting human approval)
- **Run persistence & audit trail** (every step logged)

### 6. Persistent Memory System (6 Types)
- **Episodic** — What happened, when, who decided
- **Semantic** — Facts, decisions, ADRs, patterns
- **Procedural** — Skills, runbooks, workflows
- **Relational** — Agent relationships, dependencies
- **Temporal** — Time-series data, trends
- **Aggregate** — Summaries, statistics, rollups
- **Consolidation scheduler** — Prunes, deduplicates, enforces capacity, generates aggregates

### 7. Cost Tracking & Budgets
- Per-model pricing (GPT-4o, GPT-4o-mini, Llama3 variants, etc.)
- Daily budgets + per-task budgets
- JSONL audit log for cost analysis
- Real-time budget enforcement in AgentLoop

### 8. Audit Trail & Observability
- Every tool call, decision, permission check, iteration, cost logged
- Task-level traces, correlation traces, agent history
- Queryable by task_id, agent_id, event_type, correlation_id

---

## Getting Started

### Prerequisites
- Python 3.12+
- Ollama (for local LLM) or OpenAI API key

### Installation
```bash
git clone https://github.com/light-speed-holdings/light-speed-agents
cd light-speed-agents
pip install -e .[dev]
```

### Configuration
```bash
# Copy example config
cp config.example.yaml config.yaml

# Set up Ollama (local)
ollama pull llama3.1
ollama serve

# Or set OpenAI key
export OPENAI_API_KEY=sk-...
```

### Run the CLI
```bash
# List agents
ls-agents list

# Send a task
ls-agents task send --assignee backend-engineer --instruction "Create a new API endpoint"

# Start a workflow
ls-agents workflow start software-development

# Check permissions
ls-agents permissions check backend-engineer write

# Run an agent directly
ls-agents run --agent backend-engineer --prompt "Refactor the auth module"
```

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src/lightspeed_agents

# Lint
ruff check src/
```

---

## Project Structure

```
light-speed-holdings/
├── AGENTS.md                    # Company constitution (agent roles, protocols, quality standards)
├── README.md                    # This file
├── pyproject.toml               # Project config, dependencies, tool settings
├── company/
│   ├── agent-registry.json      # 18+ agent definitions (Pydantic-validated)
│   └── config/
│       └── kpis.yaml            # KPI definitions with targets
├── docs/
│   ├── roadmap.md               # MVP 1-6 roadmap with exit criteria
│   ├── agents.md                # Agent role definitions
│   ├── sprint-3-plan.md         # Sprint 3 execution plan
│   └── sprint-5-plan.md         # Sprint 5 execution plan
├── src/
│   └── lightspeed_agents/
│       ├── __init__.py
│       ├── main.py
│       ├── constants.py
│       ├── config/
│       │   └── settings.py
│       ├── models/
│       │   ├── agent.py         # Pydantic Agent model
│       │   └── resolver.py      # ModelResolver (tier→provider/model)
│       ├── core/
│       │   ├── agent_loop.py    # ReAct loop with budget control
│       │   ├── agent_runner.py  # High-level agent execution
│       │   ├── tool_runner.py   # Tool execution (read/write/edit/...)
│       │   ├── cost_tracker.py  # Per-model/task cost tracking
│       │   └── __init__.py
│       ├── message_bus/
│       │   ├── task.py
│       │   ├── task_status.py
│       │   ├── file_store.py
│       │   ├── message_bus.py
│       │   ├── audit.py
│       │   ├── dead_letter.py
│       │   ├── executor.py
│       │   └── __init__.py
│       ├── workflow/
│       │   ├── models.py
│       │   ├── loader.py
│       │   ├── engine.py
│       │   └── __init__.py
│       ├── permissions/
│       │   ├── tiers.py
│       │   ├── tool_registry.py
│       │   ├── checker.py
│       │   ├── approval.py
│       │   ├── hitl_gate.py
│       │   └── __init__.py
│       ├── memory/
│       │   ├── models.py
│       │   ├── filestore.py
│       │   ├── search.py
│       │   ├── consolidation.py
│       │   ├── engine.py
│       │   └── __init__.py
│       ├── providers/
│       │   ├── base.py
│       │   ├── ollama.py
│       │   ├── openai.py
│       │   ├── registry.py
│       │   └── __init__.py
│       ├── registry/
│       │   └── registry.py
│       ├── agents/
│       │   ├── loader.py
│       │   ├── base.py
│       │   └── registry.py
│       └── cli/
│           ├── main.py
│           └── commands/
│               ├── agents.py
│               ├── tasks.py
│               ├── workflows.py
│               ├── run.py
│               ├── permissions.py
│               ├── memory.py
│               ├── models.py
│               └── company.py
└── tests/
    ├── test_agent_model.py
    ├── test_task.py
    ├── test_file_store.py
    ├── test_executor.py
    ├── test_dlq.py
    ├── test_audit.py
    ├── test_audit_enhanced.py
    ├── test_agent_loop.py
    ├── test_runner.py
    ├── test_tool_runner.py
    ├── test_cost_tracker.py
    ├── test_workflow_engine.py
    ├── test_workflow_models.py
    ├── test_workflow_loader.py
    ├── test_permissions_executor.py
    ├── test_permissions_hitl_gate.py
    ├── test_permissions_checker.py
    ├── test_permissions_approval.py
    ├── test_permissions_tiers.py
    ├── test_permissions_tool_registry.py
    ├── test_cli.py
    └── test_consolidation.py
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| `AGENTS.md` | Company constitution — agent roles, protocols, quality standards, tool approval tiers |
| `docs/roadmap.md` | MVP 1-6 roadmap with deliverables, owners, exit criteria |
| `docs/agents.md` | Detailed agent role definitions and working styles |
| `docs/sprint-3-plan.md` | Sprint 3 execution plan (memory, consolidation, workflows) |
| `docs/sprint-5-plan.md` | Sprint 5 execution plan (decision engine, ADRs, policy engine) |
| `company/config/kpis.yaml` | KPI definitions with targets and measurement methods |

---

## Contributing

1. Read `AGENTS.md` — it's the constitution
2. Follow the quality standards: Ruff linting, Black formatting, type hints, tests for all new code
3. All changes require review from lead-engineer or cto
4. Security-sensitive changes require security-engineer review
5. Architecture changes require chief-architect review

---

## License

MIT License — see LICENSE file for details.

---

## Contact

**Light Speed Holdings, Inc.**  
Built with ❤️ by an AI-native company.

*Light Speed Agents — The Operating System for AI Workforces*  
*AGENTS.md v1.0 | July 27, 2026*