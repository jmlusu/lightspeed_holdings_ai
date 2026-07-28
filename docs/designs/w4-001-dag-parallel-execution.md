# W4-001: DAG-Based Parallel Execution Model

**Sprint**: 4
**Task**: W4-001
**Author**: chief-architect
**Date**: 2026-07-28
**Status**: Approved

---

## 1. Problem Statement

The current `WorkflowEngine._advance_steps()` executes workflow steps sequentially,
iterating through `workflow.steps` in list order with a `current_step_index` pointer.
Steps without inter-dependencies are unnecessarily serialized. Workflows like
`incident-response` or any future fan-out/fan-in pattern cannot exploit parallelism.

The `WorkflowStep.depends_on` field already encodes a directed graph, but the
engine ignores it for concurrency purposes.

## 2. Goals

1. Build a `WorkflowDAG` class that models step dependencies as a directed acyclic graph.
2. Validate the graph has no cycles at construction time (fail-fast).
3. Identify independent steps that can execute concurrently.
4. Identify join points where parallel branches converge and must all complete.
5. Support a `max_parallel` knob to cap concurrent step count.
6. Provide a clean interface for `WorkflowEngine` integration without breaking the
   existing sequential model (backward compatible — linear workflows remain linear).

## 3. Architecture Overview

### 3.1 System Diagram

```
                    ┌──────────────────────────────────┐
                    │         WorkflowEngine            │
                    │                                    │
                    │  _advance_steps()                  │
                    │    │                               │
                    │    ▼                               │
                    │  WorkflowDAG.get_ready_steps()     │
                    │    │                               │
                    │    ▼                               │
                    │  [dispatch N tasks to MessageBus]  │
                    │    │                               │
                    │    ▼                               │
                    │  on step_complete:                 │
                    │    DAG.get_ready_steps(completed)  │
                    │    dispatch next batch             │
                    └──────────────────────────────────┘

   WorkflowDAG Internals:
   ┌─────────────────────────────────────────────────────┐
   │                    WorkflowDAG                       │
   │                                                      │
   │  adjacency:  dict[str, set[str]]  (id → dependents) │
   │  in_degree:  dict[str, int]       (id → count)      │
   │  steps_by_id: dict[str, WorkflowStep]                │
   │                                                      │
   │  ┌──────────┐     ┌──────────┐     ┌──────────┐    │
   │  │  detect  │     │ analyze  │     │ resolve  │    │
   │  │  (L0)    │     │  (L1)    │     │  (L2)    │    │
   │  └────┬─────┘     └────┬─────┘     └────┬─────┘    │
   │       │                │                │            │
   │       ▼                ▼                ▼            │
   │  ┌──────────┐     ┌──────────┐                       │
   │  │ escalate │     │investigate│                      │
   │  │  (L1)    │     │  (L2)    │                       │
   │  └──────────┘     └──────────┘                       │
   └─────────────────────────────────────────────────────┘

   Execution Layers (from topological sort):
   ─────────────────────────────────────────
   Layer 0:  [detect]                        ← 1 parallel slot
   Layer 1:  [escalate, analyze]             ← 2 parallel slots
   Layer 2:  [resolve, investigate]          ← 2 parallel slots
   Layer 3:  [postmortem]                    ← 1 parallel slot
```

### 3.2 Data Flow

```
  YAML workflows.yaml
        │
        ▼
  loader.py → list[WorkflowStep]
        │
        ▼
  WorkflowDAG(steps)
        │  builds adjacency + in_degree
        │  validates acyclicity
        ▼
  ┌─── Execution Loop ────────────────────────┐
  │  completed: set[str] = ∅                    │
  │  while completed ≠ all_steps:               │
  │    ready = get_ready_steps(completed)        │
  │    ready = ready[:max_parallel]              │
  │    dispatch(ready)                           │
  │    wait for callbacks...                     │
  │    completed.add(step_id)                    │
  │    repeat                                    │
  └─────────────────────────────────────────────┘
```

## 4. Class Design

### 4.1 `WorkflowDAG`

