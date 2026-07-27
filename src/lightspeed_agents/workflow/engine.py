from datetime import datetime, timezone
from typing import Callable, Optional

from lightspeed_agents.workflow.models import (
    Workflow,
    WorkflowRun,
    WorkflowStep,
    WorkflowStatus,
    WorkflowStepStatus,
)
from lightspeed_agents.workflow.loader import load_workflows, get_workflow
from lightspeed_agents.message_bus.message_bus import MessageBus
from lightspeed_agents.message_bus.task import Task
from lightspeed_agents.message_bus.task_status import TaskStatus, TaskPriority
from lightspeed_agents.message_bus.file_store import FileStore
from lightspeed_agents.memory.engine import MemoryEngine


RUNS_FILE = "workflow_runs.json"


class WorkflowEngine:

    def __init__(
        self,
        bus: MessageBus = None,
        memory: MemoryEngine = None,
        bus_dir: str = ".opencode",
        workflows_path: str = None,
    ):
        self.bus = bus or MessageBus(bus_dir)
        self.memory = memory or MemoryEngine()
        self.store = FileStore(bus_dir)
        self.workflows_path = workflows_path

    def list_workflows(self) -> list[Workflow]:
        return load_workflows(self.workflows_path)

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return get_workflow(workflow_id, self.workflows_path)

    def start_workflow(
        self,
        workflow_id: str,
        initial_context: dict = None,
    ) -> WorkflowRun:
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_id}' not found")

        run = WorkflowRun(workflow_id=workflow_id)
        run.status = WorkflowStatus.RUNNING
        run.started_at = datetime.now(timezone.utc).isoformat()
        run.touch()

        self._save_run(run)
        self.memory.record_task_outcome(
            task_id=run.id,
            agent_id=workflow.owner,
            content=f"Started workflow: {workflow.name}",
            status="running",
            tags=["workflow", workflow_id],
        )

        self._advance_steps(workflow, run, initial_context)
        return run

    def get_run(self, run_id: str) -> Optional[WorkflowRun]:
        runs = self._load_runs()
        for run in runs:
            if run.id == run_id:
                return run
        return None

    def get_runs_by_workflow(self, workflow_id: str) -> list[WorkflowRun]:
        return [
            r for r in self._load_runs()
            if r.workflow_id == workflow_id
        ]

    def get_all_runs(self) -> list[WorkflowRun]:
        return self._load_runs()

    def complete_step(
        self,
        run_id: str,
        step_id: str,
        result: str = "",
    ) -> WorkflowRun:
        run = self.get_run(run_id)
        if not run:
            raise ValueError(f"Run '{run_id}' not found")

        workflow = self.get_workflow(run.workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{run.workflow_id}' not found")

        step = self._find_step(workflow, step_id)
        if not step:
            raise ValueError(f"Step '{step_id}' not found")

        step.status = WorkflowStepStatus.COMPLETED
        step.result = result
        run.step_results[step_id] = {
            "status": "completed",
            "result": result,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

        if step.task_id:
            self.bus.complete_task(step.task_id, result=result)

        run.touch()
        self._save_run(run)

        self.memory.record_task_outcome(
            task_id=run.id,
            agent_id=step.assignee,
            content=f"Completed step '{step_id}': {result[:200]}",
            status="completed",
            tags=["workflow", run.workflow_id, step_id],
        )

        self._advance_steps(workflow, run)
        return run

    def fail_step(
        self,
        run_id: str,
        step_id: str,
        error: str = "",
    ) -> WorkflowRun:
        run = self.get_run(run_id)
        if not run:
            raise ValueError(f"Run '{run_id}' not found")

        workflow = self.get_workflow(run.workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{run.workflow_id}' not found")

        step = self._find_step(workflow, step_id)
        if not step:
            raise ValueError(f"Step '{step_id}' not found")

        step.status = WorkflowStepStatus.FAILED
        step.error = error
        run.step_results[step_id] = {
            "status": "failed",
            "error": error,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }
        run.status = WorkflowStatus.FAILED
        run.touch()
        self._save_run(run)

        if step.task_id:
            self.bus.fail_task(step.task_id, error=error)

        self.memory.record_task_outcome(
            task_id=run.id,
            agent_id=step.assignee,
            content=f"Failed step '{step_id}': {error[:200]}",
            status="failed",
            tags=["workflow", run.workflow_id, step_id],
        )

        return run

    def approve_step(self, run_id: str, step_id: str) -> WorkflowRun:
        run = self.get_run(run_id)
        if not run:
            raise ValueError(f"Run '{run_id}' not found")

        workflow = self.get_workflow(run.workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{run.workflow_id}' not found")

        step = self._find_step(workflow, step_id)
        if not step:
            raise ValueError(f"Step '{step_id}' not found")

        if step.task_id:
            self.bus.approve_task(step.task_id)

        step.status = WorkflowStepStatus.IN_PROGRESS
        run.step_results[step_id]["status"] = "in_progress"
        run.touch()
        self._save_run(run)
        return run

    def cancel_workflow(self, run_id: str) -> WorkflowRun:
        run = self.get_run(run_id)
        if not run:
            raise ValueError(f"Run '{run_id}' not found")

        run.status = WorkflowStatus.CANCELLED
        run.touch()
        self._save_run(run)

        workflow = self.get_workflow(run.workflow_id)
        if workflow:
            for step_def in workflow.steps:
                step_result = run.step_results.get(step_def.id, {})
                if step_result.get("status") in ("pending", "in_progress"):
                    if step_def.task_id:
                        self.bus.cancel_task(step_def.task_id)

        return run

    def _advance_steps(
        self,
        workflow: Workflow,
        run: WorkflowRun,
        context: dict = None,
    ):
        steps = workflow.steps
        if run.current_step_index >= len(steps):
            run.status = WorkflowStatus.COMPLETED
            run.completed_at = datetime.now(timezone.utc).isoformat()
            run.touch()
            self._save_run(run)
            return

        for i in range(run.current_step_index, len(steps)):
            step_def = steps[i]

            step_result = run.step_results.get(step_def.id, {})
            if step_result.get("status") in ("completed", "failed"):
                run.current_step_index = i + 1
                continue

            deps_met = self._dependencies_met(step_def, workflow, run)
            if not deps_met:
                break

            task = self.bus.send_task(
                instruction=step_def.instruction,
                receiver_id=step_def.assignee,
                sender_id=workflow.owner,
                priority=TaskPriority.HIGH if step_def.requires_approval else TaskPriority.MEDIUM,
                tags=["workflow", workflow.id, step_def.id],
                metadata={
                    "workflow_id": workflow.id,
                    "run_id": run.id,
                    "step_id": step_def.id,
                    "tier": step_def.tier,
                },
            )

            step_def.task_id = task.id
            step_def.status = WorkflowStepStatus.IN_PROGRESS
            run.step_results[step_def.id] = {
                "status": "in_progress",
                "task_id": task.id,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }

            if step_def.requires_approval:
                step_def.status = WorkflowStepStatus.WAITING_APPROVAL
                self.bus.park_for_approval(task.id)
                run.step_results[step_def.id]["status"] = "waiting_approval"
                run.current_step_index = i
                run.touch()
                self._save_run(run)
                return

            run.current_step_index = i + 1
            run.touch()
            self._save_run(run)

    def _dependencies_met(
        self,
        step: WorkflowStep,
        workflow: Workflow,
        run: WorkflowRun,
    ) -> bool:
        for dep_id in step.depends_on:
            dep_result = run.step_results.get(dep_id, {})
            if dep_result.get("status") != "completed":
                return False
        return True

    def _find_step(
        self,
        workflow: Workflow,
        step_id: str,
    ) -> Optional[WorkflowStep]:
        for step in workflow.steps:
            if step.id == step_id:
                return step
        return None

    def _save_run(self, run: WorkflowRun):
        runs = self._load_runs()
        for i, existing in enumerate(runs):
            if existing.id == run.id:
                runs[i] = run
                break
        else:
            runs.append(run)
        self.store.save(RUNS_FILE, [r.model_dump(mode="json") for r in runs])

    def _load_runs(self) -> list[WorkflowRun]:
        raw = self.store.load(RUNS_FILE)
        return [WorkflowRun(**r) for r in raw]
