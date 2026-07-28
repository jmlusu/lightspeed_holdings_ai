# W4-019: Checkpoint/Rollback Model — Design Document

## Problem

When a workflow step fails, the entire workflow is marked FAILED with no recovery path. There is no way to:
- Save workflow state at step boundaries
- Roll back to a previous consistent state
- Execute compensating actions (undo partial work)
- Resume from a checkpoint after failure

## Architecture

```
┌──────────────────┐     ┌──────────────────────┐
│  WorkflowEngine  │────▶│  CheckpointManager   │
│   (engine.py)    │     │  (checkpoint.py)     │
└──────────────────┘     └──────────────────────┘
        │                          │
        ▼                          ▼
┌──────────────────┐     ┌──────────────────────┐
│  WorkflowRun     │     │  WorkflowCheckpoint  │
│  (step_results)  │     │  (step_states snap)  │
└──────────────────┘     └──────────────────────┘
```

## Data Models

### WorkflowCheckpoint (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| id | str | Unique checkpoint ID (auto-generated) |
| run_id | str | Parent workflow run |
| workflow_id | str | Workflow definition ID |
| step_id | str | Step that triggered this checkpoint |
| step_index | int | Step index in the workflow sequence |
| created_at | str | ISO timestamp |
| step_states | dict[str, CheckpointStepState] | Snapshot of all step states |
| status_snapshot | str | Workflow status at checkpoint time |
| metadata | dict | Additional context |

### CheckpointStepState (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| step_id | str | Step identifier |
| status | str | Step status at checkpoint |
| result | str | Step result if completed |
| error | str | Step error if failed |
| task_id | str | Associated task ID |

### RollbackResult (Pydantic)

| Field | Type | Description |
|-------|------|-------------|
| success | bool | Whether rollback succeeded |
| checkpoint_id | str | Checkpoint rolled back to |
| restored_step_index | int | Step index to resume from |
| steps_reset | list[str] | Steps that were reset |
| compensating_actions_executed | list[str] | Steps with compensating actions |
| error | str | Error message if rollback failed |

## CheckpointManager Interface

| Method | Description |
|--------|-------------|
| `create_checkpoint(run_id, workflow_id, step_id, step_index, steps, step_results, status, metadata)` | Creates snapshot at step boundary |
| `get_latest_checkpoint(run_id) -> WorkflowCheckpoint \| None` | Gets most recent checkpoint for a run |
| `get_checkpoint(checkpoint_id) -> WorkflowCheckpoint \| None` | Gets specific checkpoint |
| `get_checkpoints_for_run(run_id) -> list[WorkflowCheckpoint]` | Lists all checkpoints for a run |
| `rollback_to_checkpoint(checkpoint, steps) -> RollbackResult` | Computes rollback plan |
| `restore_run_state(checkpoint) -> dict[str, dict]` | Restores step_results from checkpoint |
| `delete_checkpoints_for_run(run_id) -> int` | Cleans up checkpoints |

## Integration Points

### W4-021: Checkpoint Creation at Step Boundaries

In `WorkflowEngine.complete_step()`, after saving the run:
```python
self.checkpoint_manager.create_checkpoint(
    run_id=run.id,
    workflow_id=run.workflow_id,
    step_id=step_id,
    step_index=run.current_step_index,
    steps=workflow.steps,
    step_results=run.step_results,
)
```

### W4-022: Rollback to Checkpoint

In `WorkflowEngine.fail_step()`, after marking failure:
```python
checkpoint = self.checkpoint_manager.get_latest_checkpoint(run.id)
if checkpoint:
    rollback = self.checkpoint_manager.rollback_to_checkpoint(checkpoint, workflow.steps)
    restored = self.checkpoint_manager.restore_run_state(checkpoint)
    run.step_results = restored
    run.current_step_index = checkpoint.step_index
    run.status = WorkflowStatus.RUNNING
```

### W4-023: Compensating Actions

Each `WorkflowStep` has an optional `compensating_action: str` field. During rollback, steps with compensating actions are flagged for execution. The engine can execute these as reverse operations.

### W4-024: Failure Handling Integration

The rollback order is:
1. Step fails
2. Check retry policy (W4-012) — if retries available, retry
3. If retries exhausted, get latest checkpoint
4. Rollback to checkpoint
5. Execute compensating actions
6. Resume from restored state

## Rollback State Machine

```
RUNNING ──▶ STEP_FAILED ──▶ RETRY_CHECK
                                │
                    ┌───────────┴───────────┐
                    │                       │
              Retries Left            Retries Exhausted
                    │                       │
                    ▼                       ▼
              RETRY_STEP            GET_CHECKPOINT
                                        │
                                        ▼
                                  ROLLBACK_TO_CP
                                        │
                                        ▼
                              EXECUTE_COMPENSATIONS
                                        │
                                        ▼
                                  RESUME_FROM_CP
```

## Checkpoint Storage

- Stored in `workflow_checkpoints.json` via FileStore
- CRC32 integrity checks (from W4-048)
- One checkpoint per step completion
- Old checkpoints can be pruned (keep last N per run)

## Edge Cases

| Case | Handling |
|------|----------|
| No checkpoint exists | Rollback fails gracefully, workflow stays FAILED |
| Checkpoint step state is stale | Restore from checkpoint, re-dispatch incomplete steps |
| Compensating action fails | Log warning, continue rollback for other steps |
| Parallel workflow checkpoint | Snapshot includes all parallel step states |
| Checkpoint after approval gate | Restore to waiting_approval state |

## File Structure

New file: `src/lightspeed_agents/workflow/checkpoint.py`

| Export | Type | Purpose |
|--------|------|---------|
| WorkflowCheckpoint | model | Checkpoint data |
| CheckpointStepState | model | Per-step snapshot |
| RollbackResult | model | Rollback outcome |
| CheckpointManager | class | Checkpoint CRUD + rollback |
