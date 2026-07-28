# W4-010: Retry Policy Model — Design Document

## Problem

The current `WorkflowEngine.fail_step()` immediately marks steps as FAILED with no recovery. The `DeadLetterQueue` only handles stale tasks (30-min timeout). Transient failures (rate limits, timeouts, temporary errors) cause permanent workflow failure.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  WorkflowStep │────▶│ RetryPolicy  │────▶│   Executor   │
│  (models.py) │     │  (retry.py)  │     │ (executor.py)│
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                     ┌──────┴──────┐
                     │ BackoffCalc │
                     │  (jitter)   │
                     └─────────────┘
```

## Data Models

### RetryPolicy (Pydantic)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| max_retries | int | 3 | Maximum retry attempts (0-10) |
| backoff_base | float | 2.0 | Base for exponential backoff |
| backoff_max | float | 60.0 | Maximum backoff in seconds |
| jitter | bool | True | Add random jitter to prevent thundering herd |
| retry_on | list[str] | ["timeout", "rate_limit", "temporary_error"] | Error types to retry |
| no_retry_on | list[str] | ["auth_error", "validation_error", "not_found"] | Error types NOT to retry |

### StepRetryState (Pydantic)

Tracks per-step retry state within a workflow run.

| Field | Type | Description |
|-------|------|-------------|
| step_id | str | Step identifier |
| run_id | str | Workflow run identifier |
| attempt | int | Current attempt number |
| max_retries | int | Maximum allowed retries |
| last_error | str | Most recent error message |
| last_error_type | str | Classification of last error |
| next_retry_at | str \| None | ISO timestamp for next retry |
| retry_history | list[dict] | Full history of retry attempts |

## Backoff Algorithm

```
delay = min(backoff_base ^ attempt, backoff_max)
if jitter:
    delay += random(0, delay * 0.1)
```

### Example Delays (base=2.0, max=60.0)

| Attempt | Base Delay | With Jitter (approx) |
|---------|-----------|---------------------|
| 1 | 2.0s | 2.0-2.2s |
| 2 | 4.0s | 4.0-4.4s |
| 3 | 8.0s | 8.0-8.8s |
| 4 | 16.0s | 16.0-17.6s |
| 5 | 32.0s | 32.0-35.2s |
| 6 | 60.0s | 60.0-66.0s (capped) |

## Integration Points

### W4-011: RetryPolicy on WorkflowStep
- Add `retry_policy: RetryPolicy | None = None` to `WorkflowStep`
- YAML parsing: `retry:` block in step definition

### W4-012: Auto Retry in Executor
- Modify `Executor._process_task()` to catch retryable errors
- On failure: check `RetryPolicy.should_retry(error_type, attempt)`
- If retryable: calculate delay, schedule re-execution
- If not retryable or exhausted: fail permanently

### W4-013: Backoff Calculation
- Standalone `calculate_delay()` method in RetryPolicy
- Used by Executor for scheduling next attempt

### W4-014: Retry State in Task Model
- Already has `retry_count: int = 0`
- Add `retry_state: StepRetryState | None = None` for workflow context

### W4-015: DLQ Enhancement
- DLQ should check if failed task has remaining retries
- If retries available: move back to pending with delay
- If exhausted: keep in DLQ permanently

## Error Classification

| Error Type | Retryable | Reason |
|-----------|-----------|--------|
| timeout | Yes | Transient network issue |
| rate_limit | Yes | Provider throttle, will resolve |
| temporary_error | Yes | Generic transient |
| auth_error | No | Permanent credential issue |
| validation_error | No | Bad input, won't self-fix |
| not_found | No | Missing resource |
| permission_denied | No | Access control, won't self-fix |

## State Machine

```
PENDING ──▶ RUNNING ──▶ FAILED ──▶ RETRYING ──▶ RUNNING
                                │                  │
                                │    ┌─────────────┘
                                │    │
                                ▼    ▼
                            EXHAUSTED (permanent failure)
```
