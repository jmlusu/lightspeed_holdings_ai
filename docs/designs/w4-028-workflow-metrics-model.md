# W4-028: Workflow Metrics Model Design

**Task:** W4-028  
**Owner:** data-engineer  
**Sprint:** 4  
**Status:** DESIGN  
**Created:** July 28, 2026  

---

## 1. Architecture Overview

### 1.1 Purpose

The Workflow Metrics system provides observability for workflow execution. It collects duration, cost, success rate, and retry data for every workflow run, stores execution traces for debugging, computes health scores, and detects SLA violations.

### 1.2 Position in the System

```
WorkflowEngine
    |
    ├── WorkflowMetricsCollector  (new — W4-028/W4-029)
    |       |
    |       ├── WorkflowMetrics store   (JSON via FileStore)
    |       └── TraceSpan store         (JSON via FileStore)
    |
    ├── MessageBus / AuditStore   (existing — correlates via run_id)
    ├── CostTracker               (existing — feeds total_cost)
    └── MemoryEngine              (existing — records outcomes)
```

The collector sits alongside the existing `WorkflowEngine` and is called at lifecycle boundaries: workflow start, step start/complete/fail, and workflow completion. It does not modify engine logic — it is a pure observer.

### 1.3 Data Flow

```
WorkflowEngine.start_workflow()
    → collector.record_workflow_start(workflow_id, run_id)

WorkflowEngine._advance_steps()
    → collector.record_step_start(run_id, step_id, assignee)

WorkflowEngine.complete_step()
    → collector.record_step_complete(run_id, step_id, duration, cost)

WorkflowEngine.fail_step()
    → collector.record_step_fail(run_id, step_id, error, duration)

WorkflowEngine (run reaches terminal state)
    → collector.record_workflow_complete(run_id, status)
```

### 1.4 Storage

All metrics persist as JSON files via the `message_bus.FileStore` (which provides file locking and atomic writes). Two files:

| File | Contents | Access Pattern |
|------|----------|----------------|
| `workflow_metrics.json` | Array of `WorkflowMetrics` records | Append on workflow completion; read for queries |
| `workflow_traces.json` | Array of `TraceSpan` records | Append on every event; read for debugging |

Traces use a ring-buffer cap of 10,000 spans. Older spans are trimmed on write.

---

## 2. Data Models

### 2.1 WorkflowMetrics

```python
class WorkflowMetrics(BaseModel):
    workflow_id: str
    run_id: str
    started_at: str                          # ISO-8601
    completed_at: str | None = None
    duration_seconds: float | None = None
    status: str = "running"                  # running | completed | failed | cancelled
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    total_cost: float = 0.0
    retry_count: int = 0
    parallel_steps: int = 0                  # max concurrent steps observed
    tags: list[str] = []
```

Fields are populated incrementally. `duration_seconds` is computed on completion from `started_at` → `completed_at`.

### 2.2 TraceSpan

```python
class TraceSpan(BaseModel):
    span_id: str              # UUID
    parent_span_id: str | None = None
    operation: str            # "step.execute", "step.retry", "workflow.checkpoint"
    start_time: str           # ISO-8601
    end_time: str | None = None
    duration_ms: float | None = None
    status: str = "running"   # running | completed | failed
    metadata: dict = {}
```

Spans form a tree via `parent_span_id`. A workflow-level span is the root; step spans are children.

---

## 3. Collector Interface

```python
class WorkflowMetricsCollector:
    def __init__(self, store_dir: str = ".opencode")

    # Lifecycle recording
    def record_workflow_start(self, workflow_id: str, run_id: str) -> WorkflowMetrics
    def record_step_start(self, run_id: str, step_id: str, assignee: str) -> TraceSpan
    def record_step_complete(self, run_id: str, step_id: str, duration: float, cost: float = 0.0) -> TraceSpan
    def record_step_fail(self, run_id: str, step_id: str, error: str, duration: float) -> TraceSpan
    def record_workflow_complete(self, run_id: str, status: str) -> WorkflowMetrics

    # Queries
    def get_metrics(self, workflow_id: str) -> WorkflowMetrics | None
    def get_workflow_history(self, workflow_id: str, limit: int = 10) -> list[WorkflowMetrics]
    def get_health_score(self, workflow_id: str) -> float          # 0.0 – 1.0
    def get_slas(self, workflow_id: str) -> dict                   # {p50, p95, p99}
    def get_traces(self, run_id: str) -> list[TraceSpan]
```

