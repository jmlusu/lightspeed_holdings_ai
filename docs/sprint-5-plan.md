# Sprint 5 Planning: Dashboard & REST API

## Sprint Overview

**Sprint Name:** MVP 5 — Dashboard & REST API  
**Duration:** Weeks 9-10 (August 25 - September 7, 2026)  
**Sprint Goal:** Deliver a production-grade FastAPI REST layer and a CEO-facing operational dashboard that provides real-time visibility into agents, tasks, workflows, costs, and memory across the organization.  
**Sprint Owner:** chief-of-staff  
**Approved by:** human-ceo

---

## Current State Assessment

### What Exists (from Sprints 1-4)

| Component | Module | API Surface | Status |
|-----------|--------|-------------|--------|
| MessageBus | `message_bus/message_bus.py` | In-process only | ✅ Stable |
| Task model | `message_bus/task.py` | Pydantic model | ✅ Stable |
| TaskStatus/TaskPriority | `message_bus/task_status.py` | Enums | ✅ Stable |
| CostTracker | `core/cost_tracker.py` | In-process only | ✅ Stable |
| WorkflowEngine | `workflow/engine.py` | In-process only | ✅ Stable |
| MemoryEngine | `memory/engine.py` | In-process only | ✅ Stable |
| AgentRegistry | `agents/registry.py` | In-process only | ✅ Stable |
| CLI (Typer) | `cli/main.py` | CLI commands | ✅ Stable |
| Services module | `services/__init__.py` | Empty placeholder | 🔄 Ready |
| Configuration | `config/settings.py` | Pydantic settings | ✅ Stable |

### What's Missing for Sprint 5

- ❌ FastAPI application and ASGI server setup
- ❌ REST API endpoints for all subsystems
- ❌ WebSocket support for real-time updates
- ❌ Authentication and API key management
- ❌ OpenAPI documentation and schema exports
- ❌ KPI collectors for all 7 departments
- ❌ Dashboard HTML/JS frontend
- ❌ Real-time event streaming
- ❌ API rate limiting and throttling
- ❌ CORS configuration
- ❌ Health check endpoints

---

## Sprint 5 Goals

### Primary Goal
Expose every core subsystem (MessageBus, CostTracker, WorkflowEngine, MemoryEngine, AgentRegistry) through a well-documented REST API, and provide a real-time CEO dashboard that aggregates KPIs across all 7 departments.

### Key Results

| KR# | Key Result | Target | Measurement |
|-----|-----------|--------|-------------|
| KR1 | REST API endpoints covering all core subsystems | 50+ endpoints | Endpoint count in OpenAPI spec |
| KR2 | WebSocket real-time event stream | Live updates within 200ms | Latency measurement |
| KR3 | CEO Dashboard renders live KPIs | All 7 department KPIs visible | Dashboard screenshot + manual verification |
| KR4 | API response time (p95) | < 100ms for read endpoints | Load test results |
| KR5 | Test coverage for API layer | ≥ 90% | pytest-cov report |
| KR6 | OpenAPI documentation completeness | 100% endpoint coverage | Swagger UI verification |

### Success Criteria

- [ ] FastAPI application starts and serves on configurable host/port
- [ ] All core subsystems accessible via REST endpoints
- [ ] WebSocket pushes task state changes in real time
- [ ] Dashboard shows live KPIs for all 7 departments
- [ ] Authentication (API key) protects write endpoints
- [ ] Health check endpoint returns system status
- [ ] OpenAPI/Swagger docs are self-documenting
- [ ] All endpoints have unit and integration tests
- [ ] No regression in existing CLI functionality

---

## Sprint 5 Epics & User Stories

### Epic 1: FastAPI Application Foundation (HIGH Priority)

**Epic Owner:** backend-engineer  
**Estimated Effort:** 16 hours  
**Dependencies:** None — foundational work

| Story ID | User Story | Acceptance Criteria | Owner | Est. Hours | Priority |
|----------|-----------|---------------------|-------|------------|----------|
| D5-001 | As a developer, I want a FastAPI application factory so that the API is modular and testable | App factory creates FastAPI instance with proper middleware; CORS configured; lifespan events handle startup/shutdown | backend-engineer | 4 | P0 |
| D5-002 | As a developer, I want configuration settings for the API server so that host, port, and auth are configurable | Pydantic Settings class with env var support for API_HOST, API_PORT, API_KEY, CORS_ORIGINS | backend-engineer | 2 | P0 |
| D5-003 | As an operator, I want a health check endpoint so that I can verify system readiness | `GET /api/v1/health` returns status, timestamp, subsystem health (bus, memory, workflow, cost) | backend-engineer | 2 | P0 |
| D5-004 | As an operator, I want a readiness endpoint so that orchestrators can check dependency status | `GET /api/v1/ready` returns per-subsystem readiness with dependency graph | backend-engineer | 2 | P0 |
| D5-005 | As a developer, I want dependency injection for core services so that endpoints are testable | FastAPI Depends() providers for MessageBus, CostTracker, WorkflowEngine, MemoryEngine | backend-engineer | 4 | P0 |
| D5-006 | As a developer, I want exception handlers so that errors return consistent JSON | Custom HTTPException handlers; validation errors return 422 with structured detail | backend-engineer | 2 | P1 |

**Exit Criteria:**
- `uvicorn lightspeed_agents.services.app:create_app --factory` starts the server
- Health check returns 200 OK with subsystem status
- All core services injectable via Depends()
- CORS headers present in responses

---

### Epic 2: Task & MessageBus API (HIGH Priority)

**Epic Owner:** backend-engineer  
**Estimated Effort:** 18 hours  
**Dependencies:** Epic 1 (app foundation)

| Story ID | User Story | Acceptance Criteria | Owner | Est. Hours | Priority |
|----------|-----------|---------------------|-------|------------|----------|
| D5-007 | As an API consumer, I want to list all tasks so that I can see the current workload | `GET /api/v1/tasks` returns paginated list with status, priority, assignee filters | backend-engineer | 3 | P0 |
| D5-008 | As an API consumer, I want to get a specific task so that I can inspect its details | `GET /api/v1/tasks/{task_id}` returns full Task object with timestamps and metadata | backend-engineer | 2 | P0 |
| D5-009 | As an API consumer, I want to create a task so that I can dispatch work through the API | `POST /api/v1/tasks` accepts instruction, receiver_id, priority; returns created Task | backend-engineer | 3 | P0 |
| D5-010 | As an API consumer, I want to update task status so that I can advance work items | `PATCH /api/v1/tasks/{task_id}/status` accepts status transition with validation | backend-engineer | 2 | P0 |
| D5-011 | As an API consumer, I want to query tasks by status so that I can filter work queues | `GET /api/v1/tasks?status=pending&priority=high` returns filtered results | backend-engineer | 2 | P1 |
| D5-012 | As an API consumer, I want to get tasks by agent so that I can see an agent's workload | `GET /api/v1/tasks?receiver_id=frontend-engineer` returns agent-specific tasks | backend-engineer | 2 | P1 |
| D5-013 | As an API consumer, I want to get task statistics so that I can monitor throughput | `GET /api/v1/tasks/stats` returns counts by status, priority, avg completion time | backend-engineer | 2 | P1 |
| D5-014 | As an API consumer, I want to delete a task so that I can clean up obsolete items | `DELETE /api/v1/tasks/{task_id}` soft-deletes task; returns 204 No Content | backend-engineer | 2 | P2 |

**Exit Criteria:**
- Full CRUD operations on tasks via REST
- Filtering and pagination work correctly
- Status transitions are validated (e.g., cannot go from completed to pending)
- Task statistics endpoint returns accurate aggregates

---

### Epic 3: Cost & Budget API (HIGH Priority)

**Epic Owner:** backend-engineer  
**Estimated Effort:** 12 hours  
**Dependencies:** Epic 1 (app foundation)

| Story ID | User Story | Acceptance Criteria | Owner | Est. Hours | Priority |
|----------|-----------|---------------------|-------|------------|----------|
| D5-015 | As a CFO agent, I want to query cost summary so that I can monitor budget consumption | `GET /api/v1/costs/summary` returns total cost, daily cost, budget remaining, by-model breakdown | backend-engineer | 3 | P0 |
| D5-016 | As a CFO agent, I want to query cost history so that I can analyze spending trends | `GET /api/v1/costs/history?days=7` returns daily cost series with token counts | backend-engineer | 3 | P0 |
| D5-017 | As a CFO agent, I want to query costs by model so that I can optimize model selection | `GET /api/v1/costs/by-model` returns per-model cost, token, and call counts | backend-engineer | 2 | P1 |
| D5-018 | As a CFO agent, I want to query costs by agent so that I can attribute spending | `GET /api/v1/costs/by-agent` returns per-agent cost breakdown | backend-engineer | 2 | P1 |
| D5-019 | As an operator, I want to check budget status so that I can prevent overruns | `GET /api/v1/costs/budget` returns daily/task limits, current usage, remaining | backend-engineer | 2 | P0 |

