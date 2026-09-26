"""Explicit unchanged-intent retry for retained failed queue items."""

from __future__ import annotations

from dataclasses import is_dataclass, replace
from typing import Any, Callable, Protocol

from .faults import FaultInjector, NO_FAULTS


class BindingGuardProtocol(Protocol):
    def check(self) -> None: ...


class StateStoreProtocol(Protocol):
    def load(self, item: object) -> object: ...
    def transition(self, item: object, previous: object, updated: object) -> object: ...


class SpoolProtocol(Protocol):
    def move(self, item: object, destination: str) -> object: ...


class RequeueError(RuntimeError):
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


def requeue_failed(
    item: object,
    *,
    guard: BindingGuardProtocol,
    state_store: StateStoreProtocol,
    spool: SpoolProtocol,
    validate_intent: Callable[[object], None],
    faults: FaultInjector = NO_FAULTS,
) -> object:
    """Persist failed->PENDING before the no-overwrite failed->pending move."""

    state = state_store.load(item)
    if _state_name(state) != "FAILED":
        raise RequeueError("only FAILED items can be explicitly requeued")
    validate_intent(item)
    guard.check()
    pending = _updated(
        state,
        state=_state_value(state, "PENDING"),
        retry_epoch=getattr(state, "retry_epoch") + 1,
        epoch_attempt_count=0,
        next_attempt_at=None,
        ack=None,
    )
    pending = state_store.transition(item, state, pending)
    faults.hit("requeue.pending.durable")
    guard.check()
    moved = spool.move(item, "pending")
    faults.hit("requeue.moved")
    return moved


def recover_requeue(
    item: object,
    *,
    guard: BindingGuardProtocol,
    state_store: StateStoreProtocol,
    spool: SpoolProtocol,
) -> object:
    state = state_store.load(item)
    if _state_name(state) != "PENDING" or getattr(state, "retry_epoch") <= 0:
        raise RequeueError("failed/PENDING recovery requires an explicit retry epoch")
    guard.check()
    return spool.move(item, "pending")
