"""Single-process durable upload worker orchestration."""

from __future__ import annotations

from dataclasses import is_dataclass, replace
from datetime import datetime, timezone
import random
import time
from typing import Any, Callable, Iterable, Protocol
from uuid import UUID

from .ack import AckMismatch, ValidatedAck, to_state_ack, validate_ack
from .client import HttpResult, UploadClient, UploadTransportError, safe_error_code
from .faults import FaultInjector, NO_FAULTS
from .retry import MAX_ATTEMPTS_PER_EPOCH, RetryDisposition, classify_response, plan_retry
from .recovery import LocalIntentChanged


class BindingGuardProtocol(Protocol):
    def check(self) -> None: ...


class StateStoreProtocol(Protocol):
    def load(self, item: object) -> object | None: ...
    def initialize(self, item: object) -> object: ...
    def transition(self, item: object, previous: object, updated: object) -> object: ...


class SpoolProtocol(Protocol):
    def move(self, item: object, destination: str) -> object: ...


class WorkerHalted(RuntimeError):
    pass


def _state_name(state: object) -> str:
    value = getattr(state, "state")
    return getattr(value, "value", value)


def _state_value(state: object, name: str) -> object:
    current = getattr(state, "state")
    enum_type = type(current)
    if isinstance(current, str):
        try:
            return enum_type(name)
        except TypeError:
            return name
    try:
        return enum_type[name]
    except (KeyError, TypeError):
        return enum_type(name)


def _updated(current: object, **changes: Any) -> object:
    changes.setdefault("state_revision", getattr(current, "state_revision") + 1)
    if is_dataclass(current):
        return replace(current, **changes)
    model_copy = getattr(current, "model_copy", None)
    if callable(model_copy):
        return model_copy(update=changes)
    values = dict(vars(current))
    values.update(changes)
    return type(current)(**values)


def _safe_request_id(result: HttpResult | None) -> str | None:
    if result is None:
        return None
    values = [value for key, value in result.headers.items() if key.lower() == "x-request-id"]
    if len(values) != 1:
        return None
    try:
        return str(UUID(values[0])) if values[0] == str(UUID(values[0])) else None
    except (ValueError, AttributeError):
        return None


