# Light Speed Holdings — Organizational Chart

**Approved by human-ceo | July 28, 2026 | AGENTS.md v1.0**

---

## Mermaid Org Chart

```mermaid
org-chart
    human-ceo[human-ceo<br/>Final Authority<br/>T4 Approvals]
    chief-of-staff[chief-of-staff<br/>Coordination, Sprint Planning<br/>Blocker Resolution<br/>T3 DUAL]
    ceo-advisor[ceo-advisor<br/>Executive Coaching, Strategy<br/>Board Preparation<br/>Advisory Only]
    cto[cto<br/>Technology, Architecture, Security<br/>T3 DUAL]
    cfo[cfo<br/>Budget, Cost Tracking, Resource Allocation<br/>T3 DUAL]
    coo[coo<br/>Operations, Process Opt<br/>Incident Management<br/>T3 DUAL]

    chief-architect[chief-architect<br/>System Design, ADRs<br/>Scalability<br/>T2 GATE]
    lead-engineer[lead-engineer<br/>Implementation, Code Quality<br/>Mentoring<br/>T2 GATE]
    ai-engineer[ai-engineer<br/>LLM Integration, Prompts<br/>Memory, Agent Loop<br/>T2 GATE]
    data-engineer[data-engineer<br/>Pipelines, Knowledge Graph<br/>Analytics<br/>T2 GATE]
    security-engineer[security-engineer<br/>Permissions, Audit<br/>Compliance<br/>T3 DUAL]

    backend-engineer[backend-engineer<br/>Core Platform, APIs<br/>Database<br/>T2 GATE]
    frontend-engineer[frontend-engineer<br/>Dashboard, CLI<br/>UI/UX<br/>T2 GATE]
    qa-engineer[qa-engineer<br/>Test Strategy, Integration<br/>Performance<br/>T2 GATE]

    devops-engineer[devops-engineer<br/>CI/CD, Deployment<br/>Infrastructure, Monitoring<br/>T3 DUAL]

    product-manager[product-manager<br/>Roadmap, Priorities<br/>User Stories<br/>T1 SOFT]
    technical-writer[technical-writer<br/>API Docs, User Guides<br/>Architecture Docs<br/>T0 AUTO]

    human-ceo --> chief-of-staff
    human-ceo --> ceo-advisor
    human-ceo --> cto
    human-ceo --> cfo
    human-ceo --> coo

    cto --> chief-architect
    cto --> lead-engineer
    cto --> ai-engineer
    cto --> data-engineer
    cto --> security-engineer

    lead-engineer --> backend-engineer
    lead-engineer --> frontend-engineer
    lead-engineer --> qa-engineer

    coo --> devops-engineer

    chief-of-staff -.-> product-manager
    product-manager --> technical-writer
```

---

## Text-Based Org Chart

```
Light Speed Holdings, Inc.
│
├─ human-ceo (Final Authority, T4 Approvals)
│  │
│  ├─ chief-of-staff (Coordination, Sprint Planning, Blocker Resolution) [T3 DUAL]
│  │  │
│  │  └─► product-manager (Roadmap, Priorities, User Stories) [T1 SOFT]
│  │        └─► technical-writer (API Docs, User Guides, Architecture Docs) [T0 AUTO]
│  │
│  ├─ ceo-advisor (Executive Coaching, Strategic Advice, Board Preparation) [Advisory Only]
│  │     └─ No direct reports
│  │
│  ├─ cto (Technology, Architecture, Security) [T3 DUAL]
│  │  │
│  │  ├─ chief-architect (System Design, ADRs, Scalability) [T2 GATE]
│  │  ├─ lead-engineer (Implementation, Code Quality, Mentoring) [T2 GATE]
│  │  │  │
│  │  │  ├─ backend-engineer (Core Platform, APIs, Database) [T2 GATE]
│  │  │  ├─ frontend-engineer (Dashboard, CLI, UI/UX) [T2 GATE]
│  │  │  └─ qa-engineer (Test Strategy, Integration, Performance) [T2 GATE]
│  │  ├─ ai-engineer (LLM Integration, Prompts, Memory, Agent Loop) [T2 GATE]
│  │  ├─ data-engineer (Pipelines, Knowledge Graph, Analytics) [T2 GATE]
│  │  └─ security-engineer (Permissions, Audit, Compliance) [T3 DUAL]
│  │
│  ├─ cfo (Budget, Cost Tracking, Resource Allocation) [T3 DUAL]
│  │
│  └─ coo (Operations, Process Optimization, Incident Management) [T3 DUAL]
│     │
│     └─ devops-engineer (CI/CD, Deployment, Infrastructure, Monitoring) [T3 DUAL]
```

