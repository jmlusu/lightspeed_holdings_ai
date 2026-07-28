from __future__ import annotations

import random
from enum import Enum

from pydantic import BaseModel, Field


class RetryState(str, Enum):
    RETRY = "retry"
    EXHAUSTED = "exhausted"
    PERMANENT_FAILURE = "permanent_failure"


class RetryPolicy(BaseModel):
    max_retries: int = Field(default=3, ge=0, le=10)
    backoff_base: float = Field(default=2.0, gt=0)
    backoff_max: float = Field(default=60.0, gt=0)
    jitter: bool = True
    retry_on: list[str] = Field(default_factory=lambda: ["timeout", "rate_limit", "temporary_error"])
    no_retry_on: list[str] = Field(default_factory=lambda: ["auth_error", "validation_error", "not_found"])

    def calculate_delay(self, attempt: int) -> float:
        if attempt <= 0:
            return 0.0

        base_delay = min(self.backoff_base ** attempt, self.backoff_max)

        if self.jitter:
            jitter_range = base_delay * 0.1
            return base_delay + random.uniform(0, jitter_range)

        return base_delay

    def should_retry(self, error_type: str, attempt: int) -> bool:
        if attempt >= self.max_retries:
            return False

        if error_type in self.no_retry_on:
            return False

        if self.retry_on and error_type not in self.retry_on:
            return False

        return True

    def get_retry_state(self, task_retry_count: int) -> RetryState:
        if task_retry_count >= self.max_retries:
            return RetryState.EXHAUSTED
        return RetryState.RETRY


class StepRetryState(BaseModel):
    step_id: str
    run_id: str
    attempt: int = 0
    max_retries: int = 3
    last_error: str = ""
    last_error_type: str = ""
    next_retry_at: str | None = None
    retry_history: list[dict] = Field(default_factory=list)

    def record_attempt(self, error: str, error_type: str) -> None:
        self.attempt += 1
        self.last_error = error
        self.last_error_type = error_type
        self.retry_history.append({
            "attempt": self.attempt,
            "error": error,
            "error_type": error_type,
        })

    def reset(self) -> None:
        self.attempt = 0
        self.last_error = ""
        self.last_error_type = ""
        self.next_retry_at = None
        self.retry_history.clear()
