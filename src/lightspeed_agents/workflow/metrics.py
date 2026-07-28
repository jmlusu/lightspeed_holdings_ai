from __future__ import annotations

import statistics
import uuid
from datetime import datetime, UTC
from typing import Any

from pydantic import BaseModel, Field

from lightspeed_agents.message_bus.file_store import FileStore


class WorkflowMetrics(BaseModel):
    workflow_id: str
    run_id: str
    started_at: str
    completed_at: str | None = None
    duration_seconds: float | None = None
    status: str = "running"
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    total_cost: float = 0.0
    retry_count: int = 0
    parallel_steps: int = 0
    tags: list[str] = []


class TraceSpan(BaseModel):
    span_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    parent_span_id: str | None = None
    operation: str = ""
    start_time: str = ""
    end_time: str | None = None
    duration_ms: float | None = None
    status: str = "running"
    metadata: dict[str, Any] = {}


METRICS_FILE = "workflow_metrics.json"
TRACES_FILE = "workflow_traces.json"
MAX_TRACES = 10_000


class WorkflowMetricsCollector:

    def __init__(self, store_dir: str = ".opencode"):
        self._store = FileStore(store_dir)
        self._in_progress: dict[str, WorkflowMetrics] = {}
        self._active_spans: dict[str, TraceSpan] = {}

    def record_workflow_start(
        self, workflow_id: str, run_id: str
    ) -> WorkflowMetrics:
        metrics = WorkflowMetrics(
            workflow_id=workflow_id,
            run_id=run_id,
            started_at=datetime.now(UTC).isoformat(),
            status="running",
        )
        self._in_progress[run_id] = metrics

        root_span = TraceSpan(
            parent_span_id=None,
            operation="workflow.execute",
            start_time=metrics.started_at,
            status="running",
            metadata={"workflow_id": workflow_id, "run_id": run_id},
        )
        self._active_spans[f"{run_id}:root"] = root_span
        self._write_span(root_span)

        return metrics

    def record_step_start(
        self, run_id: str, step_id: str, assignee: str
    ) -> TraceSpan:
        metrics = self._in_progress.get(run_id)
        if metrics:
            active_count = sum(
                1
                for s_id, s in self._active_spans.items()
                if s_id.startswith(f"{run_id}:step:")
                and s.status == "running"
            )
            if active_count + 1 > metrics.parallel_steps:
                metrics.parallel_steps = active_count + 1

        parent_key = f"{run_id}:root"
        parent_span_id = (
            self._active_spans[parent_key].span_id
            if parent_key in self._active_spans
            else None
        )

        span = TraceSpan(
            parent_span_id=parent_span_id,
            operation="step.execute",
            start_time=datetime.now(UTC).isoformat(),
            status="running",
            metadata={"run_id": run_id, "step_id": step_id, "assignee": assignee},
        )
        self._active_spans[f"{run_id}:step:{step_id}"] = span
        self._write_span(span)
        return span

    def record_step_complete(
        self,
        run_id: str,
        step_id: str,
        duration: float,
        cost: float = 0.0,
    ) -> TraceSpan:
        metrics = self._in_progress.get(run_id)
        if metrics:
            metrics.completed_steps += 1
            metrics.total_cost += cost

        span_key = f"{run_id}:step:{step_id}"
        span = self._active_spans.pop(span_key, None)
        if span:
            span.end_time = datetime.now(UTC).isoformat()
            span.duration_ms = duration * 1000
            span.status = "completed"
            self._write_span(span)

        self._persist_metrics_if_done(run_id)
        return span or TraceSpan(operation="step.execute", status="completed")

    def record_step_fail(
        self, run_id: str, step_id: str, error: str, duration: float
    ) -> TraceSpan:
        metrics = self._in_progress.get(run_id)
        if metrics:
            metrics.failed_steps += 1

        span_key = f"{run_id}:step:{step_id}"
        span = self._active_spans.pop(span_key, None)
        if span:
            span.end_time = datetime.now(UTC).isoformat()
            span.duration_ms = duration * 1000
            span.status = "failed"
            span.metadata["error"] = error
            self._write_span(span)

        self._persist_metrics_if_done(run_id)
        return span or TraceSpan(
            operation="step.execute",
            status="failed",
            metadata={"error": error},
        )

    def record_workflow_complete(
        self, run_id: str, status: str
    ) -> WorkflowMetrics | None:
        metrics = self._in_progress.pop(run_id, None)
        if not metrics:
            return None

        now = datetime.now(UTC).isoformat()
        metrics.completed_at = now
        metrics.status = status

        start = datetime.fromisoformat(metrics.started_at)
        end = datetime.fromisoformat(now)
        metrics.duration_seconds = (end - start).total_seconds()

        root_key = f"{run_id}:root"
        root_span = self._active_spans.pop(root_key, None)
        if root_span:
            root_span.end_time = now
            root_span.duration_ms = metrics.duration_seconds * 1000
            root_span.status = "completed" if status == "completed" else "failed"
            self._write_span(root_span)

        self._append_metrics(metrics)
        return metrics

    def get_metrics(self, workflow_id: str) -> WorkflowMetrics | None:
        for run_id, m in self._in_progress.items():
            if m.workflow_id == workflow_id:
                return m
        all_metrics = self._load_metrics()
        matching = [m for m in all_metrics if m.workflow_id == workflow_id]
        if not matching:
            return None
        return matching[-1]

    def get_workflow_history(
        self, workflow_id: str, limit: int = 10
    ) -> list[WorkflowMetrics]:
        all_metrics = self._load_metrics()
        matching = [m for m in all_metrics if m.workflow_id == workflow_id]
        return matching[-limit:]

    def get_health_score(self, workflow_id: str) -> float:
        history = self.get_workflow_history(workflow_id, limit=20)
        completed = [m for m in history if m.status == "completed"]
        failed = [m for m in history if m.status == "failed"]

        total = len(history)
        if total == 0:
            return 1.0

        success_rate = len(completed) / total
        failure_rate = len(failed) / total

        target_duration = 60.0
        durations = [
            m.duration_seconds
            for m in completed
            if m.duration_seconds is not None
        ]
        if durations:
            median_dur = statistics.median(durations)
            speed_score = max(
                0.0, min(1.0, 1.0 - (median_dur - target_duration) / target_duration)
            )
        else:
            speed_score = 1.0

        health = 0.50 * success_rate + 0.25 * (1.0 - failure_rate) + 0.25 * speed_score
        return max(0.0, min(1.0, health))

    def get_slas(self, workflow_id: str) -> dict[str, Any]:
        history = self.get_workflow_history(workflow_id, limit=100)
        durations = sorted(
            m.duration_seconds
            for m in history
            if m.status == "completed" and m.duration_seconds is not None
        )

        if not durations:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "sample_size": 0}

        return {
            "p50": self._percentile(durations, 50.0),
            "p95": self._percentile(durations, 95.0),
            "p99": self._percentile(durations, 99.0),
            "sample_size": len(durations),
        }

    def get_traces(self, run_id: str) -> list[TraceSpan]:
        all_spans = self._load_spans()
        return [s for s in all_spans if s.metadata.get("run_id") == run_id]

    def record_retry(self, run_id: str, step_id: str) -> TraceSpan:
        metrics = self._in_progress.get(run_id)
        if metrics:
            metrics.retry_count += 1

        parent_key = f"{run_id}:step:{step_id}"
        parent_span_id = (
            self._active_spans[parent_key].span_id
            if parent_key in self._active_spans
            else None
        )

        span = TraceSpan(
            parent_span_id=parent_span_id,
            operation="step.retry",
            start_time=datetime.now(UTC).isoformat(),
            status="running",
            metadata={"run_id": run_id, "step_id": step_id},
        )
        self._write_span(span)
        return span

    def record_checkpoint(
        self, run_id: str, step_id: str
    ) -> TraceSpan:
        root_key = f"{run_id}:root"
        parent_span_id = (
            self._active_spans[root_key].span_id
            if root_key in self._active_spans
            else None
        )

        span = TraceSpan(
            parent_span_id=parent_span_id,
            operation="workflow.checkpoint",
            start_time=datetime.now(UTC).isoformat(),
            end_time=datetime.now(UTC).isoformat(),
            duration_ms=0.0,
            status="completed",
            metadata={"run_id": run_id, "step_id": step_id},
        )
        self._write_span(span)
        return span

    def get_dashboard_data(self, workflow_id: str) -> dict[str, Any]:
        history = self.get_workflow_history(workflow_id, limit=20)
        last_run = history[-1] if history else None
        health = self.get_health_score(workflow_id)
        slas = self.get_slas(workflow_id)

        completed_runs = [m for m in history if m.status == "completed"]
        total_runs = len(history)
        success_rate = len(completed_runs) / total_runs if total_runs > 0 else 0.0

        durations = [
            m.duration_seconds
            for m in completed_runs
            if m.duration_seconds is not None
        ]
        avg_duration = statistics.mean(durations) if durations else 0.0
        total_cost = sum(m.total_cost for m in history)
        avg_retries = (
            statistics.mean(m.retry_count for m in history) if history else 0.0
        )

        return {
            "workflow_id": workflow_id,
            "health_score": health,
            "last_run": {
                "run_id": last_run.run_id,
                "status": last_run.status,
                "duration_seconds": last_run.duration_seconds,
                "total_cost": last_run.total_cost,
                "completed_steps": last_run.completed_steps,
                "total_steps": last_run.total_steps,
            }
            if last_run
            else None,
            "slas": slas,
            "history": [
                {
                    "run_id": m.run_id,
                    "status": m.status,
                    "duration_seconds": m.duration_seconds,
                    "started_at": m.started_at,
                    "completed_at": m.completed_at,
                }
                for m in history
            ],
            "summary": {
                "total_runs": total_runs,
                "success_rate": round(success_rate, 4),
                "avg_duration_seconds": round(avg_duration, 2),
                "total_cost": round(total_cost, 4),
                "avg_retries": round(avg_retries, 2),
            },
        }

    def update_step_total(self, run_id: str, total: int) -> None:
        metrics = self._in_progress.get(run_id)
        if metrics:
            metrics.total_steps = total

    def add_tag(self, run_id: str, tag: str) -> None:
        metrics = self._in_progress.get(run_id)
        if metrics and tag not in metrics.tags:
            metrics.tags.append(tag)

    @staticmethod
    def _percentile(sorted_values: list[float], p: float) -> float:
        if not sorted_values:
            return 0.0
        idx = min(int(p / 100.0 * len(sorted_values)), len(sorted_values) - 1)
        return round(sorted_values[idx], 4)

    def _append_metrics(self, metrics: WorkflowMetrics) -> None:
        all_metrics = self._load_metrics()
        all_metrics.append(metrics)
        self._store.save(METRICS_FILE, [m.model_dump(mode="json") for m in all_metrics])

    def _persist_metrics_if_done(self, run_id: str) -> None:
        metrics = self._in_progress.get(run_id)
        if not metrics:
            return
        if metrics.status in ("completed", "failed", "cancelled"):
            self._in_progress.pop(run_id, None)
            self._append_metrics(metrics)

    def _write_span(self, span: TraceSpan) -> None:
        all_spans = self._load_spans()
        for i, existing in enumerate(all_spans):
            if existing.span_id == span.span_id:
                all_spans[i] = span
                break
        else:
            all_spans.append(span)

        if len(all_spans) > MAX_TRACES:
            all_spans = all_spans[-MAX_TRACES:]

        self._store.save(
            TRACES_FILE, [s.model_dump(mode="json") for s in all_spans]
        )

    def _load_metrics(self) -> list[WorkflowMetrics]:
        raw = self._store.load(METRICS_FILE)
        return [WorkflowMetrics(**m) for m in raw]

    def _load_spans(self) -> list[TraceSpan]:
        raw = self._store.load(TRACES_FILE)
        return [TraceSpan(**s) for s in raw]