**Exit Criteria:**
- Cost summary returns accurate real-time data
- Historical cost data is queryable with time range filters
- Model and agent cost attribution works correctly
- Budget status shows remaining capacity

---

### Epic 4: Workflow API (MEDIUM Priority)

**Epic Owner:** lead-engineer  
**Estimated Effort:** 16 hours  
**Dependencies:** Epic 1 (app foundation)

| Story ID | User Story | Acceptance Criteria | Owner | Est. Hours | Priority |
|----------|-----------|---------------------|-------|------------|----------|
| D5-020 | As an API consumer, I want to list workflows so that I can see available automations | `GET /api/v1/workflows` returns list of defined workflows with step counts | backend-engineer | 3 | P0 |
| D5-021 | As an API consumer, I want to get workflow details so that I can inspect steps and dependencies | `GET /api/v1/workflows/{workflow_id}` returns full workflow with step graph | backend-engineer | 2 | P0 |
| D5-022 | As an API consumer, I want to start a workflow so that I can trigger automations | `POST /api/v1/workflows/{workflow_id}/start` returns WorkflowRun with initial status | backend-engineer | 3 | P0 |
| D5-023 | As an API consumer, I want to get workflow run status so that I can track progress | `GET /api/v1/workflows/runs/{run_id}` returns run with step results and current status | backend-engineer | 2 | P0 |
| D5-024 | As an API consumer, I want to list all runs for a workflow so that I can see execution history | `GET /api/v1/workflows/{workflow_id}/runs` returns paginated run history | backend-engineer | 2 | P1 |
| D5-025 | As an API consumer, I want to complete a workflow step so that I can advance execution | `POST /api/v1/workflows/runs/{run_id}/steps/{step_id}/complete` advances the run | backend-engineer | 2 | P1 |
| D5-026 | As an API consumer, I want to cancel a workflow run so that I can stop runaway executions | `POST /api/v1/workflows/runs/{run_id}/cancel` sets run to cancelled; cleans up tasks | backend-engineer | 2 | P2 |

**Exit Criteria:**
- Workflow listing and detail endpoints return accurate data
- Starting a workflow via API creates tasks on the MessageBus
- Run status tracks step-by-step progress
- Cancellation properly cleans up pending tasks

---

### Epic 5: Memory & Knowledge API (MEDIUM Priority)

**Epic Owner:** lead-engineer  
**Estimated Effort:** 14 hours  
**Dependencies:** Epic 1 (app foundation)

| Story ID | User Story | Acceptance Criteria | Owner | Est. Hours | Priority |
|----------|-----------|---------------------|-------|------------|----------|
| D5-027 | As an API consumer, I want to search memory so that I can recall organizational knowledge | `GET /api/v1/memory/search?q=keyword&type=episodic` returns ranked results | backend-engineer | 3 | P0 |
| D5-028 | As an API consumer, I want to get memory entries by type so that I can browse knowledge | `GET /api/v1/memory?type=semantic` returns paginated entries with metadata | backend-engineer | 2 | P0 |
| D5-029 | As an API consumer, I want to get memory statistics so that I can monitor knowledge growth | `GET /api/v1/memory/stats` returns counts by type, total, recent growth | backend-engineer | 2 | P0 |
| D5-030 | As an API consumer, I want to record knowledge so that I can capture insights via API | `POST /api/v1/memory` creates a new memory entry with content, type, tags | backend-engineer | 3 | P1 |
| D5-031 | As an API consumer, I want to trigger consolidation so that I can maintain memory quality | `POST /api/v1/memory/consolidate` triggers consolidation cycle; returns results | backend-engineer | 2 | P2 |
| D5-032 | As an API consumer, I want to get memory entries by agent so that I can inspect agent knowledge | `GET /api/v1/memory?agent_id=ai-engineer` returns agent-specific entries | backend-engineer | 2 | P1 |

**Exit Criteria:**
- Memory search returns relevant results via REST
- Memory entries are browsable by type and agent
- Memory statistics show accurate counts
- Consolidation can be triggered via API

---

### Epic 6: Agent Registry API (MEDIUM Priority)

**Epic Owner:** lead-engineer  
**Estimated Effort:** 8 hours  
**Dependencies:** Epic 1 (app foundation)

| Story ID | User Story | Acceptance Criteria | Owner | Est. Hours | Priority |
|----------|-----------|---------------------|-------|------------|----------|
| D5-033 | As an API consumer, I want to list all agents so that I can see the organization | `GET /api/v1/agents` returns list of agents with role, department, tools | backend-engineer | 2 | P0 |
| D5-034 | As an API consumer, I want to get agent details so that I can inspect capabilities | `GET /api/v1/agents/{agent_id}` returns full Agent model with permissions | backend-engineer | 2 | P0 |
| D5-035 | As an API consumer, I want to get agents by department so that I can see team composition | `GET /api/v1/agents?department=engineering` returns department-filtered list | backend-engineer | 2 | P1 |
| D5-036 | As an API consumer, I want to get the agent hierarchy so that I can visualize reporting | `GET /api/v1/agents/hierarchy` returns tree structure of reports_to relationships | backend-engineer | 2 | P1 |

**Exit Criteria:**
- Agent listing returns all 17+ agents with metadata
- Agent detail returns full capabilities and permissions
- Department filtering works correctly
- Hierarchy tree reflects actual reporting structure

---

### Epic 7: WebSocket Real-Time Events (HIGH Priority)

**Epic Owner:** frontend-engineer  
**Estimated Effort:** 14 hours  
**Dependencies:** Epic 1 (app foundation), Epics 2-6 (data sources)

| Story ID | User Story | Acceptance Criteria | Owner | Est. Hours | Priority |
|----------|-----------|---------------------|-------|------------|----------|
| D5-037 | As a dashboard user, I want to receive real-time task updates so that I see changes instantly | WebSocket endpoint `/ws/events` pushes task_created, task_completed, task_failed events | frontend-engineer | 4 | P0 |
| D5-038 | As a dashboard user, I want to subscribe to specific event types so that I reduce noise | WebSocket accepts `?topics=task,cost,workflow` filter parameter | frontend-engineer | 3 | P0 |
| D5-039 | As a dashboard user, I want to receive cost alerts so that I know when budgets are hit | WebSocket pushes budget_warning at 80% and budget_exceeded at 100% | frontend-engineer | 3 | P1 |
| D5-040 | As a dashboard user, I want to receive workflow status updates so that I track automation progress | WebSocket pushes workflow_started, step_completed, workflow_completed events | frontend-engineer | 2 | P1 |
| D5-041 | As a developer, I want connection heartbeat so that stale connections are cleaned up | WebSocket sends ping every 30s; closes inactive connections after 90s | frontend-engineer | 2 | P1 |

**Exit Criteria:**
- WebSocket connection established and authenticated
- Task events stream in real time (< 200ms latency)
- Topic filtering reduces event noise
- Budget alerts fire at configured thresholds
- Heartbeat prevents zombie connections

---

### Epic 8: CEO Dashboard Frontend (HIGH Priority)

**Epic Owner:** frontend-engineer  
**Estimated Effort:** 24 hours  
**Dependencies:** Epic 7 (WebSocket), Epics 2-6 (REST data)

| Story ID | User Story | Acceptance Criteria | Owner | Est. Hours | Priority |
|----------|-----------|---------------------|-------|------------|----------|
| D5-042 | As the CEO, I want a dashboard overview page so that I can see organizational health at a glance | Single page showing KPI cards for all 7 departments with status indicators | frontend-engineer | 4 | P0 |
| D5-043 | As the CEO, I want a task board view so that I can see work in progress | Kanban-style board showing tasks by status (pending, in-progress, completed, failed) | frontend-engineer | 4 | P0 |
| D5-044 | As the CEO, I want a cost monitor panel so that I can track spending | Real-time cost chart with daily trend, model breakdown, budget gauge | frontend-engineer | 4 | P0 |
| D5-045 | As the CEO, I want a workflow monitor so that I can see automation status | List of active workflow runs with step progress bars and status | frontend-engineer | 3 | P1 |
| D5-046 | As the CEO, I want an agent status panel so that I can see who's working | Grid of agent cards showing status, current task, last activity | frontend-engineer | 3 | P1 |
| D5-047 | As the CEO, I want a memory/knowledge panel so that I can see organizational learning | Memory growth chart, recent entries feed, search bar | frontend-engineer | 3 | P2 |
| D5-048 | As the CEO, I want the dashboard to auto-refresh so that data is always current | WebSocket connection updates all panels without page refresh | frontend-engineer | 2 | P0 |
| D5-049 | As the CEO, I want a mobile-responsive layout so that I can check status on my phone | Dashboard renders correctly on 375px+ viewport widths | frontend-engineer | 1 | P2 |

