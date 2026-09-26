"""Private Backend runner contracts; never expose fences in public API responses."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Mapping
from uuid import UUID

from sqlalchemy.orm import Session


class LostFence(RuntimeError):
    """The caller must stop its child and discard its local output."""


class OutcomeUnknown(RuntimeError):
    """Primary could not resolve an operation; do not publish or persist failure."""


class JobInvariantError(RuntimeError):
    """Fail closed on a broken durable state; never repair from live catalog."""


class AdapterOutputInvalid(JobInvariantError):
    """The complete child result failed the Backend's closed validation."""


@dataclass(frozen=True)
class JobFence:
    project_id: UUID
    run_id: UUID
    generation: int
    attempt_token: UUID
    claim_request_id: UUID


@dataclass(frozen=True)
class Claim:
    fence: JobFence
    attempt_count: int
    lease_expires_at: datetime
    correlation_id: UUID


@dataclass(frozen=True)
class FinalizedResults:
    ocr_result_id: UUID
    verification_result_id: UUID
    verification_status: str
    snapshot_sha256: str
    configuration_sha256: str
    profile_digest: str


# Mandatory integration boundary, implemented by the parent persistence owner.
# Validate the COMPLETE closed/bounded adapter schema and immutable input hashes,
# then insert ALL summaries/regions/items using this Session WITHOUT commit,
# rollback, opening another connection or modifying run/job/attempt rows.
# Raise on invalid output: the enclosing transaction rolls every insert back.
ResultWriter = Callable[[Session, Mapping[str, Any], Any], FinalizedResults]
