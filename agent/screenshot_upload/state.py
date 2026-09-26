"""Validated durable queue-state value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Mapping
from uuid import UUID

from .jsonio import dumps_compact, loads_strict


MAX_STATE_BYTES = 256 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class StateError(ValueError):
    pass


class QueueStatus(str, Enum):
    PENDING = "PENDING"
    IN_FLIGHT = "IN_FLIGHT"
    RETRY_WAIT = "RETRY_WAIT"
    ACKED = "ACKED"
    UPLOADED = "UPLOADED"
    FAILED = "FAILED"


def _canonical_uuid(value: Any, field: str) -> str:
    if type(value) is not str:
        raise StateError(f"{field} must be a UUID string")
    try:
        parsed = UUID(value)
    except ValueError as exc:
        raise StateError(f"{field} must be a UUID") from exc
    if str(parsed) != value:
        raise StateError(f"{field} must use canonical UUID text")
    return value


def _parse_utc(value: Any, field: str) -> datetime | None:
    if value is None:
        return None
    if type(value) is not str:
        raise StateError(f"{field} must be a UTC timestamp or null")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise StateError(f"{field} is not ISO 8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise StateError(f"{field} must identify UTC")
    return parsed.astimezone(timezone.utc)


def _format_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise StateError("queue timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class LastError:
    code: str
    request_id: str | None = None
    status: int | None = None

    def __post_init__(self) -> None:
        if (
            type(self.code) is not str
            or not 1 <= len(self.code) <= 64
            or any(ord(character) < 0x21 or ord(character) > 0x7E for character in self.code)
        ):
            raise StateError("last_error code is invalid")
        if self.request_id is not None:
            _canonical_uuid(self.request_id, "last_error.request_id")
        if self.status is not None and (type(self.status) is not int or not 100 <= self.status <= 599):
            raise StateError("last_error status is invalid")

    def to_json(self) -> dict[str, Any]:
        return {"code": self.code, "request_id": self.request_id, "status": self.status}

    @classmethod
    def from_json(cls, value: Any) -> "LastError":
        if type(value) is not dict or set(value) != {"code", "request_id", "status"}:
            raise StateError("last_error schema is invalid")
        return cls(value["code"], value["request_id"], value["status"])


@dataclass(frozen=True)
class AckRecord:
    screenshot: Mapping[str, Any]
    status: int
    location: str
    idempotency_replayed: bool
    x_request_id: str
    received_at: datetime

    def __post_init__(self) -> None:
        if type(self.screenshot) is not dict:
            object.__setattr__(self, "screenshot", dict(self.screenshot))
        if self.status not in (200, 201) or type(self.status) is not int:
            raise StateError("ack status is invalid")
        if type(self.location) is not str or not self.location.startswith("/api/v1/projects/"):
            raise StateError("ack Location is invalid")
        if type(self.idempotency_replayed) is not bool:
            raise StateError("ack replay flag is invalid")
        _canonical_uuid(self.x_request_id, "ack.x_request_id")
        _format_utc(self.received_at)

    def to_json(self) -> dict[str, Any]:
        return {
            "screenshot": dict(self.screenshot),
            "status": self.status,
            "location": self.location,
            "idempotency_replayed": self.idempotency_replayed,
            "x_request_id": self.x_request_id,
            "received_at": _format_utc(self.received_at),
        }

    @classmethod
    def from_json(cls, value: Any) -> "AckRecord":
        expected = {
            "screenshot", "status", "location", "idempotency_replayed", "x_request_id", "received_at"
        }
        if type(value) is not dict or set(value) != expected or type(value["screenshot"]) is not dict:
            raise StateError("ack schema is invalid")
        received = _parse_utc(value["received_at"], "ack.received_at")
        assert received is not None
        return cls(
            screenshot=value["screenshot"],
            status=value["status"],
            location=value["location"],
            idempotency_replayed=value["idempotency_replayed"],
            x_request_id=value["x_request_id"],
            received_at=received,
        )


@dataclass(frozen=True)
class QueueState:
    queue_state_version: int
    client_upload_id: str
    manifest_sha256: str
    state: QueueStatus
    state_revision: int
    attempt_count: int
    retry_epoch: int
    epoch_attempt_count: int
    last_attempt_at: datetime | None
    next_attempt_at: datetime | None
    last_error: LastError | None
    ack: AckRecord | None

    def __post_init__(self) -> None:
        if type(self.queue_state_version) is not int or self.queue_state_version != 1:
            raise StateError("unsupported queue state version")
        _canonical_uuid(self.client_upload_id, "client_upload_id")
        if type(self.manifest_sha256) is not str or not _SHA256.fullmatch(self.manifest_sha256):
            raise StateError("manifest digest is invalid")
        if type(self.state) is not QueueStatus:
            try:
                object.__setattr__(self, "state", QueueStatus(self.state))
            except ValueError as exc:
                raise StateError("queue state is invalid") from exc
        for field in ("state_revision", "attempt_count", "retry_epoch", "epoch_attempt_count"):
            value = getattr(self, field)
            minimum = 1 if field == "state_revision" else 0
            if type(value) is not int or value < minimum:
                raise StateError(f"{field} is invalid")
        _format_utc(self.last_attempt_at)
        _format_utc(self.next_attempt_at)
        if self.epoch_attempt_count > self.attempt_count:
            raise StateError("epoch attempt count exceeds lifetime count")
        if self.attempt_count == 0 and self.last_attempt_at is not None:
            raise StateError("an unattempted item cannot have last_attempt_at")
        if self.attempt_count > 0 and self.last_attempt_at is None:
            raise StateError("an attempted item requires last_attempt_at")
        if self.state in (QueueStatus.IN_FLIGHT, QueueStatus.RETRY_WAIT):
            if self.last_attempt_at is None or self.next_attempt_at is None or self.ack is not None:
                raise StateError("active retry state has invalid timestamps or ack")
        elif self.state in (QueueStatus.ACKED, QueueStatus.UPLOADED):
            if self.ack is None or self.next_attempt_at is not None or self.last_error is not None:
                raise StateError("acknowledged state is invalid")
        elif self.state is QueueStatus.FAILED:
            if self.last_error is None or self.next_attempt_at is not None or self.ack is not None:
                raise StateError("FAILED state is invalid")
        elif self.state is QueueStatus.PENDING:
            if self.next_attempt_at is not None or self.ack is not None:
                raise StateError("PENDING state is invalid")

    @classmethod
    def initial(cls, client_upload_id: str, manifest_sha256: str) -> "QueueState":
        return cls(1, client_upload_id, manifest_sha256, QueueStatus.PENDING, 1, 0, 0, 0, None, None, None, None)

    def to_json(self) -> dict[str, Any]:
        return {
            "queue_state_version": 1,
            "client_upload_id": self.client_upload_id,
            "manifest_sha256": self.manifest_sha256,
            "state": self.state.value,
            "state_revision": self.state_revision,
            "attempt_count": self.attempt_count,
            "retry_epoch": self.retry_epoch,
            "epoch_attempt_count": self.epoch_attempt_count,
            "last_attempt_at": _format_utc(self.last_attempt_at),
            "next_attempt_at": _format_utc(self.next_attempt_at),
            "last_error": None if self.last_error is None else self.last_error.to_json(),
            "ack": None if self.ack is None else self.ack.to_json(),
        }

    def to_bytes(self) -> bytes:
        data = dumps_compact(self.to_json())
        if len(data) > MAX_STATE_BYTES:
            raise StateError("state exceeds 256 KiB")
        return data

    @classmethod
    def from_bytes(cls, raw: bytes) -> "QueueState":
        value = loads_strict(raw, max_bytes=MAX_STATE_BYTES)
        expected = {
            "queue_state_version", "client_upload_id", "manifest_sha256", "state", "state_revision",
            "attempt_count", "retry_epoch", "epoch_attempt_count", "last_attempt_at", "next_attempt_at",
            "last_error", "ack",
        }
        if type(value) is not dict or set(value) != expected:
            raise StateError("state schema is invalid")
        try:
            status = QueueStatus(value["state"])
        except (ValueError, TypeError) as exc:
            raise StateError("queue state is invalid") from exc
        return cls(
            queue_state_version=value["queue_state_version"],
            client_upload_id=value["client_upload_id"],
            manifest_sha256=value["manifest_sha256"],
            state=status,
            state_revision=value["state_revision"],
            attempt_count=value["attempt_count"],
            retry_epoch=value["retry_epoch"],
            epoch_attempt_count=value["epoch_attempt_count"],
            last_attempt_at=_parse_utc(value["last_attempt_at"], "last_attempt_at"),
            next_attempt_at=_parse_utc(value["next_attempt_at"], "next_attempt_at"),
            last_error=None if value["last_error"] is None else LastError.from_json(value["last_error"]),
            ack=None if value["ack"] is None else AckRecord.from_json(value["ack"]),
        )