**Exit Criteria:**
- Dashboard loads and shows all 7 department KPIs
- Task board reflects real-time MessageBus state
- Cost monitor shows live spending data
- Auto-refresh works via WebSocket
- Mobile layout is usable

---

### Epic 9: API Security & Authentication (HIGH Priority)

**Epic Owner:** security-engineer  
**Estimated Effort:** 12 hours  
**Dependencies:** Epic 1 (app foundation)

| Story ID | User Story | Acceptance Criteria | Owner | Est. Hours | Priority |
|----------|-----------|---------------------|-------|------------|----------|
| D5-050 | As an operator, I want API key authentication so that write endpoints are protected | `X-API-Key` header validated against configured keys; 401 on missing/invalid | security-engineer | 4 | P0 |
| D5-051 | As an operator, I want read endpoints to be public so that the dashboard works without auth | GET endpoints accessible without API key; POST/PATCH/DELETE require auth | security-engineer | 2 | P0 |
| D5-052 | As an operator, I want rate limiting so that the API is not overwhelmed | Configurable rate limits per endpoint tier; 429 response with Retry-After header | security-engineer | 3 | P1 |
| D5-053 | As a security engineer, I want request logging so that I can audit API usage | All API requests logged with timestamp, method, path, status, client IP | security-engineer | 2 | P1 |
| D5-054 | As an operator, I want CORS configuration so that the dashboard domain is allowed | Configurable allowed origins; preflight requests handled correctly | security-engineer | 1 | P0 |

**Exit Criteria:**
- Write endpoints require valid API key
- Read endpoints are accessible for dashboard
- Rate limiting returns 429 with proper headers
- All requests are logged for audit
- CORS allows dashboard domain

---

### Epic 10: Testing & Documentation (HIGH Priority)

**Epic Owner:** qa-engineer  
**Estimated Effort:** 20 hours  
**Dependencies:** All Epics 1-9

| Story ID | User Story | Acceptance Criteria | Owner | Est. Hours | Priority |
|----------|-----------|---------------------|-------|------------|----------|
| D5-055 | As a developer, I want unit tests for all API endpoints so that regressions are caught | Every endpoint has unit test with mocked dependencies; covers happy path and error cases | qa-engineer | 8 | P0 |
| D5-056 | As a developer, I want integration tests so that end-to-end flows work | Integration tests start real FastAPI TestClient; test full request lifecycle | qa-engineer | 4 | P0 |
| D5-057 | As a developer, I want WebSocket tests so that real-time features are validated | WebSocket connection, message receipt, topic filtering, heartbeat all tested | qa-engineer | 3 | P1 |
| D5-058 | As a developer, I want load tests so that performance requirements are verified | Locust or similar load test hitting all read endpoints; p95 < 100ms verified | qa-engineer | 3 | P1 |
| D5-059 | As a developer, I want OpenAPI schema validation so that docs match implementation | Generated OpenAPI spec passes Spectral linting; all endpoints documented | qa-engineer | 2 | P1 |

**Exit Criteria:**
- ≥ 90% code coverage for `services/` module
- All endpoints have unit tests
- Integration tests cover critical paths
- Load test confirms p95 < 100ms
- OpenAPI spec is lint-clean

---

### Epic 11: Deployment & DevOps (MEDIUM Priority)

**Epic Owner:** devops-engineer  
**Estimated Effort:** 10 hours  
**Dependencies:** Epic 1 (app foundation)

| Story ID | User Story | Acceptance Criteria | Owner | Est. Hours | Priority |
|----------|-----------|---------------------|-------|------------|----------|
| D5-060 | As an operator, I want a Dockerfile for the API so that it can be containerized | Multi-stage Dockerfile builds API image; runs uvicorn; exposes port 8000 | devops-engineer | 3 | P1 |
| D5-061 | As an operator, I want docker-compose so that I can run the full stack locally | docker-compose.yml with API, optional Redis for rate limiting | devops-engineer | 2 | P1 |
| D5-062 | As an operator, I want CI pipeline for API tests so that quality is enforced | GitHub Actions workflow runs tests on PR; fails on coverage drop | devops-engineer | 3 | P1 |
| D5-063 | As an operator, I want a startup script so that the API runs in development | Script starts uvicorn with reload, configurable env, and health check wait | devops-engineer | 2 | P2 |

**Exit Criteria:**
- `docker build` produces working API image
- `docker compose up` starts API server
- CI pipeline runs on PR and blocks merge on failure
- Development startup script works

---

## Sprint 5 Dependencies Map

```
                    ┌─────────────────┐
                    │  Epic 1: App    │
                    │  Foundation     │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
   ┌────────▼──────┐ ┌──────▼──────┐ ┌───────▼───────┐
   │ Epic 2: Tasks │ │ Epic 3: Cost│ │ Epic 6: Agent │
   │ API           │ │ API         │ │ Registry API  │
   └────────┬──────┘ └──────┬──────┘ └───────┬───────┘
            │                │                │
   ┌────────▼──────┐ ┌──────▼──────┐         │
   │ Epic 4:       │ │ Epic 5:     │         │
   │ Workflow API  │ │ Memory API  │         │
   └────────┬──────┘ └──────┬──────┘         │
            │                │                │
            └────────────────┼────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Epic 7:        │
                    │  WebSocket      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │                             │
     ┌────────▼────────┐          ┌─────────▼─────────┐
     │ Epic 8: Dashboard│         │ Epic 9: Security  │
     │ Frontend         │         │ & Auth            │
     └────────┬────────┘          └─────────┬─────────┘
              │                             │
              └──────────────┬──────────────┘
                             │
                    ┌────────▼────────┐
                    │  Epic 10:       │
                    │  Testing & Docs │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Epic 11:       │
                    │  Deployment     │
                    └─────────────────┘
```

### Critical Path

1. **Epic 1** (Foundation) → **Epic 2** (Tasks API) → **Epic 7** (WebSocket) → **Epic 8** (Dashboard) → **Epic 10** (Testing)
2. **Epic 1** → **Epic 9** (Security) must be parallel-ready by Week 9 Day 3

### Cross-Workstream Dependencies

| From | To | Dependency | Risk |
|------|----|-----------|------|
| Epic 2 (Tasks) | Epic 4 (Workflows) | WorkflowEngine uses MessageBus | Low — shared module |
| Epic 2 (Tasks) | Epic 7 (WebSocket) | WebSocket broadcasts task events | Medium — event wiring |
| Epic 3 (Costs) | Epic 7 (WebSocket) | Budget alerts via WebSocket | Low — threshold logic |
| Epic 9 (Security) | Epic 1 (Foundation) | Auth middleware on app | Medium — must design early |
| Epic 8 (Dashboard) | Epic 7 (WebSocket) | Dashboard consumes WS events | High — UI depends on WS contract |
| Epic 10 (Testing) | All Epics | Tests require endpoints to exist | Low — incremental |

---

## Detailed Task Dependencies

### Epic 1: FastAPI Foundation — Dependencies

| Story | Internal Dependencies | External Dependencies | Cross-Agent Dependencies | Risk Level |
|-------|----------------------|----------------------|-------------------------|------------|
| D5-001 | None | `pyproject.toml` (add fastapi, uvicorn), `config/settings.py` (existing patterns) | lead-engineer (architecture review) | LOW |
| D5-002 | D5-001 (app factory) | `config/settings.py` (Pydantic Settings pattern) | None | LOW |
| D5-003 | D5-001 (app factory), D5-005 (DI providers) | `message_bus/message_bus.py`, `memory/engine.py`, `workflow/engine.py`, `core/cost_tracker.py` | None | LOW |
| D5-004 | D5-001 (app factory), D5-003 (health check) | Same as D5-003 | None | LOW |
| D5-005 | D5-001 (app factory) | `message_bus/message_bus.py`, `core/cost_tracker.py`, `workflow/engine.py`, `memory/engine.py`, `agents/registry.py` | None | MEDIUM — must understand all subsystem interfaces |
| D5-006 | D5-001 (app factory) | None (standard FastAPI patterns) | None | LOW |

**Epic 1 Blockers:**
- `fastapi` and `uvicorn` must be added to `pyproject.toml` dependencies before any work begins
- `config/settings.py` must be understood to follow existing Pydantic Settings patterns

---

### Epic 2: Task & MessageBus API — Dependencies

