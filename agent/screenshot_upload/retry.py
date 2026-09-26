"""Deterministic retry classification and deadline calculation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from enum import Enum
import math
from typing import Callable, Mapping


MAX_ATTEMPTS_PER_EPOCH = 8


class RetryDisposition(str, Enum):
    SUCCESS = "SUCCESS"
    RETRY = "RETRY"
    TERMINAL = "TERMINAL"


@dataclass(frozen=True)
class RetryPlan:
    next_attempt_at: datetime
    delay_seconds: float
    local_delay_seconds: float
    retry_after_valid: bool
    diagnostic_code: str | None = None


def base_delay(attempt_number: int) -> float:
    if type(attempt_number) is not int or not 1 <= attempt_number <= MAX_ATTEMPTS_PER_EPOCH:
        raise ValueError("attempt number must be in 1..8")
    return float(min(300, 2 ** (attempt_number - 1)))


def equal_jitter(attempt_number: int, uniform: Callable[[float, float], float]) -> float:
    ceiling = base_delay(attempt_number)
    selected = float(uniform(ceiling / 2.0, ceiling))
    if not math.isfinite(selected) or not ceiling / 2.0 <= selected <= ceiling:
        raise ValueError("RNG returned a value outside the equal-jitter interval")
    return selected


def parse_retry_after(value: str | None, received_at: datetime) -> datetime | None:
    """Return the server's minimum UTC deadline or None for invalid input."""

    if value is None or type(value) is not str or not value or value != value.strip():
        return None
    if received_at.tzinfo is None:
        raise ValueError("received_at must be timezone-aware")
    received_utc = received_at.astimezone(timezone.utc)
    if value.isascii() and value.isdecimal():
        try:
            seconds = int(value)
            deadline = received_utc + timedelta(seconds=seconds)
        except (OverflowError, ValueError):
            return None
        return deadline
    try:
        parsed = parsedate_to_datetime(value)
        if parsed is None or parsed.tzinfo is None:
            return None
        deadline = parsed.astimezone(timezone.utc)
        deadline.timestamp()
    except (OverflowError, OSError, TypeError, ValueError):
        return None
    return max(received_utc, deadline)


def plan_retry(
    attempt_number: int,
    received_at: datetime,
    uniform: Callable[[float, float], float],
    retry_after: str | None = None,
) -> RetryPlan:
    local_delay = equal_jitter(attempt_number, uniform)
    local_deadline = received_at.astimezone(timezone.utc) + timedelta(seconds=local_delay)
    server_deadline = parse_retry_after(retry_after, received_at)
    selected = max(local_deadline, server_deadline) if server_deadline is not None else local_deadline
    return RetryPlan(
        next_attempt_at=selected,
        delay_seconds=max(0.0, (selected - received_at.astimezone(timezone.utc)).total_seconds()),
        local_delay_seconds=local_delay,
        retry_after_valid=server_deadline is not None,
        diagnostic_code=None if retry_after is None or server_deadline is not None else "INVALID_RETRY_AFTER",
    )


def classify_response(status_code: int, error_code: str | None = None) -> RetryDisposition:
    if status_code in (200, 201):
        return RetryDisposition.SUCCESS
    if status_code in (408, 429) or 500 <= status_code <= 599:
        return RetryDisposition.RETRY
    if status_code == 409 and error_code == "UPLOAD_IN_PROGRESS":
        return RetryDisposition.RETRY
    return RetryDisposition.TERMINAL


def first_header(headers: Mapping[str, str], name: str) -> str | None:
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return None
