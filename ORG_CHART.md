# Light Speed Holdings — Organizational Chart (Updated)

```mermaid
org-chart
    human-ceo[human-ceo<br/>Final Authority<br/>T4 Approvals]
    chief-of-staff[chief-of-staff<br/>Executive Oversight<br/>Coordination]
    ceo-advisor[ceo-advisor<br/>Executive Coaching<br/>Strategy Advisory]
    
    chief-legal-officer[chief-legal-officer<br/>Legal & Compliance<br/>Risk Management]
    cto[cto<br/>Technology, Architecture<br/>Security]
    cfo[cfo<br/>Budget, Cost Tracking<br/>Resource Allocation]
    coo[coo<br/>Operations, Process Opt<br/>Incident Management]

    chief-architect[chief-architect<br/>System Design, ADRs<br/>Scalability]
    lead-engineer[lead-engineer<br/>Implementation, Code Quality<br/>Mentoring]
    ai-engineer[ai-engineer<br/>LLM Integration, Prompts<br/>Memory, Agent Loop]
    data-engineer[data-engineer<br/>Pipelines, Knowledge Graph<br/>Analytics]
    security-engineer[security-engineer<br/>Permissions, Audit<br/>Compliance]

    backend-engineer[backend-engineer<br/>Core Platform, APIs<br/>Database]
    frontend-engineer[frontend-engineer<br/>Dashboard, CLI<br/>UI/UX]
    qa-engineer[qa-engineer<br/>Test Strategy, Integration<br/>Performance]

    devops-engineer[devops-engineer<br/>CI/CD, Deployment<br/>Infrastructure, Monitoring]

    product-manager[product-manager<br/>Roadmap, Priorities<br/>User Stories]
    technical-writer[technical-writer<br/>API Docs, User Guides<br/>Architecture Docs]

    human-ceo --> chief-of-staff
    human-ceo --> ceo-advisor

    chief-of-staff --> chief-legal-officer
    chief-of-staff --> cto
    chief-of-staff --> cfo
    chief-of-staff --> coo
    chief-of-staff -.-> product-manager

    cto --> chief-architect
    cto --> lead-engineer
    cto --> ai-engineer
    cto --> data-engineer
    cto --> security-engineer

    lead-engineer --> backend-engineer
    lead-engineer --> frontend-engineer
    lead-engineer --> qa-engineer

    coo --> devops-engineer

    product-manager --> technical-writer
```

---

## Text-Based Org Chart

```
Light Speed Holdings, Inc.
│
├─ human-ceo (Final Authority, T4 Approvals)
│  │
│  ├─ chief-of-staff (Executive Oversight, Coordination)
│  │  │
│  │  ├─ chief-legal-officer (Legal & Compliance, Risk Management)
│  │  ├─ cto (Technology, Architecture, Security)
│  │  │  ├─ chief-architect
│  │  │  ├─ lead-engineer
│  │  │  │  ├─ backend-engineer
│  │  │  │  ├─ frontend-engineer
│  │  │  │  └─ qa-engineer
│  │  │  ├─ ai-engineer
│  │  │  ├─ data-engineer
│  │  │  └─ security-engineer
│  │  ├─ cfo (Budget, Cost Tracking, Resource Allocation)
│  │  └─ coo (Operations, Process Optimization, Incident Management)
│  │     └─ devops-engineer
│  │  │
│  │  └─► product-manager (Roadmap, Priorities) ── technical-writer (API Docs)
│  │
│  └─ ceo-advisor (Executive Coaching, Strategy Advisory) ── No Direct Reports
```

---

## Department Summary

| Department | Executive | Agents | Count |
|------------|-----------|--------|-------|
| **Executive** | human-ceo | chief-of-staff, ceo-advisor | 3 |
| **Operations/Coordination** | chief-of-staff | product-manager, technical-writer | 2 |
| **Legal** | chief-of-staff | chief-legal-officer | 1 |
| **Engineering** | cto | chief-architect, lead-engineer, backend-engineer, frontend-engineer, qa-engineer, data-engineer | 6 |
| **AI/ML** | cto | ai-engineer | 1 |
| **Security** | cto | security-engineer | 1 |
| **Operations/DevOps** | coo | devops-engineer | 1 |
| **Finance** | cfo | — | 1 |
| **Total** | | | **18 agents** |

---

## Authority & Tier Mapping

| Role | Max Tier | Approval Authority | Reports To |
|------|----------|-------------------|------------|
| human-ceo | T4 (BOARD) | Final decisions, legal, budget, production | — |
| chief-of-staff | T3 (DUAL) | Cross-dept coordination, executive oversight | human-ceo |
| ceo-advisor | None | Advisory only | human-ceo |
| chief-legal-officer | T4 (LEGAL) | Legal risk, compliance, contracts | chief-of-staff |
| cto | T3 (DUAL) | Architecture, tech decisions, security policy | chief-of-staff |
| cfo | T3 (DUAL) | Budget allocation, cost approval, resource planning | chief-of-staff |
| coo | T3 (DUAL) | Operations, process changes, incident response | chief-of-staff |
| chief-architect | T2 (GATE) | System design, ADRs, scalability decisions | cto |
| lead-engineer | T2 (GATE) | Implementation, code review, tech debt | cto |
| backend/engineer | T2 (GATE) | Code execution, git, deploy to staging | lead-engineer |
| frontend-engineer | T1 (SOFT) | Write docs, edit code, UI changes | lead-engineer |
| qa-engineer | T2 (GATE) | Run tests, CI pipelines, performance tests | lead-engineer |
| ai-engineer | T2 (GATE) | LLM prompts, model config, memory ops | cto |
| data-engineer | T2 (GATE) | Data pipelines, analytics queries | cto |
| security-engineer | T3 (DUAL) | Permissions, audit, compliance | cto |
| devops-engineer | T3 (DUAL) | Docker, deploy, infrastructure, monitoring | coo |
| product-manager | T1 (SOFT) | Roadmap, priorities, user stories | chief-of-staff |
| technical-writer | T0 (AUTO) | Read, search, write docs | product-manager |

---

## Escalation Path (Updated)

```
Specialist (Engineer, PM, etc.)
         │
         ▼ (15 min SLA)
Executive (CTO, CFO, COO, Lead Engineer)
         │
         ▼ (Cross-department)
CHIEF OF STAFF ←── Coordinates resolution
         │
         ▼ (Business-critical: budget, legal, production)
HUMAN CEO ←── Final decision
         ▲
         │
CEO ADVISOR ──→ Provides recommendation *to* CEO (not in chain of command)

LEGAL MATTERS:
Specialist/Executive → Chief Legal Officer → Chief of Staff → human-ceo
```

---

*Generated from AGENTS.md v1.1 — Light Speed Holdings, Inc.*
*Effective: July 28, 2026*