---

## Complete Agent Roster (17 Agents)

| # | Role | Reports To | Department | Tier | Authority |
|---|------|------------|------------|------|-----------|
| 1 | human-ceo | — | Executive | T4 BOARD | Final authority, T4 approvals |
| 2 | chief-of-staff | human-ceo | Executive | T3 DUAL | Cross-dept coordination, sprint planning, blocker resolution |
| 3 | ceo-advisor | human-ceo | Executive | Advisory | Executive coaching, strategic advice, board prep, governance |
| 4 | cto | human-ceo | Engineering | T3 DUAL | Architecture, code standards, tool selection, security |
| 5 | cfo | human-ceo | Finance | T3 DUAL | Budget, cost tracking, resource allocation |
| 6 | coo | human-ceo | Operations | T3 DUAL | Process optimization, incident management |
| 7 | chief-architect | cto | Engineering | T2 GATE | System design, ADRs, scalability |
| 8 | lead-engineer | cto | Engineering | T2 GATE | Code quality, sprint tasks, technical docs |
| 9 | backend-engineer | lead-engineer | Engineering | T2 GATE | Core platform, APIs, database, testing |
| 10 | frontend-engineer | lead-engineer | Engineering | T2 GATE | Dashboard, CLI, UI/UX |
| 11 | qa-engineer | lead-engineer | Engineering | T2 GATE | Test strategy, integration, performance |
| 12 | ai-engineer | cto | AI/ML | T2 GATE | LLM integration, prompts, memory, agent loop |
| 13 | data-engineer | cto | Data | T2 GATE | Pipelines, knowledge graph, analytics |
| 14 | security-engineer | cto | Security | T3 DUAL | Permissions, audit, compliance |
| 15 | devops-engineer | coo | Operations | T3 DUAL | CI/CD, deployment, infrastructure, monitoring |
| 16 | product-manager | chief-of-staff (dotted) | Product | T1 SOFT | Roadmap, priorities, user stories |
| 17 | technical-writer | product-manager | Product | T0 AUTO | API docs, user guides, architecture docs |

---

## Reporting Lines

```
human-ceo
├── chief-of-staff
│   └── product-manager (dotted)
│       └── technical-writer
├── ceo-advisor (no direct reports)
├── cto
│   ├── chief-architect
│   ├── lead-engineer
│   │   ├── backend-engineer
│   │   ├── frontend-engineer
│   │   └── qa-engineer
│   ├── ai-engineer
│   ├── data-engineer
│   └── security-engineer
├── cfo
└── coo
    └── devops-engineer
```

---

## Authority & Tier Mapping

