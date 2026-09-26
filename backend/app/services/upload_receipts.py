"""Durable receipt transactions; callers own staging/publication, never deletion.

``factory`` must open fresh Sessions against the authoritative primary. ``commit``
is an injectable transaction boundary (not a global Session monkeypatch). A
transport error raised there is always uncertain, even after COMMIT succeeded.
"""
from dataclasses import dataclass
from datetime import timedelta
from hashlib import sha256
import json
from math import ceil
import re
from uuid import UUID, uuid4

import rfc8785
from sqlalchemy.exc import SQLAlchemyError

from backend.app.errors import DomainError
from backend.app.repositories import upload_receipts as repo
from backend.app.repositories.catalog import project
from backend.app.services.catalog import validate_references
from backend.app.services.upload_types import (
    AttemptFence, ReservationOutcome, ReservationState, UploadOutcome,
    NOOP_UPLOAD_FAULTS,
)

RENEW_INTERVAL_SECONDS = repo.RENEW_INTERVAL_SECONDS


@dataclass(frozen=True)
class UploadIntent:
    project_id: UUID
    client_upload_id: UUID
    canonical_request: bytes
    request_fingerprint: str

    def payload(self):
        # The strict wire parser runs upstream. Here protect the immutable
        # service boundary and reject corruption before looking up a receipt.
        if (not isinstance(self.canonical_request, bytes)
                or not 1 <= len(self.canonical_request) <= 65536
                or sha256(self.canonical_request).hexdigest() != self.request_fingerprint):
            raise ValueError("Invalid canonical request digest")
        payload = json.loads(self.canonical_request)
        required = {"fingerprint_version", "upload_protocol_version", "project_id",
                    "build_id", "locale_id", "category_id", "situation_id", "source",
                    "original_filename", "metadata_version", "metadata", "file_hash",
                    "media_type", "size_bytes", "width", "height"}
        if (not isinstance(payload, dict) or set(payload) != required
                or rfc8785.dumps(payload) != self.canonical_request
                or payload["project_id"] != str(self.project_id)
                or self.client_upload_id.version != 4
                or payload["source"] not in ("agent", "automation")
                or payload["media_type"] not in ("image/png", "image/jpeg")
                or any(type(payload[k]) is not int or payload[k] != 1 for k in
                       ("fingerprint_version", "upload_protocol_version", "metadata_version"))):
            raise ValueError("Invalid canonical upload intent")
        return payload


def _unavailable():
    error = DomainError(503, "DATABASE_UNAVAILABLE", "Database unavailable or upload outcome uncertain")
    error.retry_after = 5
    return error


def _commit(session, phase):
    session.commit()


def _fence(row):
    return AttemptFence(row.project_id, row.client_upload_id, row.request_fingerprint,
                        row.attempt_generation, row.attempt_token,
                        row.candidate_screenshot_id, row.candidate_storage_key,
                        row.lease_expires_at)


def _new_fence(intent, payload, generation, now):
    candidate = uuid4()
    extension = "png" if payload["media_type"] == "image/png" else "jpg"
    return AttemptFence(intent.project_id, intent.client_upload_id, intent.request_fingerprint,
                        generation, uuid4(), candidate,
                        f"objects/{intent.project_id}/{candidate}.{extension}",
                        now + timedelta(seconds=repo.LEASE_SECONDS))


def _verify_row(row):
    if (not 1 <= len(row.canonical_request) <= 65536
            or sha256(bytes(row.canonical_request)).hexdigest() != row.request_fingerprint):
        raise _unavailable()


def _serialize(row):
    # Keep this module independent of screenshots.py (its orchestrator imports us).
    result = {c.key: getattr(row, c.key) for c in row.__mapper__.column_attrs
              if c.key != "storage_key"}
    result["metadata"] = result.pop("capture_metadata")
    result["content_url"] = f"/api/v1/projects/{row.project_id}/screenshots/{row.id}/content"
    return result


def _screenshot(session, row):
    screenshot = repo.load_completed_screenshot(session, row)
    payload = json.loads(bytes(row.canonical_request))
    actual = {key: getattr(screenshot, key) for key in
              ("source", "original_filename", "metadata_version", "file_hash", "media_type",
               "size_bytes", "width", "height")}
    actual.update({key: str(getattr(screenshot, key)) for key in
                   ("project_id", "build_id", "locale_id", "category_id", "situation_id")})
    actual.update(metadata=screenshot.capture_metadata, fingerprint_version=1, upload_protocol_version=1)
    if rfc8785.dumps(actual) != bytes(row.canonical_request):
        raise _unavailable()
    return _serialize(screenshot)