```python
from __future__ import annotations

from collections import defaultdict, deque
from typing import Optional

from lightspeed_agents.workflow.models import WorkflowStep


class DAGValidationError(Exception):
    """Raised when a workflow contains a dependency cycle."""


class StepNotFoundError(Exception):
    """Raised when referencing a step ID that does not exist in the DAG."""


class WorkflowDAG:
    """Directed acyclic graph of workflow steps with parallel execution support.

    Builds a DAG from a list of WorkflowStep objects, validates acyclicity,
    and provides query methods for parallel scheduling.

    Usage:
        dag = WorkflowDAG(workflow.steps)
        dag.validate()  # raises DAGValidationError on cycles

        # Get steps ready to execute
        ready = dag.get_ready_steps(completed={"create_task", "assign_agent"})

        # Get execution layers for batch scheduling
        layers = dag.get_execution_layers()
    """

    def __init__(self, steps: list[WorkflowStep]) -> None:
        self._steps_by_id: dict[str, WorkflowStep] = {}
        self._adjacency: dict[str, set[str]] = defaultdict(set)
        self._in_degree: dict[str, int] = {}
        self._validated: bool = False

        for step in steps:
            self._steps_by_id[step.id] = step
            if step.id not in self._in_degree:
                self._in_degree[step.id] = 0

        for step in steps:
            for dep_id in step.depends_on:
                self._adjacency[dep_id].add(step.id)
                self._in_degree[step.id] += 1

    def validate(self) -> bool:
        """Check the graph contains no cycles using Kahn's algorithm.

        Returns True if valid. Raises DAGValidationError if a cycle exists.
        After validation, the DAG is marked as validated and subsequent calls
        skip re-computation.
        """
        if self._validated:
            return True

        in_degree = dict(self._in_degree)
        queue: deque[str] = deque(
            sid for sid, deg in in_degree.items() if deg == 0
        )
        visited_count = 0

        while queue:
            node = queue.popleft()
            visited_count += 1
            for dependent in self._adjacency[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if visited_count != len(self._steps_by_id):
            cycle_members = [
                sid
                for sid, deg in self._in_degree.items()
                if in_degree[sid] > 0
            ]
            raise DAGValidationError(
                f"Dependency cycle detected involving steps: {cycle_members}"
            )

        self._validated = True
        return True

    def get_ready_steps(
        self,
        completed: set[str],
        running: Optional[set[str]] = None,
    ) -> list[WorkflowStep]:
        """Return steps whose dependencies are all satisfied and are not yet
        dispatched.

        Args:
            completed: IDs of steps that have finished successfully.
            running: IDs of steps currently in progress (optional, used to
                     prevent re-dispatch of in-flight steps).

        Returns:
            List of WorkflowStep objects eligible for immediate execution.
            Order is deterministic (sorted by ID) but steps are independent
            and can be dispatched in any order.
        """
        running = running or set()
        ready = []

        for step_id, step in self._steps_by_id.items():
            if step_id in completed or step_id in running:
                continue

            deps_met = all(
                dep in completed for dep in step.depends_on
            )
            if deps_met:
                ready.append(step)

        ready.sort(key=lambda s: s.id)
        return ready

    def get_dependents(self, step_id: str) -> list[str]:
        """Return IDs of steps that directly depend on the given step.

        Args:
            step_id: The step to query.

        Returns:
            List of downstream step IDs (empty if leaf node).

        Raises:
            StepNotFoundError: If step_id is not in the DAG.
        """
        if step_id not in self._steps_by_id:
            raise StepNotFoundError(f"Step '{step_id}' not found in DAG")
        return sorted(self._adjacency.get(step_id, set()))

    def get_execution_layers(self) -> list[list[WorkflowStep]]:
        """Return steps grouped into parallel execution layers.

        Steps within the same layer have no inter-dependencies and can run
        concurrently. Layer N completes before any step in layer N+1 begins.

        Uses Kahn's algorithm to compute the longest-path (critical path)
        layer assignment: layer[step] = max(layer[dep] + 1 for dep in deps).

        Returns:
            List of layers, each layer is a list of WorkflowStep objects.
            Steps in the same layer are sorted by ID.
        """
        in_degree = dict(self._in_degree)
        layer_of: dict[str, int] = {sid: 0 for sid in self._steps_by_id}

        queue: deque[str] = deque(
            sid for sid, deg in in_degree.items() if deg == 0
        )

        while queue:
            node = queue.popleft()
            for dependent in self._adjacency[node]:
                layer_of[dependent] = max(
                    layer_of[dependent],
                    layer_of[node] + 1,
                )
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        max_layer = max(layer_of.values()) if layer_of else -1
        layers: list[list[WorkflowStep]] = [[] for _ in range(max_layer + 1)]
        for step_id, lyr in layer_of.items():
            layers[lyr].append(self._steps_by_id[step_id])

        for layer in layers:
            layer.sort(key=lambda s: s.id)

        return layers

    @property
    def step_count(self) -> int:
        return len(self._steps_by_id)

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        return self._steps_by_id.get(step_id)

    def all_step_ids(self) -> list[str]:
        return sorted(self._steps_by_id.keys())
```

### 4.2 Integration with `WorkflowEngine._advance_steps()`

The engine method is modified to use the DAG for step discovery instead of
index-based iteration. The key change: replace the `for i in range(...)` loop
with `get_ready_steps()`.

```python
# In WorkflowEngine:

def __init__(self, ..., max_parallel: int = 5):
    ...
    self.max_parallel = max_parallel

def _advance_steps(self, workflow, run, context=None):
    from lightspeed_agents.workflow.dag import WorkflowDAG

    dag = WorkflowDAG(workflow.steps)
    dag.validate()

    completed = {
        sid for sid, res in run.step_results.items()
        if res.get("status") in ("completed", "skipped")
    }
    running = {
        sid for sid, res in run.step_results.items()
        if res.get("status") in ("in_progress", "waiting_approval")
    }

    ready = dag.get_ready_steps(completed, running)
    dispatched = 0

    for step_def in ready:
        if dispatched >= self.max_parallel:
            break

        if step_def.id in run.step_results:
            continue

        # dispatch task (existing logic)
        task = self.bus.send_task(...)
        step_def.task_id = task.id
        step_def.status = WorkflowStepStatus.IN_PROGRESS
        run.step_results[step_def.id] = { ... }
        dispatched += 1

    if not ready and not running:
        run.status = WorkflowStatus.COMPLETED
        run.completed_at = datetime.now(UTC).isoformat()
        run.touch()
        self._save_run(run)
```