| Role | Max Tier | Approval Authority |
|------|----------|-------------------|
| human-ceo | T4 (BOARD) | Final decisions, production deploy, budgets >$10K, legal |
| chief-of-staff | T3 (DUAL) | Cross-dept coordination, sprint planning, blocker resolution |
| ceo-advisor | Advisory | No decision power — coaching, strategy, governance, board prep |
| cto | T3 (DUAL) | Architecture, tech decisions, security policy |
| cfo | T3 (DUAL) | Budget allocation, cost approval, resource planning |
| coo | T3 (DUAL) | Operations, process changes, incident response |
| chief-architect | T2 (GATE) | System design, ADRs, scalability decisions |
| lead-engineer | T2 (GATE) | Implementation, code review, tech debt |
| backend-engineer | T2 (GATE) | Code execution, git, deploy to staging |
| frontend-engineer | T2 (GATE) | Write docs, edit code, UI changes |
| qa-engineer | T2 (GATE) | Run tests, CI pipelines, performance tests |
| ai-engineer | T2 (GATE) | LLM prompts, model config, memory ops |
| data-engineer | T2 (GATE) | Data pipelines, analytics queries |
| security-engineer | T3 (DUAL) | Permissions, audit, compliance |
| devops-engineer | T3 (DUAL) | Docker, deploy, infrastructure, monitoring |
| product-manager | T1 (SOFT) | Roadmap, priorities, user stories |
| technical-writer | T0 (AUTO) | Read, search, write docs |

---

## Escalation Path

```
Specialist → Executive (15 min SLA)
Executive → chief-of-staff (cross-department)
chief-of-staff → human-ceo (business-critical)
CEO Advisor → human-ceo (advisory, not in escalation chain)
```

---

## Department Summary

| Department | Executive | Agents | Count |
|------------|-----------|--------|-------|
| **Executive** | human-ceo | chief-of-staff, ceo-advisor, cto, cfo, coo | 6 |
| **Engineering** | cto | chief-architect, lead-engineer, backend-engineer, frontend-engineer, qa-engineer, data-engineer | 6 |
| **AI/ML** | cto | ai-engineer | 1 |
| **Security** | cto | security-engineer | 1 |
| **Operations** | coo | devops-engineer | 1 |
| **Finance** | cfo | — | 1 |
| **Product** | (via chief-of-staff) | product-manager, technical-writer | 2 |
| **Total** | | | **17 agents** |

---

## Permission Tier Definitions

| Tier | Name | Approvals Required | Timeout | Typical Actions |
|------|------|-------------------|---------|-----------------|
| T0 | AUTO | 0 | — | Read, search, list, grep |
| T1 | SOFT | 0 (warning) | — | Write docs, create plans, edit code |
| T2 | GATE | 1 | 30 min | Run tests, commit, Python/SQL, deploy staging |
| T3 | DUAL | 2 | 60 min | Docker, shell, production deploy, migrate |
| T4 | BOARD | 3 (human-ceo + 2) | 24 hr | Contracts, spend >$10K, prod deploy, legal |

---

## Communication Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│    human-ceo    │────►│  chief-of-staff │────►│ Department Heads │
│   (Strategy)    │     │  (Coordination) │     │  (cto, cfo, coo) │
└────────┬────────┘     └─────────────────┘     └────────┬─────────┘
         │                                                │
         │          ┌───────────────────┐                  │
         └─────────►│   ceo-advisor     │                  │
                    │ (Advisory Only)   │                  │
                    └───────────────────┘                  │
                                                           │
                        ┌──────────────────────────────────┼──────────────────────────────────┐
                        ▼                                  ▼                                  ▼
                 ┌───────────────┐                 ┌───────────────┐                 ┌───────────────┐
                 │ Engineering   │                 │ Operations    │                 │ Product       │
                 │ (cto)         │                 │ (coo)         │                 │ (via cos)     │
                 └───────┬───────┘                 └───────┬───────┘                 └───────┬───────┘
                         │                                 │                                 │
        ┌────────────────┼────────────────┐                │                                 │
        ▼                ▼                ▼                ▼                                 ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               ┌──────────────────┐
│ chief-arch   │ │ lead-engineer│ │ ai-engineer  │ │ devops-eng   │               │ product-manager  │
│              │ │              │ │ data-engineer│ │              │               │ technical-writer │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────────────┘               └──────────────────┘
       │                │                │
       ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ backend-eng  │ │ frontend-eng │ │ qa-engineer  │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

*Generated from AGENTS.md v1.0 — Light Speed Holdings, Inc.*
*Effective: July 28, 2026*
*Approved by: human-ceo*