def _existing(session, row, intent, now):
    _verify_row(row)
    if (row.request_fingerprint != intent.request_fingerprint
            or bytes(row.canonical_request) != intent.canonical_request):
        return ReservationOutcome(ReservationState.CONFLICT)
    if row.state == "COMPLETED":
        return ReservationOutcome(ReservationState.REPLAY, screenshot=_screenshot(session, row))
    return None


def _busy(row, now):
    delay = max(1, ceil((row.lease_expires_at - now).total_seconds())) if (
        row is not None and row.state == "PROCESSING") else 1
    return ReservationOutcome(ReservationState.IN_PROGRESS, retry_after=delay)


def _references(session, intent, payload, *, lock=False):
    validate_references(session, intent.project_id,
                        {k: UUID(payload[k]) for k in
                         ("build_id", "locale_id", "category_id", "situation_id")},
                        field_prefix="metadata", lock=lock)


def reserve_or_replay(factory, intent, *, faults=NOOP_UPLOAD_FAULTS, commit=_commit):
    payload = intent.payload()
    attempted = None
    first = False
    try:
        with factory() as session:
            repo.begin_primary(session)
            project(session, intent.project_id)
            row = repo.lock_receipt(session, intent.project_id, intent.client_upload_id)
            now = repo.sample_db_clock(session)
            if row is None:
                attempted = _new_fence(intent, payload, 1, now)
                first = True
                inserted = repo.insert_first_attempt(session, intent, attempted)
                row = repo.lock_receipt(session, intent.project_id, intent.client_upload_id)
                now = repo.sample_db_clock(session)
                if inserted:
                    # Validate after arbitration; an existing winner must be
                    # compared before current context validation.
                    _references(session, intent, payload)
                    repo.renew_locked(session, row, attempted, now)
                    attempted = _fence(row)
                else:
                    attempted = None
            if attempted is None:
                result = _existing(session, row, intent, now)
                if result:
                    return result
                if row.state == "PROCESSING" and row.lease_expires_at > now:
                    return _busy(row, now)
                _references(session, intent, payload)
                attempted = _new_fence(intent, payload, row.attempt_generation + 1, now)
                first = False
                repo.take_over_locked(session, row, now, attempted)
            faults.hit("RESERVE_BEFORE_COMMIT", {"fence": attempted})
            try:
                commit(session, "reserve")
                faults.hit("RESERVE_AFTER_COMMIT_BEFORE_PUBLISH", {"fence": attempted})
            except Exception:
                session.invalidate()
                return recover_reservation_commit(factory, intent, attempted, first_insert=first)
            return ReservationOutcome(ReservationState.OWNED, fence=attempted)
    except (SQLAlchemyError, RuntimeError, OverflowError):
        raise _unavailable() from None


def recover_reservation_commit(factory, intent, attempted_fence, *, first_insert=False):
    payload = intent.payload()
    try:
        with factory() as session:
            repo.begin_primary(session)
            if first_insert:
                # Never infer rollback from SELECT finding no visible row.
                inserted = repo.insert_first_attempt(session, intent, attempted_fence)
            else:
                inserted = False
            row = repo.lock_receipt(session, intent.project_id, intent.client_upload_id)
            now = repo.sample_db_clock(session)
            if row is None:
                raise _unavailable()
            result = _existing(session, row, intent, now)
            if result:
                return result
            if inserted:
                _references(session, intent, payload)
                # Arbitration can have taken time. This is an uncommitted new
                # reservation, so start its lease at the locked decision point.
                row.lease_expires_at = now + timedelta(seconds=repo.LEASE_SECONDS)
                row.updated_at = now
                session.flush()
            if not repo.owns(row, attempted_fence) or row.lease_expires_at <= now:
                return _busy(row, now)
            result = ReservationOutcome(ReservationState.OWNED, fence=_fence(row))
            try:
                session.commit()
            except Exception:
                session.invalidate()
                raise _unavailable() from None
            return result
    except (SQLAlchemyError, RuntimeError):
        raise _unavailable() from None


def renew_attempt(factory, fence, *, faults=NOOP_UPLOAD_FAULTS, commit=_commit):
    """Call at intervals <=20s. Any exception must stop publication/finalization."""
    try:
        with factory() as session:
            repo.begin_primary(session)
            row = repo.lock_receipt(session, fence.project_id, fence.client_upload_id)
            now = repo.sample_db_clock(session)
            if row is None:
                return False
            _verify_row(row)
            if not repo.renew_locked(session, row, fence, now):
                return False
            faults.hit("RENEW_BEFORE_COMMIT", {"fence": fence})
            try:
                commit(session, "renew")
            except Exception:
                session.invalidate()
                raise _unavailable() from None
            return True
    except (SQLAlchemyError, RuntimeError):
        raise _unavailable() from None