### 4.3 `max_parallel` Limiting

```
max_parallel = 3

Layer 0:  [A]              → dispatch A (1/3 slots)
Layer 1:  [B, C, D]        → dispatch B, C, D (3/3 slots)
Layer 2:  [E, F]           → dispatch E, F (2/3 slots) — after B,C,D complete
Layer 3:  [G]              → dispatch G (1/3 slots) — after E,F complete

If Layer 1 had [B, C, D, E]:
  → dispatch B, C, D (3/3 slots)
  → wait for one to complete
  → dispatch E (now 3/3 again)
```

The limiting operates per-call to `get_ready_steps`:
1. `get_ready_steps()` returns ALL currently ready steps (no limit).
2. The caller slices `[:max_parallel]` before dispatching.
3. When a step completes, `_advance_steps()` is called again, which calls
   `get_ready_steps()` with the updated `completed` set.
4. The new batch is dispatched up to `max_parallel - len(currently_running)`.

This keeps the DAG layer-agnostic — the DAG answers "what CAN run", the engine
decides "how many TO run".

## 5. Edge Cases and Error Handling

| Case | Behavior |
|------|----------|
| **Cycle detected** | `validate()` raises `DAGValidationError` with cycle member IDs. Workflow refuses to start. |
| **Unknown dependency** | `__init__` increments in-degree for steps referencing non-existent IDs. `validate()` catches this as part of cycle detection. If the referenced step doesn't exist in the list, the dependent's in-degree never reaches 0 → cycle error. **Fix**: also validate all `depends_on` entries reference existing step IDs in `__init__`. |
| **Duplicate step IDs** | `__init__` uses dict — last-write-wins with a warning log. Document: step IDs must be unique. |
| **Empty workflow** | Returns empty layers, `validate()` returns True, `get_ready_steps()` returns `[]`. |
| **Single step, no deps** | Layer 0: `[step]`. Executes immediately. |
| **All steps independent** | Single layer: `[all steps]`. All dispatched in one batch (up to `max_parallel`). |
| **Leaf nodes (no dependents)** | `get_dependents()` returns `[]`. `get_execution_layers()` places them in the final layer. |
| **Step failure** | Engine sets `run.status = FAILED`. DAG is not consulted further until `complete_step` or `fail_step` triggers `_advance_steps`. Failed steps block downstream dependents (deps check requires `completed` status). |
| **Approval-gated steps** | Appear in `running` set. `get_ready_steps()` excludes them. Downstream steps wait. |

## 6. Implementation Plan

| Task | Owner | Deliverable |
|------|-------|-------------|
| W4-001 | chief-architect | Design doc + `dag.py` skeleton |
| W4-002 | lead-engineer | Engine integration in `engine.py` |
| W4-003 | lead-engineer | Unit tests for DAG + engine integration |
| W4-004 | devops-engineer | Add parallel execution metrics to monitoring |

## 7. Backward Compatibility

- Workflows with zero `depends_on` fields produce a single execution layer —
  identical to current sequential behavior.
- Workflows with strict linear dependencies (`A → B → C → D`) produce one
  step per layer — identical to current sequential behavior.
- The `WorkflowRun.current_step_index` field becomes unused by the DAG engine
  but is preserved for API compatibility. It can be deprecated in Sprint 5.
- No changes to `WorkflowStep` or `Workflow` models.
- No changes to the YAML schema.

## 8. Testing Strategy

1. **Unit tests for `WorkflowDAG`**:
   - Linear chain: `A → B → C` produces 3 layers of 1 step each.
   - Diamond: `A → [B, C] → D` produces layers `[A], [B,C], [D]`.
   - Parallel fan-out: `[A, B, C]` (no deps) produces 1 layer of 3 steps.
   - Cycle detection: `A → B → C → A` raises `DAGValidationError`.
   - Self-loop: `A → A` raises `DAGValidationError`.
   - Empty input: returns empty layers.
   - `get_ready_steps()` with partial completions.
   - `get_dependents()` for leaf and branch nodes.

2. **Integration tests for engine**:
   - Start workflow, complete steps in any order, verify DAG advancement.
   - Verify `max_parallel` caps concurrent dispatches.
   - Verify approval-gated steps block downstream.

## 9. Open Questions

- Should `max_parallel` be per-workflow (config in YAML) or global (engine config)?
  **Decision**: Global for now. Per-workflow can be added in Sprint 5.
- Should the DAG support weighted edges (step priority within a layer)?
  **Decision**: Not in scope. Steps within a layer are sorted by ID for determinism.
- Should `complete_step()` re-evaluate the DAG eagerly or lazily?
  **Decision**: Eagerly — call `_advance_steps()` immediately after completion (matches current behavior).
