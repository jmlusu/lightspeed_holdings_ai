from __future__ import annotations

import logging
from collections import defaultdict, deque
from typing import Optional

from lightspeed_agents.workflow.models import WorkflowStep

logger = logging.getLogger(__name__)


class DAGValidationError(Exception):
    pass


class StepNotFoundError(Exception):
    pass


class WorkflowDAG:

    def __init__(self, steps: list[WorkflowStep]) -> None:
        self._steps_by_id: dict[str, WorkflowStep] = {}
        self._adjacency: dict[str, set[str]] = defaultdict(set)
        self._in_degree: dict[str, int] = {}
        self._validated: bool = False

        for step in steps:
            if step.id in self._steps_by_id:
                logger.warning(
                    "Duplicate step ID '%s' — last occurrence wins", step.id
                )
            self._steps_by_id[step.id] = step
            if step.id not in self._in_degree:
                self._in_degree[step.id] = 0

        for step in steps:
            for dep_id in step.depends_on:
                if dep_id not in self._steps_by_id:
                    logger.warning(
                        "Step '%s' depends on non-existent step '%s'",
                        step.id,
                        dep_id,
                    )
                self._adjacency[dep_id].add(step.id)
                self._in_degree[step.id] += 1

    def validate(self) -> bool:
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
        running = running or set()
        ready = []

        for step_id, step in self._steps_by_id.items():
            if step_id in completed or step_id in running:
                continue

            deps_met = all(dep in completed for dep in step.depends_on)
            if deps_met:
                ready.append(step)

        ready.sort(key=lambda s: s.id)
        return ready

    def get_dependents(self, step_id: str) -> list[str]:
        if step_id not in self._steps_by_id:
            raise StepNotFoundError(f"Step '{step_id}' not found in DAG")
        return sorted(self._adjacency.get(step_id, set()))

    def get_execution_layers(self) -> list[list[WorkflowStep]]:
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