def _as_upload(result):
    if result.state == ReservationState.REPLAY:
        return UploadOutcome(result.screenshot, 200, True)
    code = "IDEMPOTENCY_CONFLICT" if result.state == ReservationState.CONFLICT else "UPLOAD_IN_PROGRESS"
    error = DomainError(409, code, "Upload identity conflicts" if code == "IDEMPOTENCY_CONFLICT" else "Upload in progress")
    error.retry_after = result.retry_after
    raise error


def finalize_attempt(factory, fence, intent, *, faults=NOOP_UPLOAD_FAULTS, commit=_commit):
    """Only call after exact candidate bytes have been published/verified."""
    payload = intent.payload()
    if (fence.project_id, fence.client_upload_id, fence.request_fingerprint) != (
            intent.project_id, intent.client_upload_id, intent.request_fingerprint):
        raise ValueError("Intent and fence differ")
    try:
        with factory() as session:
            repo.begin_primary(session)
            faults.hit("BEFORE_FINAL_LOCK", {"fence": fence})
            row = repo.lock_receipt(session, fence.project_id, fence.client_upload_id)
            now = repo.sample_db_clock(session)
            if row is None:
                raise _unavailable()
            result = _existing(session, row, intent, now)
            if result:
                return _as_upload(result)
            if not repo.owns(row, fence) or row.lease_expires_at <= now:
                return _as_upload(_busy(row, now))
            try:
                # Hold key-share locks through the Screenshot insert/receipt
                # completion so a validated parent cannot disappear mid-finalize.
                _references(session, intent, payload, lock=True)
                faults.hit("AFTER_FINAL_REFERENCES_BEFORE_SCREENSHOT_INSERT", {"fence": fence})
                values = {k: v for k, v in payload.items()
                          if k not in ("fingerprint_version", "upload_protocol_version", "metadata")}
                for key in ("project_id", "build_id", "locale_id", "category_id", "situation_id"):
                    values[key] = UUID(values[key])
                values.update(id=fence.candidate_screenshot_id, storage_key=fence.candidate_storage_key,
                              client_upload_id=fence.client_upload_id, capture_metadata=payload["metadata"])
                screenshot = repo.insert_screenshot(session, values)
                faults.hit("AFTER_SCREENSHOT_INSERT_BEFORE_RECEIPT_UPDATE", {"fence": fence})
                repo.complete_locked(session, row, fence, screenshot, now)
                result = UploadOutcome(_serialize(screenshot), 201, False)
                faults.hit("FINALIZE_BEFORE_COMMIT", {"fence": fence})
            except Exception as exc:
                # Only a successful rollback authorizes FAILED bookkeeping.
                try:
                    session.rollback()
                except Exception:
                    session.invalidate()
                    raise _unavailable() from None
                fail_after_known_rollback(factory, fence, getattr(exc, "code", "FINALIZE_FAILED"),
                                          rollback_confirmed=True)
                raise
            try:
                commit(session, "finalize")
            except Exception:
                session.invalidate()
                return recover_finalize_commit(factory, fence, intent)
            # A response-send loss must not enter rollback/FAILED handling.
            faults.hit("AFTER_FINALIZE_COMMIT_BEFORE_RESPONSE", {"fence": fence})
            return result
    except (SQLAlchemyError, RuntimeError):
        raise _unavailable() from None


def recover_finalize_commit(factory, fence, intent):
    """Locked read waits out the old transaction; unresolved work stays retryable.

    A live owned PROCESSING receipt returns 409 (per contract's alternative),
    rather than refinalizing without the caller re-verifying its object.
    """
    intent.payload()
    try:
        with factory() as session:
            repo.begin_primary(session)
            row = repo.lock_receipt(session, fence.project_id, fence.client_upload_id)
            now = repo.sample_db_clock(session)
            if row is None:
                raise _unavailable()
            result = _existing(session, row, intent, now)
            return _as_upload(result or _busy(row, now))
    except (SQLAlchemyError, RuntimeError):
        raise _unavailable() from None


def fail_after_known_rollback(factory, fence, safe_code, *, rollback_confirmed=False,
                              faults=NOOP_UPLOAD_FAULTS, commit=_commit):
    if not rollback_confirmed:
        raise ValueError("FAILED requires confirmed rollback")
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", safe_code):
        safe_code = "UPLOAD_FAILED"
    try:
        with factory() as session:
            repo.begin_primary(session)
            row = repo.lock_receipt(session, fence.project_id, fence.client_upload_id)
            now = repo.sample_db_clock(session)
            if row is None:
                return False
            _verify_row(row)
            if not repo.mark_failed_locked(session, row, fence, now, safe_code):
                return False
            faults.hit("BEFORE_FAILED_COMMIT", {"fence": fence})
            try:
                commit(session, "failed")
            except Exception:
                session.invalidate()
                return False
            return True
    except (SQLAlchemyError, DomainError, RuntimeError):
        return False