---

## 4. Health Score Calculation

The health score is a weighted composite of three signals derived from the last N completed runs (default N = 20):

```
health = 0.50 × success_rate
       + 0.25 × (1.0 - normalized_failure_rate)
       + 0.25 × speed_score
```

Where:

| Component | Formula | Range |
|-----------|---------|-------|
| `success_rate` | `completed_runs / total_runs` | 0.0 – 1.0 |
| `normalized_failure_rate` | `failed_runs / total_runs` | 0.0 – 1.0 |
| `speed_score` | `1.0 - clamp((median_duration - target_duration) / target_duration, 0, 1)` | 0.0 – 1.0 |

Default `target_duration` = 60 seconds. If no completed runs exist, score defaults to `1.0` (no data = no degradation).

The score is clamped to `[0.0, 1.0]`.

---

## 5. SLA Percentile Calculation

Given a set of `duration_seconds` values from completed runs of a workflow:

1. Sort durations ascending.
2. Compute percentile index: `idx = ceil(percentile / 100.0 * len(durations)) - 1`.
3. Clamp index to `[0, len(durations) - 1]`.
4. Return the value at that index.

```python
def _percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    idx = min(int(p / 100.0 * len(sorted_values)), len(sorted_values) - 1)
    return sorted_values[idx]
```

SLA output:

```json
{
  "p50": 45.2,
  "p95": 120.0,
  "p99": 180.5,
  "sample_size": 20
}
```

---

## 6. Dashboard Data Shape

The dashboard endpoint (W4-031) consumes:

```json
{
  "workflow_id": "daily-executive-briefing",
  "health_score": 0.92,
  "last_run": {
    "run_id": "abc123",
    "status": "completed",
    "duration_seconds": 34.5,
    "total_cost": 0.12,
    "completed_steps": 5,
    "total_steps": 5
  },
  "slas": {
    "p50": 32.0,
    "p95": 68.0,
    "p99": 95.0,
    "sample_size": 18
  },
  "history": [
    {
      "run_id": "abc123",
      "status": "completed",
      "duration_seconds": 34.5,
      "started_at": "2026-08-12T09:00:00Z",
      "completed_at": "2026-08-12T09:00:35Z"
    }
  ],
  "summary": {
    "total_runs": 20,
    "success_rate": 0.95,
    "avg_duration_seconds": 41.2,
    "total_cost": 2.40,
    "avg_retries": 0.15
  }
}
```

---

## 7. Integration Points

### 7.1 With WorkflowEngine

The collector is instantiated in `WorkflowEngine.__init__` and called at lifecycle points. The engine does not await or depend on the collector — recording failures are logged but do not block execution.

### 7.2 With AuditStore

TraceSpans carry `run_id` which correlates to `AuditStore` entries via the existing `correlation_id` mechanism. This enables cross-referencing workflow traces with tool calls and decisions.

### 7.3 With CostTracker

Step costs are passed into `record_step_complete` from the `CostTracker` summary. The collector sums them into `total_cost` on the `WorkflowMetrics` record.

---

## 8. Files

| File | Purpose |
|------|---------|
| `src/lightspeed_agents/workflow/metrics.py` | Models + collector implementation |
| `tests/test_workflow_metrics.py` | Unit tests (W4-035) |
| `docs/designs/w4-028-workflow-metrics-model.md` | This document |

---

*Document Version: 1.0*  
*Owner: data-engineer, Light Speed Holdings, Inc.*