| Story | Internal Dependencies | External Dependencies | Cross-Agent Dependencies | Risk Level |
|-------|----------------------|----------------------|-------------------------|------------|
| D5-007 | D5-001, D5-005 (foundation + DI) | `message_bus/message_bus.py` (MessageBus.list_tasks()), `message_bus/task.py` (Task model) | None | LOW |
| D5-008 | D5-007 (list endpoint pattern) | `message_bus/message_bus.py` (MessageBus.get_task()) | None | LOW |
| D5-009 | D5-007, D5-008 | `message_bus/message_bus.py` (MessageBus.send_task()), `message_bus/task.py` (TaskCreate schema) | None | MEDIUM — task creation triggers MessageBus events |
| D5-010 | D5-007, D5-008 | `message_bus/task_status.py` (TaskStatus enum, valid transitions) | None | MEDIUM — status transition validation logic |
| D5-011 | D5-007 | `message_bus/message_bus.py` (filtering support) | None | LOW |
| D5-012 | D5-007 | `message_bus/message_bus.py` (receiver_id filter) | None | LOW |
| D5-013 | D5-007 | `message_bus/message_bus.py` (aggregate statistics) | None | MEDIUM — requires new aggregation logic |
| D5-014 | D5-007, D5-008 | `message_bus/message_bus.py` (soft delete) | None | LOW |

**Epic 2 Blockers:**
- D5-001 and D5-005 must be complete (app factory + DI providers)
- `MessageBus` interface must be understood — check if `list_tasks()` and `get_task()` methods exist or need to be added

---

### Epic 3: Cost & Budget API — Dependencies

| Story | Internal Dependencies | External Dependencies | Cross-Agent Dependencies | Risk Level |
|-------|----------------------|----------------------|-------------------------|------------|
| D5-015 | D5-001, D5-005 (foundation + DI) | `core/cost_tracker.py` (CostTracker.get_summary()) | None | LOW |
| D5-016 | D5-015 | `core/cost_tracker.py` (CostTracker.get_history()) | None | LOW |
| D5-017 | D5-015 | `core/cost_tracker.py` (per-model cost data) | None | MEDIUM — may need to add model grouping |
| D5-018 | D5-015 | `core/cost_tracker.py` (per-agent cost data) | None | MEDIUM — may need to add agent grouping |
| D5-019 | D5-015 | `core/cost_tracker.py` (budget limits, current usage) | None | LOW |

**Epic 3 Blockers:**
- D5-001 and D5-005 must be complete
- `CostTracker` API must be verified — check if summary, history, and budget methods exist

---

### Epic 4: Workflow API — Dependencies

| Story | Internal Dependencies | External Dependencies | Cross-Agent Dependencies | Risk Level |
|-------|----------------------|----------------------|-------------------------|------------|
| D5-020 | D5-001, D5-005 (foundation + DI) | `workflow/engine.py` (WorkflowEngine.list_workflows()), `workflow/models.py` (Workflow model) | None | LOW |
| D5-021 | D5-020 | `workflow/engine.py` (WorkflowEngine.get_workflow()) | None | LOW |
| D5-022 | D5-020, D5-021 | `workflow/engine.py` (WorkflowEngine.start_workflow()), `message_bus/message_bus.py` (task creation) | Epic 2 (task creation pattern) | MEDIUM — workflow start creates tasks on MessageBus |
| D5-023 | D5-022 | `workflow/engine.py` (WorkflowEngine.get_run_status()) | None | LOW |
| D5-024 | D5-020, D5-023 | `workflow/engine.py` (run history) | None | LOW |
| D5-025 | D5-022, D5-023 | `workflow/engine.py` (WorkflowEngine.complete_step()), `message_bus/message_bus.py` | None | MEDIUM — step completion advances workflow |
| D5-026 | D5-022, D5-023 | `workflow/engine.py` (cancel logic), `message_bus/message_bus.py` (cleanup) | None | MEDIUM — must clean up pending tasks |

**Epic 4 Blockers:**
- D5-001 and D5-005 must be complete
- `WorkflowEngine` API must be verified — check if all required methods exist
- D5-022 depends on Epic 2 pattern for task creation

---

### Epic 5: Memory & Knowledge API — Dependencies

| Story | Internal Dependencies | External Dependencies | Cross-Agent Dependencies | Risk Level |
|-------|----------------------|----------------------|-------------------------|------------|
| D5-027 | D5-001, D5-005 (foundation + DI) | `memory/engine.py` (MemoryEngine.search()), `memory/search.py` (search logic) | None | LOW |
| D5-028 | D5-027 | `memory/engine.py` (MemoryEngine.list_entries()), `memory/models.py` (MemoryEntry model) | None | LOW |
| D5-029 | D5-027 | `memory/engine.py` (stats aggregation) | None | LOW |
| D5-030 | D5-027, D5-028 | `memory/engine.py` (MemoryEngine.add_entry()) | None | LOW |
| D5-031 | D5-027, D5-028 | `memory/engine.py` (MemoryEngine.consolidate()), `memory/consolidation.py` | None | LOW |
| D5-032 | D5-027, D5-028 | `memory/engine.py` (agent_id filter) | None | LOW |

**Epic 5 Blockers:**
- D5-001 and D5-005 must be complete
- `MemoryEngine` API must be verified — check if all required methods exist

---

### Epic 6: Agent Registry API — Dependencies

| Story | Internal Dependencies | External Dependencies | Cross-Agent Dependencies | Risk Level |
|-------|----------------------|----------------------|-------------------------|------------|
| D5-033 | D5-001, D5-005 (foundation + DI) | `agents/registry.py` (AgentRegistry.list_agents()), `agents/base.py` (Agent model) | None | LOW |
| D5-034 | D5-033 | `agents/registry.py` (AgentRegistry.get_agent()) | None | LOW |
| D5-035 | D5-033 | `agents/registry.py` (department filter) | None | LOW |
| D5-036 | D5-033 | `agents/registry.py` (hierarchy/reporting structure) | None | LOW |

**Epic 6 Blockers:**
- D5-001 and D5-005 must be complete
- `AgentRegistry` API must be verified — check if all required methods exist

---

### Epic 7: WebSocket Real-Time Events — Dependencies

| Story | Internal Dependencies | External Dependencies | Cross-Agent Dependencies | Risk Level |
|-------|----------------------|----------------------|-------------------------|------------|
| D5-037 | D5-001 (app factory), D5-007 (task API pattern), Epics 2-6 (data sources) | `message_bus/message_bus.py` (event hooks), `core/cost_tracker.py` (budget events) | backend-engineer (event wiring) | HIGH — must integrate with all subsystems |
| D5-038 | D5-037 | None (FastAPI WebSocket query params) | None | LOW |
| D5-039 | D5-037 | `core/cost_tracker.py` (budget thresholds) | None | MEDIUM — threshold logic |
| D5-040 | D5-037 | `workflow/engine.py` (workflow events) | None | MEDIUM — workflow event hooks |
| D5-041 | D5-037 | None (FastAPI WebSocket lifecycle) | None | LOW |

**Epic 7 Blockers:**
- D5-001 must be complete
- Epics 2-6 must be at least partially complete (need data sources for events)
- `MessageBus` and `WorkflowEngine` must support event hooks/callbacks
- **CRITICAL:** Event hook mechanism must be designed and agreed upon before WebSocket work begins

---

### Epic 8: CEO Dashboard Frontend — Dependencies

| Story | Internal Dependencies | External Dependencies | Cross-Agent Dependencies | Risk Level |
|-------|----------------------|----------------------|-------------------------|------------|
| D5-042 | D5-037, D5-038 (WebSocket), D5-007, D5-015, D5-020, D5-027, D5-033 (REST APIs) | Jinja2 templates, static file serving | frontend-engineer (UI/UX) | HIGH — depends on all REST APIs + WebSocket |
| D5-043 | D5-042, D5-037, D5-007, D5-008, D5-009, D5-010 | Task board UI components | None | MEDIUM |
| D5-044 | D5-042, D5-037, D5-015, D5-016, D5-019 | Cost chart components | None | MEDIUM |
| D5-045 | D5-042, D5-037, D5-020, D5-023 | Workflow monitor components | None | MEDIUM |
| D5-046 | D5-042, D5-037, D5-033, D5-034 | Agent status components | None | MEDIUM |
| D5-047 | D5-042, D5-037, D5-027, D5-028, D5-029 | Memory panel components | None | MEDIUM |
| D5-048 | D5-037, D5-042 | WebSocket client integration | None | LOW |
| D5-049 | D5-042 | CSS responsive design | None | LOW |

**Epic 8 Blockers:**
- D5-037 must be complete (WebSocket endpoint)
- All REST APIs (Epics 2-6) must be complete
- **CRITICAL:** Dashboard cannot start until WebSocket contract is finalized
- **CRITICAL:** Dashboard cannot start until all REST API response schemas are defined

