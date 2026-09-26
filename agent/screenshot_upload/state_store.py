"""Crash-safe state.json and initialized.json persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .durable_fs import ensure_regular_file, publish_file_no_replace, replace_file, write_temp
from .marker import MarkerError, initialized_bytes, load_initialized_marker
from .jsonio import StrictJSONError
from .state import QueueState, StateError
from .state import QueueStatus


class StateStoreError(RuntimeError):
    pass


class StateStore:
    def __init__(self, guard: Callable[[], object]):
        self._guard = guard

    @staticmethod
    def _paths(item: object) -> tuple[Path, Path]:
        directory = Path(getattr(item, "item_dir"))
        return directory / "state.json", directory / "initialized.json"

    @staticmethod
    def _check_identity(item: object, state: QueueState) -> None:
        if state.client_upload_id != getattr(item, "client_upload_id"):
            raise StateStoreError("state client identity does not match manifest")
        if state.manifest_sha256 != getattr(item, "manifest_sha256"):
            raise StateStoreError("state manifest digest does not match manifest")

    def load(self, item: object) -> QueueState | None:
        state_path, marker_path = self._paths(item)
        state_stat = ensure_regular_file(state_path, allow_missing=True)
        marker_stat = ensure_regular_file(marker_path, allow_missing=True)
        if state_stat is None:
            if marker_stat is not None:
                raise StateStoreError("initialized marker exists without durable state")
            return None
        try:
            raw = state_path.read_bytes()
            if len(raw) != state_stat.st_size:
                raise StateStoreError("state changed while being read")
            state = QueueState.from_bytes(raw)
        except (OSError, StateError, StrictJSONError) as exc:
            raise StateStoreError("durable state is corrupt") from exc
        self._check_identity(item, state)
        if marker_stat is None:
            self._write_initialized(item)
        else:
            try:
                marker = load_initialized_marker(marker_path)
            except (OSError, MarkerError) as exc:
                raise StateStoreError("initialized marker is corrupt") from exc
            if marker.client_upload_id != state.client_upload_id or marker.manifest_sha256 != state.manifest_sha256:
                raise StateStoreError("initialized marker identity does not match state")
        return state

    def _write_initialized(self, item: object) -> None:
        _, marker_path = self._paths(item)
        temp = marker_path.with_name("initialized.json.tmp")
        data = initialized_bytes(getattr(item, "client_upload_id"), getattr(item, "manifest_sha256"))
        write_temp(temp, data, guard=self._guard)
        try:
            publish_file_no_replace(temp, marker_path, guard=self._guard)
        except FileExistsError:
            marker = load_initialized_marker(marker_path)
            if marker.client_upload_id != getattr(item, "client_upload_id") or marker.manifest_sha256 != getattr(item, "manifest_sha256"):
                raise StateStoreError("concurrent initialized marker mismatch")

    def initialize(self, item: object) -> QueueState:
        state_path, marker_path = self._paths(item)
        if ensure_regular_file(marker_path, allow_missing=True) is not None:
            raise StateStoreError("initialized marker exists before initialization")
        if ensure_regular_file(state_path, allow_missing=True) is not None:
            state = self.load(item)
            assert state is not None
            return state
        state = QueueState.initial(getattr(item, "client_upload_id"), getattr(item, "manifest_sha256"))
        temp = state_path.with_name("state.json.tmp")
        write_temp(temp, state.to_bytes(), guard=self._guard)
        publish_file_no_replace(temp, state_path, guard=self._guard)
        self._write_initialized(item)
        return state

    def transition(self, item: object, previous: QueueState, updated: QueueState) -> QueueState:
        self._check_identity(item, previous)
        self._check_identity(item, updated)
        current = self.load(item)
        if current != previous:
            raise StateStoreError("state transition does not start from the durable revision")
        if updated.state_revision != previous.state_revision + 1:
            raise StateStoreError("state revision must increase by one")
        allowed = {
            QueueStatus.PENDING: {QueueStatus.IN_FLIGHT, QueueStatus.FAILED},
            QueueStatus.IN_FLIGHT: {QueueStatus.RETRY_WAIT, QueueStatus.ACKED, QueueStatus.FAILED},
            QueueStatus.RETRY_WAIT: {QueueStatus.IN_FLIGHT, QueueStatus.FAILED},
            QueueStatus.ACKED: {QueueStatus.UPLOADED},
            QueueStatus.UPLOADED: set(),
            QueueStatus.FAILED: {QueueStatus.PENDING},
        }
        if updated.state not in allowed[previous.state]:
            raise StateStoreError(f"invalid queue transition {previous.state.value}->{updated.state.value}")
        if updated.attempt_count < previous.attempt_count or updated.retry_epoch < previous.retry_epoch:
            raise StateStoreError("queue counters cannot decrease")
        if updated.retry_epoch == previous.retry_epoch and updated.epoch_attempt_count < previous.epoch_attempt_count:
            raise StateStoreError("epoch attempt count cannot decrease within an epoch")
        if updated.state is QueueStatus.IN_FLIGHT:
            if updated.attempt_count != previous.attempt_count + 1 or updated.epoch_attempt_count != previous.epoch_attempt_count + 1:
                raise StateStoreError("IN_FLIGHT must consume exactly one attempt")
        elif previous.state is QueueStatus.FAILED and updated.state is QueueStatus.PENDING:
            if (
                updated.retry_epoch != previous.retry_epoch + 1
                or updated.epoch_attempt_count != 0
                or updated.attempt_count != previous.attempt_count
            ):
                raise StateStoreError("explicit retry epoch counters are invalid")
        elif (
            updated.attempt_count != previous.attempt_count
            or updated.retry_epoch != previous.retry_epoch
            or updated.epoch_attempt_count != previous.epoch_attempt_count
        ):
            raise StateStoreError("non-attempt transition changed queue counters")
        state_path, _ = self._paths(item)
        temp = state_path.with_name("state.json.tmp")
        write_temp(temp, updated.to_bytes(), guard=self._guard)
        replace_file(temp, state_path, guard=self._guard)
        return updated
