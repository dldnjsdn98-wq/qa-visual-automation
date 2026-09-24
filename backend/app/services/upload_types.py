from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Protocol
from uuid import UUID


class ReservationState(str, Enum):
    OWNED = "OWNED"
    REPLAY = "REPLAY"
    CONFLICT = "CONFLICT"
    IN_PROGRESS = "IN_PROGRESS"


@dataclass(frozen=True)
class AttemptFence:
    project_id: UUID
    client_upload_id: UUID
    request_fingerprint: str
    attempt_generation: int
    attempt_token: UUID
    candidate_screenshot_id: UUID
    candidate_storage_key: str
    lease_expires_at: datetime


@dataclass(frozen=True)
class ReservationOutcome:
    state: ReservationState
    fence: AttemptFence | None = None
    screenshot: dict[str, Any] | None = None
    retry_after: int | None = None


@dataclass(frozen=True)
class UploadOutcome:
    screenshot: dict[str, Any]
    status_code: int
    replayed: bool | None


class UploadFaultInjector(Protocol):
    def hit(self, point: str, context: dict[str, Any] | None = None) -> None: ...


class NoopUploadFaultInjector:
    def hit(self, point: str, context: dict[str, Any] | None = None) -> None:
        return None


NOOP_UPLOAD_FAULTS = NoopUploadFaultInjector()