---

### Epic 9: API Security & Authentication — Dependencies

| Story | Internal Dependencies | External Dependencies | Cross-Agent Dependencies | Risk Level |
|-------|----------------------|----------------------|-------------------------|------------|
| D5-050 | D5-001 (app factory) | `config/settings.py` (API_KEY setting) | None | LOW |
| D5-051 | D5-050 | None (FastAPI dependency override) | None | LOW |
| D5-052 | D5-001, D5-050 | `slowapi` or similar rate limiting library | None | MEDIUM — new dependency |
| D5-053 | D5-001, D5-050 | FastAPI middleware, logging | None | LOW |
| D5-054 | D5-001 | `config/settings.py` (CORS_ORIGINS setting) | None | LOW |

**Epic 9 Blockers:**
- D5-001 must be complete
- `slowapi` or equivalent must be added to `pyproject.toml` for rate limiting
- **CRITICAL:** Auth middleware must be designed early (Day 3) to avoid blocking frontend

---

### Epic 10: Testing & Documentation — Dependencies

| Story | Internal Dependencies | External Dependencies | Cross-Agent Dependencies | Risk Level |
|-------|----------------------|----------------------|-------------------------|------------|
| D5-055 | All Epics 1-9 (endpoints must exist) | `pytest`, `pytest-cov`, FastAPI TestClient | All engineers (test coordination) | LOW |
| D5-056 | All Epics 1-9 | FastAPI TestClient, full request lifecycle | All engineers | LOW |
| D5-057 | D5-037 (WebSocket endpoint) | FastAPI WebSocket test client | frontend-engineer (WS contract) | MEDIUM |
| D5-058 | All Epics 1-9 | `locust` or similar load testing tool | None | MEDIUM — new tooling |
| D5-059 | All Epics 1-9 | OpenAPI spec, Spectral linter | None | LOW |

**Epic 10 Blockers:**
- All endpoint code must be written before testing begins
- `pytest-cov` must be added to dev dependencies
- `locust` must be added to dev dependencies for load testing

---

### Epic 11: Deployment & DevOps — Dependencies

| Story | Internal Dependencies | External Dependencies | Cross-Agent Dependencies | Risk Level |
|-------|----------------------|----------------------|-------------------------|------------|
| D5-060 | D5-001 (app factory), D5-002 (config) | Docker, `pyproject.toml` | None | LOW |
| D5-061 | D5-060 | Docker Compose, `docker-compose.yml` | None | LOW |
| D5-062 | All Epics 1-9 (tests must pass) | GitHub Actions, CI pipeline | None | LOW |
| D5-063 | D5-001, D5-002 | Shell script, uvicorn | None | LOW |

**Epic 11 Blockers:**
- D5-001 and D5-002 must be complete
- All tests must pass before CI pipeline is finalized

---

## Dependency Risk Summary

| Risk Level | Count | Stories | Mitigation |
|------------|-------|---------|------------|
| **HIGH** | 5 | D5-037, D5-042, D5-043, D5-044, D5-045 | Prioritize early design; parallel work where possible |
| **MEDIUM** | 18 | D5-005, D5-009, D5-010, D5-013, D5-017, D5-018, D5-022, D5-025, D5-026, D5-039, D5-040, D5-046, D5-047, D5-052, D5-057, D5-058, D5-013, D5-017 | Detailed interface specs before coding |
| **LOW** | 40 | All others | Standard implementation |

---

## Critical Path Dependencies (Must Complete in Order)

```
Day 1:  D5-001 (App Factory) ──────────────────────────────────────────┐
Day 1:  D5-002 (Config) ───────────────────────────────────────────────┤
Day 2:  D5-005 (DI Providers) ─────────────────────────────────────────┤
Day 2:  D5-003, D5-004 (Health/Ready) ─────────────────────────────────┤
Day 2:  D5-006 (Exception Handlers) ───────────────────────────────────┤
                                                                        │
Day 3:  D5-007 (List Tasks) ───────────────────────────────────────────┤
Day 3:  D5-050, D5-054 (Auth + CORS) ──────────────────────────────────┤
                                                                        │
Day 4:  D5-008 (Get Task) ─────────────────────────────────────────────┤
Day 4:  D5-009 (Create Task) ──────────────────────────────────────────┤
Day 4:  D5-010 (Update Status) ────────────────────────────────────────┤
                                                                        │
Day 5:  D5-011, D5-012, D5-013 (Task Filters + Stats) ────────────────┤
Day 5:  D5-051 (Public Read) ──────────────────────────────────────────┤
Day 5:  D5-037 (WebSocket Foundation) ─────────────────────────────────┤
                                                                        │
Day 6:  D5-015 (Cost Summary) ─────────────────────────────────────────┤
Day 6:  D5-016 (Cost History) ─────────────────────────────────────────┤
Day 6:  D5-052 (Rate Limiting) ────────────────────────────────────────┤
                                                                        │
Day 7:  D5-017, D5-018, D5-019 (Cost Filters + Budget) ───────────────┤
Day 7:  D5-038 (WS Topic Filter) ─────────────────────────────────────┤
                                                                        │
Day 8:  D5-020 (List Workflows) ───────────────────────────────────────┤
Day 8:  D5-021 (Workflow Detail) ──────────────────────────────────────┤
Day 8:  D5-039 (Budget Alerts) ────────────────────────────────────────┤
Day 8:  D5-053 (Request Logging) ──────────────────────────────────────┤
                                                                        │
Day 9:  D5-022 (Start Workflow) ───────────────────────────────────────┤
Day 9:  D5-023 (Run Status) ───────────────────────────────────────────┤
Day 9:  D5-040 (Workflow Events) ──────────────────────────────────────┤
Day 9:  D5-041 (Heartbeat) ────────────────────────────────────────────┤
                                                                        │
Day 10: D5-024, D5-025, D5-026 (Workflow Filters + Cancel) ───────────┤
Day 10: D5-042 (Dashboard Overview) ───────────────────────────────────┤
Day 10: D5-060 (Dockerfile) ───────────────────────────────────────────┤
                                                                        │
Day 11: D5-027 (Memory Search) ────────────────────────────────────────┤
Day 11: D5-028 (List Entries) ─────────────────────────────────────────┤
Day 11: D5-043 (Task Board) ───────────────────────────────────────────┤
Day 11: D5-061 (docker-compose) ───────────────────────────────────────┤
                                                                        │
Day 12: D5-029 (Memory Stats) ─────────────────────────────────────────┤
Day 12: D5-030 (Record Memory) ────────────────────────────────────────┤
Day 12: D5-044 (Cost Monitor) ─────────────────────────────────────────┤
Day 12: D5-055 (Unit Tests) ───────────────────────────────────────────┤
                                                                        │
Day 13: D5-031, D5-032 (Consolidation + Agent Filter) ────────────────┤
Day 13: D5-062 (CI Pipeline) ──────────────────────────────────────────┤
Day 13: D5-045 (Workflow Monitor) ─────────────────────────────────────┤
                                                                        │
Day 14: D5-033 (List Agents) ──────────────────────────────────────────┤
Day 14: D5-034 (Agent Detail) ─────────────────────────────────────────┤
Day 14: D5-056 (Integration Tests) ────────────────────────────────────┤
                                                                        │
Day 15: D5-035, D5-036 (Agent Filters + Hierarchy) ───────────────────┤
Day 15: D5-046 (Agent Status Panel) ───────────────────────────────────┤
Day 15: D5-063 (Startup Script) ───────────────────────────────────────┤
                                                                        │
Day 16: D5-047 (Memory Panel) ─────────────────────────────────────────┤
Day 16: D5-057 (WebSocket Tests) ──────────────────────────────────────┤
                                                                        │
Day 17: D5-048 (Auto-Refresh) ─────────────────────────────────────────┤
Day 17: D5-058 (Load Tests) ───────────────────────────────────────────┤
                                                                        │
Day 18: D5-049 (Mobile Responsive) ────────────────────────────────────┤
Day 18: D5-059 (OpenAPI Validation) ───────────────────────────────────┤
                                                                        │
Day 19-20: Final testing, bug fixes, sprint review ────────────────────┘
```

---

## External Package Dependencies

| Package | Required By | Action |
|---------|-------------|--------|
| `fastapi` | D5-001 | Add to `pyproject.toml` dependencies |
| `uvicorn[standard]` | D5-001 | Add to `pyproject.toml` dependencies |
| `jinja2` | D5-042 (Dashboard templates) | Add to `pyproject.toml` dependencies |
| `python-multipart` | D5-009 (form data) | Add to `pyproject.toml` dependencies |
| `slowapi` | D5-052 (rate limiting) | Add to `pyproject.toml` dependencies |
| `pytest-cov` | D5-055 (coverage) | Add to `pyproject.toml` dev dependencies |
| `locust` | D5-058 (load testing) | Add to `pyproject.toml` dev dependencies |
| `websockets` | D5-037 (WebSocket) | Add to `pyproject.toml` dependencies |