class UploadWorker:
    """Run one queue item through recovery and a bounded retry epoch.

    Work-unit A owns concrete ReadyItem, QueueState, LastError, StateStore, and
    Spool classes.  This class deliberately depends only on their reviewed public
    fields and load/initialize/transition/move methods.
    """

    def __init__(
        self,
        *,
        guard: BindingGuardProtocol,
        state_store: StateStoreProtocol,
        spool: SpoolProtocol,
        client: UploadClient,
        validate_intent: Callable[[object], None],
        validate_persisted_ack: Callable[[object, object], None],
        ack_factory: Callable[..., object] | None = None,
        error_factory: Callable[..., object] | None = None,
        wall_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        uniform: Callable[[float, float], float] = random.uniform,
        faults: FaultInjector = NO_FAULTS,
    ) -> None:
        self.guard = guard
        self.state_store = state_store
        self.spool = spool
        self.client = client
        self.validate_intent = validate_intent
        self.validate_persisted_ack = validate_persisted_ack
        self.ack_factory = ack_factory
        self.error_factory = error_factory
        self.wall_clock = wall_clock
        self.monotonic = monotonic
        self.sleep = sleep
        self.uniform = uniform
        self.faults = faults

    def _error(self, code: str, result: HttpResult | None = None) -> object:
        factory = self.error_factory
        if factory is None:
            try:
                from .state import LastError as factory  # type: ignore[assignment]
            except ImportError as exc:
                raise RuntimeError("work-unit A state.LastError is unavailable") from exc
        return factory(
            code=code[:64],
            request_id=_safe_request_id(result),
            status=result.status_code if result is not None else None,
        )

    def _transition(self, item: object, current: object, **changes: Any) -> object:
        self.guard.check()
        updated = _updated(current, **changes)
        return self.state_store.transition(item, current, updated)

    def _move(self, item: object, destination: str) -> object:
        self.guard.check()
        return self.spool.move(item, destination)

    def _wait_until(self, deadline: datetime) -> None:
        deadline = deadline.astimezone(timezone.utc)
        while True:
            now = self.wall_clock().astimezone(timezone.utc)
            remaining = (deadline - now).total_seconds()
            if remaining <= 0:
                return
            before = self.monotonic()
            self.sleep(min(remaining, 1.0))
            after = self.monotonic()
            if after < before:
                raise WorkerHalted("monotonic clock moved backward")

    def run(self, items: Iterable[tuple[object, str]]) -> list[object]:
        """Process a discovery snapshot; discovery must occur under the same guard."""

        self.guard.check()
        return [self.run_item(item, location=location) for item, location in items]

    def run_item(self, item: object, *, location: str = "pending") -> object:
        state = self.state_store.load(item)
        if state is None:
            if location != "pending":
                raise WorkerHalted("state cannot be initialized outside pending")
            self.validate_intent(item)
            self.guard.check()
            state = self.state_store.initialize(item)
            self.faults.hit("worker.initialized.durable")

        location, item, state = self._recover(item, location, state)
        if location != "pending" or _state_name(state) in ("FAILED", "ACKED", "UPLOADED"):
            return state

        while _state_name(state) in ("PENDING", "RETRY_WAIT", "IN_FLIGHT"):
            deadline = getattr(state, "next_attempt_at")
            if deadline is not None:
                self._wait_until(deadline)
            state, completed = self._attempt(item, state)
            if completed:
                return state
        return state

    def _recover(self, item: object, location: str, state: object) -> tuple[str, object, object]:
        # Endpoint continuity is checked before interpreting any persisted ACK
        # or performing a recovery transition.
        self.guard.check()
        name = _state_name(state)
        if location == "pending" and name == "ACKED":
            self.validate_persisted_ack(item, getattr(state, "ack"))
            item = self._move(item, "uploaded")
            self.faults.hit("worker.recovery.uploaded.moved")
            state = self._transition(item, state, state=_state_value(state, "UPLOADED"))
            return "uploaded", item, state
        if location == "uploaded" and name == "ACKED":
            self.validate_persisted_ack(item, getattr(state, "ack"))
            state = self._transition(item, state, state=_state_value(state, "UPLOADED"))
            return location, item, state
        if location == "uploaded" and name == "UPLOADED":
            self.validate_persisted_ack(item, getattr(state, "ack"))
            return location, item, state
        if location == "pending" and name == "FAILED":
            item = self._move(item, "failed")
            self.faults.hit("worker.recovery.failed.moved")
            return "failed", item, state
        if location == "failed" and name == "PENDING":
            if getattr(state, "retry_epoch") <= 0:
                raise WorkerHalted("failed/PENDING without an explicit retry epoch")
            self.validate_intent(item)
            item = self._move(item, "pending")
            self.faults.hit("worker.recovery.requeued.moved")
            return "pending", item, state
        if location == "pending" and name == "IN_FLIGHT":
            if getattr(state, "epoch_attempt_count") >= MAX_ATTEMPTS_PER_EPOCH:
                state = self._fail(item, state, "RETRY_EXHAUSTED", None)
                return "failed", item, state
            state = self._transition(item, state, state=_state_value(state, "RETRY_WAIT"))
            self.faults.hit("worker.recovery.retry_wait.durable")
        return location, item, state

    def _attempt(self, item: object, state: object) -> tuple[object, bool]:
        self.guard.check()
        try:
            self.validate_intent(item)
        except LocalIntentChanged:
            return self._fail(item, state, "LOCAL_INTENT_CHANGED", None), True
        attempt = getattr(state, "epoch_attempt_count") + 1
        if attempt > MAX_ATTEMPTS_PER_EPOCH:
            return self._fail(item, state, "RETRY_EXHAUSTED", None), True
        now = self.wall_clock().astimezone(timezone.utc)
        fallback = plan_retry(attempt, now, self.uniform)
        state = self._transition(
            item,
            state,
            state=_state_value(state, "IN_FLIGHT"),
            attempt_count=getattr(state, "attempt_count") + 1,
            epoch_attempt_count=attempt,
            last_attempt_at=now,
            next_attempt_at=fallback.next_attempt_at,
            last_error=None,
            ack=None,
        )
        self.faults.hit("worker.in_flight.durable")
        self.guard.check()
        self.faults.hit("worker.before_http")
        try:
            result = self.client.send(item)
        except UploadTransportError:
            result = None
        self.faults.hit("worker.response_received")

        # Endpoint continuity always wins over response/ack interpretation.
        self.guard.check()
        if result is None:
            return self._retry_or_fail(item, state, "TRANSPORT_ERROR", None, None)

        disposition = classify_response(result.status_code, safe_error_code(result))
        if disposition is RetryDisposition.SUCCESS:
            try:
                validated = validate_ack(result, item)
            except AckMismatch:
                return self._retry_or_fail(item, state, "PROTOCOL_ACK_MISMATCH", result, None)
            self.faults.hit("worker.ack_validated")
            return self._acknowledge(item, state, validated), True
        if disposition is RetryDisposition.RETRY:
            retry_after = next(
                (value for key, value in result.headers.items() if key.lower() == "retry-after"),
                None,
            )
            return self._retry_or_fail(item, state, safe_error_code(result) or "HTTP_RETRYABLE", result, retry_after)
        code = "ENDPOINT_REDIRECT" if 300 <= result.status_code <= 399 else safe_error_code(result) or "HTTP_TERMINAL"
        return self._fail(item, state, code, result), True

    def _retry_or_fail(
        self,
        item: object,
        state: object,
        code: str,
        result: HttpResult | None,
        retry_after: str | None,
    ) -> tuple[object, bool]:
        attempt = getattr(state, "epoch_attempt_count")
        if attempt >= MAX_ATTEMPTS_PER_EPOCH:
            return self._fail(item, state, "RETRY_EXHAUSTED", result), True
        received_at = result.received_at if result is not None else self.wall_clock().astimezone(timezone.utc)
        plan = plan_retry(attempt, received_at, self.uniform, retry_after)
        diagnostic = plan.diagnostic_code or code
        state = self._transition(
            item,
            state,
            state=_state_value(state, "RETRY_WAIT"),
            next_attempt_at=plan.next_attempt_at,
            last_error=self._error(diagnostic, result),
        )
        self.faults.hit("worker.retry_wait.durable")
        return state, False

    def _fail(self, item: object, state: object, code: str, result: HttpResult | None) -> object:
        state = self._transition(
            item,
            state,
            state=_state_value(state, "FAILED"),
            next_attempt_at=None,
            last_error=self._error(code, result),
            ack=None,
        )
        self.faults.hit("worker.failed.durable")
        self._move(item, "failed")
        self.faults.hit("worker.failed.moved")
        return state

    def _acknowledge(self, item: object, state: object, validated: ValidatedAck) -> object:
        ack = to_state_ack(validated, self.ack_factory)
        state = self._transition(
            item,
            state,
            state=_state_value(state, "ACKED"),
            next_attempt_at=None,
            last_error=None,
            ack=ack,
        )
        self.faults.hit("worker.acked.durable")
        moved = self._move(item, "uploaded")
        self.faults.hit("worker.uploaded.moved")
        state = self._transition(moved, state, state=_state_value(state, "UPLOADED"))
        self.faults.hit("worker.uploaded.durable")
        return state
