from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Optional

from pydantic import BaseModel, Field

from lightspeed_agents.message_bus.file_store import FileStore

CHECKPOINTS_FILE = "workflow_checkpoints.json"


class CheckpointStepState(BaseModel):
    step_id: str
    status: str = "pending"
    result: str = ""
    error: str = ""
    task_id: str = ""


class WorkflowCheckpoint(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    run_id: str
    workflow_id: str
    step_id: str
    step_index: int
    created_at: str = ""
    step_states: dict[str, CheckpointStepState] = {}
    status_snapshot: str = "running"
    metadata: dict = {}

    def __init__(self, **data):
        if not data.get("created_at"):
            data["created_at"] = datetime.now(UTC).isoformat()
        super().__init__(**data)


class RollbackResult(BaseModel):
    success: bool
    checkpoint_id: str
    restored_step_index: int
    steps_reset: list[str] = []
    compensating_actions_executed: list[str] = []
    error: str = ""


class CheckpointManager:

    def __init__(self, store_dir: str = ".opencode"):
        self._store = FileStore(store_dir)

    def create_checkpoint(
        self,
        run_id: str,
        workflow_id: str,
        step_id: str,
        step_index: int,
        steps: list,
        step_results: dict[str, dict],
        status: str = "running",
        metadata: dict | None = None,
    ) -> WorkflowCheckpoint:
        step_states = {}
        for step in steps:
            result = step_results.get(step.id, {})
            step_states[step.id] = CheckpointStepState(
                step_id=step.id,
                status=result.get("status", "pending"),
                result=result.get("result", ""),
                error=result.get("error", ""),
                task_id=result.get("task_id", ""),
            )

        checkpoint = WorkflowCheckpoint(
            run_id=run_id,
            workflow_id=workflow_id,
            step_id=step_id,
            step_index=step_index,
            step_states=step_states,
            status_snapshot=status,
            metadata=metadata or {},
        )

        self._save_checkpoint(checkpoint)
        return checkpoint

    def get_latest_checkpoint(self, run_id: str) -> Optional[WorkflowCheckpoint]:
        checkpoints = self._load_checkpoints()
        run_checkpoints = [c for c in checkpoints if c.run_id == run_id]
        if not run_checkpoints:
            return None
        return max(run_checkpoints, key=lambda c: c.created_at)

    def get_checkpoint(self, checkpoint_id: str) -> Optional[WorkflowCheckpoint]:
        for c in self._load_checkpoints():
            if c.id == checkpoint_id:
                return c
        return None

    def get_checkpoints_for_run(self, run_id: str) -> list[WorkflowCheckpoint]:
        return sorted(
            [c for c in self._load_checkpoints() if c.run_id == run_id],
            key=lambda c: c.created_at,
        )

    def rollback_to_checkpoint(
        self,
        checkpoint: WorkflowCheckpoint,
        steps: list,
    ) -> RollbackResult:
        steps_reset = []
        compensating_actions = []

        for step in steps:
            state = checkpoint.step_states.get(step.id)
            if state and state.status in ("in_progress", "waiting_approval"):
                steps_reset.append(step.id)
                if step.compensating_action:
                    compensating_actions.append(step.id)

        return RollbackResult(
            success=True,
            checkpoint_id=checkpoint.id,
            restored_step_index=checkpoint.step_index,
            steps_reset=steps_reset,
            compensating_actions_executed=compensating_actions,
        )

    def restore_run_state(
        self,
        checkpoint: WorkflowCheckpoint,
    ) -> dict[str, dict]:
        restored = {}
        for step_id, state in checkpoint.step_states.items():
            restored[step_id] = {
                "status": state.status,
                "result": state.result,
                "error": state.error,
                "task_id": state.task_id,
            }
        return restored

    def delete_checkpoints_for_run(self, run_id: str) -> int:
        all_checkpoints = self._load_checkpoints()
        remaining = [c for c in all_checkpoints if c.run_id != run_id]
        deleted = len(all_checkpoints) - len(remaining)
        self._store.save(
            CHECKPOINTS_FILE,
            [c.model_dump(mode="json") for c in remaining],
        )
        return deleted

    def _save_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        all_checkpoints = self._load_checkpoints()
        all_checkpoints.append(checkpoint)
        self._store.save(
            CHECKPOINTS_FILE,
            [c.model_dump(mode="json") for c in all_checkpoints],
        )

    def _load_checkpoints(self) -> list[WorkflowCheckpoint]:
        raw = self._store.load(CHECKPOINTS_FILE)
        return [WorkflowCheckpoint(**c) for c in raw]