---

## Subsystem Interface Dependencies

| Subsystem | Module | Required Methods for API | Verified? |
|-----------|--------|-------------------------|-----------|
| MessageBus | `message_bus/message_bus.py` | `send_task()`, `get_task()`, `list_tasks()`, `update_task_status()` | ⚠️ Need to verify |
| CostTracker | `core/cost_tracker.py` | `get_summary()`, `get_history()`, `get_by_model()`, `get_by_agent()`, `get_budget()` | ⚠️ Need to verify |
| WorkflowEngine | `workflow/engine.py` | `list_workflows()`, `get_workflow()`, `start_workflow()`, `get_run_status()`, `complete_step()`, `cancel_run()` | ⚠️ Need to verify |
| MemoryEngine | `memory/engine.py` | `search()`, `list_entries()`, `get_stats()`, `add_entry()`, `consolidate()` | ⚠️ Need to verify |
| AgentRegistry | `agents/registry.py` | `list_agents()`, `get_agent()`, `get_hierarchy()` | ⚠️ Need to verify |

**ACTION REQUIRED:** Before Sprint 5 begins, verify that all subsystem methods listed above exist. If any are missing, they must be added as prerequisite work.

---

## Sprint 5 Task Assignments

### Backend Engineer (Primary: REST API)

| Story ID | Task | Sprint Day |
|----------|------|-----------|
| D5-001 | FastAPI app factory | Day 1 |
| D5-002 | API configuration settings | Day 1 |
| D5-005 | Dependency injection providers | Day 1-2 |
| D5-003 | Health check endpoint | Day 2 |
| D5-004 | Readiness endpoint | Day 2 |
| D5-006 | Exception handlers | Day 2 |
| D5-007 to D5-014 | Task API (8 stories) | Day 3-5 |
| D5-015 to D5-019 | Cost API (5 stories) | Day 6-7 |
| D5-020 to D5-026 | Workflow API (7 stories) | Day 8-10 |
| D5-027 to D5-032 | Memory API (6 stories) | Day 11-13 |
| D5-033 to D5-036 | Agent Registry API (4 stories) | Day 14 |

**Total estimated hours:** 78

### Frontend Engineer (Primary: Dashboard & WebSocket)

| Story ID | Task | Sprint Day |
|----------|------|-----------|
| D5-037 | WebSocket event streaming | Day 5-7 |
| D5-038 | WebSocket topic filtering | Day 7-8 |
| D5-039 | Budget alert events | Day 8 |
| D5-040 | Workflow status events | Day 8-9 |
| D5-041 | Connection heartbeat | Day 9 |
| D5-042 | Dashboard overview page | Day 9-11 |
| D5-043 | Task board view | Day 11-13 |
| D5-044 | Cost monitor panel | Day 13-15 |
| D5-045 | Workflow monitor | Day 15-16 |
| D5-046 | Agent status panel | Day 16-17 |
| D5-047 | Memory panel | Day 17-18 |
| D5-048 | Auto-refresh integration | Day 18 |
| D5-049 | Mobile responsive | Day 19-20 |

**Total estimated hours:** 31

### Security Engineer (Primary: API Security)

| Story ID | Task | Sprint Day |
|----------|------|-----------|
| D5-050 | API key authentication | Day 3-5 |
| D5-051 | Read endpoint public access | Day 5 |
| D5-052 | Rate limiting | Day 6-8 |
| D5-053 | Request logging/audit | Day 8-9 |
| D5-054 | CORS configuration | Day 3 |

**Total estimated hours:** 12

### QA Engineer (Primary: Testing)

| Story ID | Task | Sprint Day |
|----------|------|-----------|
| D5-055 | Unit tests for all endpoints | Day 8-15 |
| D5-056 | Integration tests | Day 12-16 |
| D5-057 | WebSocket tests | Day 16-18 |
| D5-058 | Load tests | Day 18-19 |
| D5-059 | OpenAPI schema validation | Day 19-20 |

**Total estimated hours:** 20

### DevOps Engineer (Primary: Deployment)

| Story ID | Task | Sprint Day |
|----------|------|-----------|
| D5-060 | Dockerfile | Day 10-12 |
| D5-061 | docker-compose | Day 12-13 |
| D5-062 | CI pipeline | Day 13-15 |
| D5-063 | Startup script | Day 15 |

**Total estimated hours:** 10

### Lead Engineer (Primary: Architecture Review)

| Responsibility | Sprint Day |
|----------------|-----------|
| API route design review | Day 1-2 |
| WebSocket contract review | Day 5-6 |
| Dashboard architecture review | Day 9-10 |
| Code review (all PRs) | Ongoing |
| Cross-epic integration review | Day 14-15 |

### CTO (Primary: Technical Oversight)

| Responsibility | Sprint Day |
|----------------|-----------|
| Architecture decision records | Day 1 |
| Technology selection approval | Day 1 |
| Security review | Day 8-9 |
| Performance review | Day 18-19 |

---

## Sprint 5 API Reference (Draft)

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints Summary

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | System health check |
| GET | `/ready` | No | Readiness probe |
| **Tasks** | | | |
| GET | `/tasks` | No | List tasks (filterable) |
| GET | `/tasks/{id}` | No | Get task detail |
| POST | `/tasks` | Yes | Create task |
| PATCH | `/tasks/{id}/status` | Yes | Update task status |
| DELETE | `/tasks/{id}` | Yes | Delete task |
| GET | `/tasks/stats` | No | Task statistics |
| **Costs** | | | |
| GET | `/costs/summary` | No | Cost summary |
| GET | `/costs/history` | No | Cost history (days param) |
| GET | `/costs/by-model` | No | Costs grouped by model |
| GET | `/costs/by-agent` | No | Costs grouped by agent |
| GET | `/costs/budget` | No | Budget status |
| **Workflows** | | | |
| GET | `/workflows` | No | List workflows |
| GET | `/workflows/{id}` | No | Workflow detail |
| POST | `/workflows/{id}/start` | Yes | Start workflow |
| GET | `/workflows/runs/{id}` | No | Run status |
| GET | `/workflows/{id}/runs` | No | Run history |
| POST | `/workflows/runs/{rid}/steps/{sid}/complete` | Yes | Complete step |
| POST | `/workflows/runs/{id}/cancel` | Yes | Cancel run |
| **Memory** | | | |
| GET | `/memory` | No | List memory entries |
| GET | `/memory/search` | No | Search memory |
| GET | `/memory/stats` | No | Memory statistics |
| POST | `/memory` | Yes | Record knowledge |
| POST | `/memory/consolidate` | Yes | Trigger consolidation |
| **Agents** | | | |
| GET | `/agents` | No | List agents |
| GET | `/agents/{id}` | No | Agent detail |
| GET | `/agents/hierarchy` | No | Agent hierarchy |
| **WebSocket** | | | |
| WS | `/ws/events` | Token | Real-time event stream |

### WebSocket Event Types

| Event | Payload | Trigger |
|-------|---------|---------|
| `task_created` | Task object | New task on MessageBus |
| `task_completed` | Task object | Task completion |
| `task_failed` | Task object | Task failure |
| `task_escalated` | Task object | Task escalation |
| `budget_warning` | `{daily, limit, percent}` | 80% budget usage |
| `budget_exceeded` | `{daily, limit, percent}` | 100% budget usage |
| `workflow_started` | WorkflowRun object | Workflow start |
| `step_completed` | `{run_id, step_id, result}` | Step completion |
| `workflow_completed` | WorkflowRun object | Workflow completion |

---

## Sprint 5 Milestones

| Milestone | Target Date | Deliverable | Gate |
|-----------|-------------|-------------|------|
| M5-M1: App Foundation | Week 9, Day 2 (Aug 27) | FastAPI app starts; health check works | Smoke test passes |
| M5-M2: Core APIs Ready | Week 9, Day 5 (Aug 30) | Tasks, Costs, Agents APIs complete | Unit tests pass |
| M5-M3: Security Layer | Week 10, Day 1 (Sep 1) | Auth, rate limiting, CORS working | Security review passes |
| M5-M4: WebSocket Live | Week 10, Day 2 (Sep 2) | Real-time events streaming | WS test passes |
| M5-M5: Dashboard MVP | Week 10, Day 4 (Sep 4) | Dashboard renders all panels | Visual QA passes |
| M5-M6: Testing Complete | Week 10, Day 5 (Sep 5) | All tests pass; ≥ 90% coverage | CI green |
| M5-M7: Sprint Review | Week 10, Day 5 (Sep 5) | Demo to human-ceo | CEO sign-off |

---

## Sprint 5 Timeline (Gantt View)

```
Week 9: Aug 25 - Aug 31
─────────────────────────────────────────────────
Day 1 (Mon) │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 1: App Foundation (Backend)
Day 2 (Tue) │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 1: Foundation + Security CORS
Day 3 (Wed) │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 2: Task API + Epic 9: Auth
Day 4 (Thu) │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 2: Task API (cont)
Day 5 (Fri) │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 2: Task API (cont) + Epic 7: WebSocket start
Day 6 (Sat) │░░░░░░░░░░░░░░░░│ (buffer / catch-up)
Day 7 (Sun) │░░░░░░░░░░░░░░░░│ (buffer / catch-up)

Week 10: Sep 1 - Sep 7
─────────────────────────────────────────────────
Day 8 (Mon) │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 3: Cost API + Epic 7: WS (cont)
Day 9 (Tue) │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 4: Workflow API + Epic 8: Dashboard start
Day 10 (Wed)│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 4: Workflow API (cont) + Epic 11: Dockerfile
Day 11 (Thu)│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 5: Memory API + Epic 8: Dashboard (cont)
Day 12 (Fri)│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 5: Memory API (cont) + Epic 10: Unit tests
Day 13 (Sat)│░░░░░░░░░░░░░░░░│ (buffer / catch-up)
Day 14 (Sun)│░░░░░░░░░░░░░░░░│ (buffer / catch-up)

Week 11: Sep 8 - Sep 14 (overflow / hardening)
─────────────────────────────────────────────────
Day 15 (Mon)│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 6: Agent API + Epic 10: Tests + Epic 11: CI
Day 16 (Tue)│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 8: Dashboard panels + Epic 10: WS tests
Day 17 (Wed)│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 8: Dashboard panels (cont)
Day 18 (Thu)│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 8: Dashboard polish + Epic 10: Load tests
Day 19 (Fri)│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Epic 10: Final testing + Epic 8: Mobile
Day 20 (Sat)│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ Sprint Review + Retrospective
```

---

## Sprint 5 Risks & Mitigations

| Risk ID | Risk | Probability | Impact | Mitigation | Owner |
|---------|------|-------------|--------|------------|-------|
| R5-01 | WebSocket complexity delays dashboard | Medium | High | Deliver REST-only dashboard first; add WS as enhancement | frontend-engineer |
| R5-02 | FastAPI learning curve slows backend | Low | Medium | Use standard FastAPI patterns; reference existing Pydantic models | backend-engineer |
| R5-03 | Auth middleware blocks frontend progress | Medium | High | Make auth optional initially; enforce in final week | security-engineer |
| R5-04 | Dashboard scope creep | Medium | Medium | Strict P0/P1/P2 prioritization; defer P2 items if behind | frontend-engineer |
| R5-05 | CORS misconfiguration prevents dashboard access | Low | High | Test CORS on Day 1 of dashboard work | security-engineer |
| R5-06 | Test coverage target not met | Low | High | Write tests alongside code; daily coverage check | qa-engineer |
| R5-07 | API performance below target | Low | Medium | Profile early; add caching for read-heavy endpoints | backend-engineer |
| R5-08 | Existing CLI functionality breaks | Low | High | Integration tests run on every PR; no changes to CLI modules | qa-engineer |

---

## Sprint 5 Definition of Done

### Per-Story Done

A user story is **Done** when:

- [ ] Code is written and passes Ruff linting (zero errors)
- [ ] Code is formatted with Black (no diffs)
- [ ] All functions have type hints (mypy strict mode)
- [ ] Unit tests written and passing (≥ 90% coverage for new code)
- [ ] Integration tests written (if applicable)
- [ ] Code review approved by lead-engineer or cto
- [ ] API endpoint has OpenAPI docstring (summary, description, response model)
- [ ] No regression in existing tests (`pytest` — all green)
- [ ] Documentation updated (if public API changed)

### Per-Epic Done

An epic is **Done** when:

- [ ] All stories in the epic are Done
- [ ] Epic exit criteria are met (verified by QA)
- [ ] Integration test covers epic's critical path
- [ ] Architecture decision record created (if applicable)

### Sprint Done

The sprint is **Done** when:

- [ ] All P0 stories are Done
- [ ] ≥ 80% of P1 stories are Done
- [ ] Test coverage ≥ 90% for `services/` module
- [ ] API starts, serves health check, and responds to requests
- [ ] Dashboard loads and shows real data from API
- [ ] WebSocket streams real events
- [ ] Security auth works on write endpoints
- [ ] Docker image builds successfully
- [ ] CI pipeline is green
- [ ] Load test shows p95 < 100ms for read endpoints
- [ ] Sprint review demo completed with human-ceo
- [ ] Retrospective action items documented

---

## Sprint 5 Ceremonies

| Ceremony | Date | Time | Attendees | Agenda |
|----------|------|------|-----------|--------|
| Sprint Planning | Aug 25, 2026 | 10:00 AM | All agents | Review this plan; confirm assignments; identify blockers |
| Daily Standup | Daily (Aug 25 - Sep 5) | 9:00 AM | All agents | Yesterday/today/blockers (15 min max) |
| Mid-Sprint Checkpoint | Aug 29, 2026 | 2:00 PM | Executives + Tech Leads | Review M5-M1, M5-M2 progress; adjust scope if needed |
| Architecture Review | Sep 1, 2026 | 11:00 AM | cto, lead-engineer, security-engineer | Review API contract, WS design, security model |
| Code Freeze | Sep 4, 2026 | 5:00 PM | All agents | No new features; bug fixes only |
| Sprint Review | Sep 5, 2026 | 2:00 PM | All agents + human-ceo | Demo dashboard, API, WebSocket |
| Sprint Retrospective | Sep 5, 2026 | 3:30 PM | All agents | What went well, what to improve, action items |

---

## Sprint 5 Backlog (Prioritized)

### P0 — Must Complete (43 stories, ~120 hours)

| ID | Story | Epic | Owner | Est. |
|----|-------|------|-------|------|
| D5-001 | FastAPI app factory | 1 | backend-engineer | 4 |
| D5-002 | API configuration | 1 | backend-engineer | 2 |
| D5-003 | Health check endpoint | 1 | backend-engineer | 2 |
| D5-004 | Readiness endpoint | 1 | backend-engineer | 2 |
| D5-005 | Dependency injection | 1 | backend-engineer | 4 |
| D5-006 | Exception handlers | 1 | backend-engineer | 2 |
| D5-007 | List tasks | 2 | backend-engineer | 3 |
| D5-008 | Get task detail | 2 | backend-engineer | 2 |
| D5-009 | Create task | 2 | backend-engineer | 3 |
| D5-010 | Update task status | 2 | backend-engineer | 2 |
| D5-015 | Cost summary | 3 | backend-engineer | 3 |
| D5-016 | Cost history | 3 | backend-engineer | 3 |
| D5-019 | Budget status | 3 | backend-engineer | 2 |
| D5-020 | List workflows | 4 | backend-engineer | 3 |
| D5-021 | Workflow detail | 4 | backend-engineer | 2 |
| D5-022 | Start workflow | 4 | backend-engineer | 3 |
| D5-023 | Run status | 4 | backend-engineer | 2 |
| D5-027 | Memory search | 5 | backend-engineer | 3 |
| D5-028 | List memory entries | 5 | backend-engineer | 2 |
| D5-029 | Memory statistics | 5 | backend-engineer | 2 |
| D5-033 | List agents | 6 | backend-engineer | 2 |
| D5-034 | Agent detail | 6 | backend-engineer | 2 |
| D5-037 | WS event streaming | 7 | frontend-engineer | 4 |
| D5-038 | WS topic filtering | 7 | frontend-engineer | 3 |
| D5-042 | Dashboard overview | 8 | frontend-engineer | 4 |
| D5-043 | Task board view | 8 | frontend-engineer | 4 |
| D5-044 | Cost monitor panel | 8 | frontend-engineer | 4 |
| D5-048 | Dashboard auto-refresh | 8 | frontend-engineer | 2 |
| D5-050 | API key auth | 9 | security-engineer | 4 |
| D5-051 | Public read endpoints | 9 | security-engineer | 2 |
| D5-054 | CORS configuration | 9 | security-engineer | 1 |
| D5-055 | Unit tests (all endpoints) | 10 | qa-engineer | 8 |
| D5-056 | Integration tests | 10 | qa-engineer | 4 |

### P1 — Should Complete (17 stories, ~48 hours)

| ID | Story | Epic | Owner | Est. |
|----|-------|------|-------|------|
| D5-011 | Filter tasks by status | 2 | backend-engineer | 2 |
| D5-012 | Tasks by agent | 2 | backend-engineer | 2 |
| D5-013 | Task statistics | 2 | backend-engineer | 2 |
| D5-017 | Cost by model | 3 | backend-engineer | 2 |
| D5-018 | Cost by agent | 3 | backend-engineer | 2 |
| D5-024 | Workflow run history | 4 | backend-engineer | 2 |
| D5-025 | Complete workflow step | 4 | backend-engineer | 2 |
| D5-030 | Record memory via API | 5 | backend-engineer | 3 |
| D5-032 | Memory by agent | 5 | backend-engineer | 2 |
| D5-035 | Agents by department | 6 | backend-engineer | 2 |
| D5-036 | Agent hierarchy | 6 | backend-engineer | 2 |
| D5-039 | Budget alert events | 7 | frontend-engineer | 3 |
| D5-040 | Workflow status events | 7 | frontend-engineer | 2 |
| D5-041 | Connection heartbeat | 7 | frontend-engineer | 2 |
| D5-045 | Workflow monitor panel | 8 | frontend-engineer | 3 |
| D5-046 | Agent status panel | 8 | frontend-engineer | 3 |
| D5-052 | Rate limiting | 9 | security-engineer | 3 |
| D5-053 | Request logging | 9 | security-engineer | 2 |
| D5-057 | WebSocket tests | 10 | qa-engineer | 3 |
| D5-058 | Load tests | 10 | qa-engineer | 3 |
| D5-059 | OpenAPI validation | 10 | qa-engineer | 2 |
| D5-060 | Dockerfile | 11 | devops-engineer | 3 |
| D5-061 | docker-compose | 11 | devops-engineer | 2 |
| D5-062 | CI pipeline | 11 | devops-engineer | 3 |

### P2 — Nice to Have (7 stories, ~16 hours)

| ID | Story | Epic | Owner | Est. |
|----|-------|------|-------|------|
| D5-014 | Delete task | 2 | backend-engineer | 2 |
| D5-026 | Cancel workflow run | 4 | backend-engineer | 2 |
| D5-031 | Trigger consolidation | 5 | backend-engineer | 2 |
| D5-047 | Memory panel | 8 | frontend-engineer | 3 |
| D5-049 | Mobile responsive | 8 | frontend-engineer | 1 |
| D5-063 | Startup script | 11 | devops-engineer | 2 |

---

## Sprint 5 Capacity Planning

| Agent | Available Hours | Allocated Hours | Utilization | Buffer |
|-------|----------------|-----------------|-------------|--------|
| backend-engineer | 80 | 78 | 97.5% | 2h |
| frontend-engineer | 80 | 31 | 38.8% | 49h |
| security-engineer | 40 | 12 | 30.0% | 28h |
| qa-engineer | 40 | 20 | 50.0% | 20h |
| devops-engineer | 30 | 10 | 33.3% | 20h |
| lead-engineer | 20 | 12 (reviews) | 60.0% | 8h |
| cto | 10 | 4 (oversight) | 40.0% | 6h |
| **Total** | **300** | **167** | **55.7%** | **133h** |

**Note:** Frontend-engineer has significant buffer for dashboard polish and P2 items. If Epic 8 scope is reduced, frontend-engineer can assist with WebSocket tests or documentation.

---

## Architecture Decisions (ADRs)

### ADR-001: FastAPI as REST Framework

**Status:** Proposed  
**Context:** Need a Python ASGI framework for REST API  
**Decision:** Use FastAPI with Uvicorn  
**Rationale:**
- Native Pydantic integration (existing models work directly)
- Auto-generated OpenAPI/Swagger documentation
- WebSocket support built-in (for Epic 7)
- Async support for concurrent requests
- Strong typing aligns with project standards

### ADR-002: Dependency Injection via FastAPI Depends()

**Status:** Proposed  
**Context:** Need testable, decoupled service access in endpoints  
**Decision:** Use FastAPI's `Depends()` for all service injection  
**Rationale:**
- Standard FastAPI pattern
- Easy to mock in tests
- Supports singleton and per-request lifecycles
- Clean separation of concerns

### ADR-003: API Key Authentication (not OAuth)

**Status:** Proposed  
**Context:** Need to protect write endpoints  
**Decision:** Simple API key via `X-API-Key` header  
**Rationale:**
- Appropriate for internal agent-to-agent API
- No external identity provider needed
- Can evolve to OAuth later if external access needed
- Aligns with existing permission tier model (T0-T4)

### ADR-004: WebSocket for Real-Time Updates

**Status:** Proposed  
**Context:** Dashboard needs live data without polling  
**Decision:** WebSocket endpoint with topic-based subscription  
**Rationale:**
- Lower latency than SSE (Server-Sent Events)
- Bidirectional (can request historical data)
- Topic filtering reduces bandwidth
- Native FastAPI support

### ADR-005: Dashboard as Server-Rendered HTML

**Status:** Proposed  
**Context:** Need a CEO dashboard  
**Decision:** Server-rendered HTML with vanilla JavaScript (no React/Vue)  
**Rationale:**
- Minimal build tooling required
- Fast to implement for MVP
- No npm/node dependency in production
- Can upgrade to SPA framework later

---

## File Structure (Proposed)

```
src/lightspeed_agents/
├── services/                      # NEW: API layer
│   ├── __init__.py
│   ├── app.py                     # FastAPI application factory
│   ├── config.py                  # API-specific settings
│   ├── dependencies.py            # FastAPI Depends() providers
│   ├── middleware.py               # Auth, CORS, rate limiting, logging
│   ├── exceptions.py              # Custom exception handlers
│   ├── routers/                   # API route modules
│   │   ├── __init__.py
│   │   ├── health.py              # /health, /ready
│   │   ├── tasks.py               # /tasks CRUD
│   │   ├── costs.py               # /costs endpoints
│   │   ├── workflows.py           # /workflows endpoints
│   │   ├── memory.py              # /memory endpoints
│   │   └── agents.py              # /agents endpoints
│   ├── schemas/                   # API request/response models
│   │   ├── __init__.py
│   │   ├── tasks.py               # TaskRequest, TaskResponse, TaskList
│   │   ├── costs.py               # CostSummary, CostHistory
│   │   ├── workflows.py           # WorkflowResponse, RunResponse
│   │   ├── memory.py              # MemorySearchRequest, MemoryEntryResponse
│   │   └── agents.py              # AgentResponse, AgentHierarchy
│   ├── websocket/                 # WebSocket handlers
│   │   ├── __init__.py
│   │   ├── manager.py             # ConnectionManager
│   │   ├── events.py              # Event types and serialization
│   │   └── handlers.py            # WS endpoint handlers
│   └── dashboard/                 # Dashboard frontend
│       ├── __init__.py
│       ├── routes.py              # Dashboard page routes
│       ├── static/                # Static assets
│       │   ├── css/
│       │   │   └── dashboard.css
│       │   ├── js/
│       │   │   ├── app.js         # Main dashboard logic
│       │   │   ├── websocket.js   # WS client
│       │   │   ├── tasks.js       # Task board component
│       │   │   ├── costs.js       # Cost monitor component
│       │   │   ├── workflows.js   # Workflow monitor component
│       │   │   ├── agents.js      # Agent status component
│       │   │   └── memory.js      # Memory panel component
│       │   └── img/               # Icons, logos
│       └── templates/             # Jinja2 templates
│           └── dashboard.html     # Main dashboard template
```

---

## Sprint 5 Exit Criteria (Summary)

| Category | Criterion | Verified By |
|----------|-----------|-------------|
| API | 50+ endpoints registered in OpenAPI | qa-engineer |
| API | All read endpoints respond < 100ms (p95) | qa-engineer |
| API | Auth protects write endpoints | security-engineer |
| WebSocket | Events stream within 200ms of state change | qa-engineer |
| WebSocket | Topic filtering works correctly | qa-engineer |
| Dashboard | All 7 department KPIs visible | human-ceo |
| Dashboard | Task board shows real-time data | human-ceo |
| Dashboard | Cost monitor shows live spending | human-ceo |
| Dashboard | Mobile responsive at 375px+ | qa-engineer |
| Quality | ≥ 90% test coverage for services/ | qa-engineer |
| Quality | Zero Ruff errors | qa-engineer |
| Quality | All existing tests still pass | qa-engineer |
| DevOps | Docker image builds | devops-engineer |
| DevOps | CI pipeline green | devops-engineer |
| Documentation | OpenAPI docs complete for all endpoints | technical-writer |

---

*Document Version: 1.0*  
*Created: July 27, 2026*  
*Owner: Office of the CEO, Light Speed Holdings, Inc.*  
*Prepared by: chief-of-staff*  
*Approved by: human-ceo*
