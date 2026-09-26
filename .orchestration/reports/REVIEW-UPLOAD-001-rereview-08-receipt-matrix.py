from __future__ import annotations

from hashlib import sha256
import time
from uuid import UUID, uuid4

import pytest
import rfc8785
from sqlalchemy import func, select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from backend.app.errors import DomainError
from backend.app.models import Screenshot, UploadReceipt
from backend.app.repositories import upload_receipts as repo
from backend.app.services.upload_receipts import (
    UploadIntent,
    fail_after_known_rollback,
    finalize_attempt,
    renew_attempt,
    reserve_or_replay,
)
from backend.app.services.upload_types import ReservationState


def _factory(database):
    return sessionmaker(database, expire_on_commit=False)


def _intent(catalog, label: str) -> UploadIntent:
    payload = {
        "fingerprint_version": 1,
        "upload_protocol_version": 1,
        "project_id": catalog["project"]["id"],
        "build_id": catalog["build"]["id"],
        "locale_id": catalog["locale"]["id"],
        "category_id": catalog["category"]["id"],
        "situation_id": catalog["situation"]["id"],
        "source": "agent",
        "original_filename": f"{label}.png",
        "metadata_version": 1,
        "metadata": {"checkpoint": label},
        "file_hash": sha256(label.encode()).hexdigest(),
        "media_type": "image/png",
        "size_bytes": 3,
        "width": 1,
        "height": 1,
    }
    canonical = rfc8785.dumps(payload)
    return UploadIntent(
        UUID(catalog["project"]["id"]),
        uuid4(),
        canonical,
        sha256(canonical).hexdigest(),
    )


def _commit_then_raise(session, phase):
    session.commit()
    raise OperationalError(f"committed response loss at {phase}", {}, Exception())


def _rollback_then_raise(session, phase):
    session.rollback()
    raise OperationalError(f"rolled back response loss at {phase}", {}, Exception())


def _owned(factory, intent, *, commit=None):
    kwargs = {} if commit is None else {"commit": commit}
    result = reserve_or_replay(factory, intent, **kwargs)
    assert result.state is ReservationState.OWNED
    return result.fence


def _expire_exactly_at_db_clock(factory, intent):
    with factory() as session:
        repo.begin_primary(session)
        session.execute(
            update(UploadReceipt)
            .where(
                UploadReceipt.project_id == intent.project_id,
                UploadReceipt.client_upload_id == intent.client_upload_id,
            )
            .values(lease_expires_at=func.clock_timestamp())
        )
        session.commit()


def test_exact_expiry_takeover_and_complete_stale_fence_denial(database, catalog):
    factory = _factory(database)
    intent = _intent(catalog, "exact-expiry")
    stale = _owned(factory, intent)
    _expire_exactly_at_db_clock(factory, intent)

    fresh = _owned(factory, intent)
    assert fresh.attempt_generation == stale.attempt_generation + 1
    assert fresh.attempt_token != stale.attempt_token
    assert fresh.candidate_screenshot_id != stale.candidate_screenshot_id
    assert fresh.candidate_storage_key != stale.candidate_storage_key

    assert renew_attempt(factory, stale) is False
    assert fail_after_known_rollback(
        factory, stale, "STALE_OWNER", rollback_confirmed=True
    ) is False
    with pytest.raises(DomainError) as caught:
        finalize_attempt(factory, stale, intent)
    assert (caught.value.status, caught.value.code) == (409, "UPLOAD_IN_PROGRESS")

    outcome = finalize_attempt(factory, fresh, intent)
    assert (outcome.status_code, outcome.replayed) == (201, False)
    with factory() as session:
        receipt = session.get(UploadReceipt, (intent.project_id, intent.client_upload_id))
        assert receipt.state == "COMPLETED"
        assert receipt.screenshot_id == fresh.candidate_screenshot_id
        assert session.get(Screenshot, fresh.candidate_screenshot_id) is not None
        assert session.get(Screenshot, stale.candidate_screenshot_id) is None


def test_ambiguous_first_insert_and_finalize_commit_outcomes(database, catalog):
    factory = _factory(database)

    committed_first = _intent(catalog, "first-commit-loss")
    fence_a = _owned(factory, committed_first, commit=_commit_then_raise)
    rolled_first = _intent(catalog, "first-rollback-loss")
    fence_b = _owned(factory, rolled_first, commit=_rollback_then_raise)
    assert fence_a.attempt_generation == fence_b.attempt_generation == 1

    committed_finalize = _intent(catalog, "finalize-commit-loss")
    committed_fence = _owned(factory, committed_finalize)
    replay = finalize_attempt(
        factory, committed_fence, committed_finalize, commit=_commit_then_raise
    )
    assert (replay.status_code, replay.replayed) == (200, True)

    rolled_finalize = _intent(catalog, "finalize-rollback-loss")
    rolled_fence = _owned(factory, rolled_finalize)
    with pytest.raises(DomainError) as caught:
        finalize_attempt(
            factory, rolled_fence, rolled_finalize, commit=_rollback_then_raise
        )
    assert (caught.value.status, caught.value.code) == (409, "UPLOAD_IN_PROGRESS")
    completed = finalize_attempt(factory, rolled_fence, rolled_finalize)
    assert (completed.status_code, completed.replayed) == (201, False)

    with factory() as session:
        for intent, fence in (
            (committed_finalize, committed_fence),
            (rolled_finalize, rolled_fence),
        ):
            receipt = session.get(UploadReceipt, (intent.project_id, intent.client_upload_id))
            assert receipt.state == "COMPLETED"
            assert receipt.screenshot_id == fence.candidate_screenshot_id
        count = session.scalar(
            select(func.count()).select_from(Screenshot).where(
                Screenshot.client_upload_id.in_([
                    committed_finalize.client_upload_id,
                    rolled_finalize.client_upload_id,
                ])
            )
        )
        assert count == 2


def test_ambiguous_takeover_never_guesses_rolled_back_ownership(database, catalog):
    factory = _factory(database)
    intent = _intent(catalog, "takeover-ambiguity")
    first = _owned(factory, intent)
    _expire_exactly_at_db_clock(factory, intent)

    outcome = reserve_or_replay(factory, intent, commit=_rollback_then_raise)
    assert (outcome.state, outcome.retry_after) == (
        ReservationState.IN_PROGRESS, 1
    )
    with factory() as session:
        row = session.get(UploadReceipt, (intent.project_id, intent.client_upload_id))
        assert row.attempt_generation == first.attempt_generation
        assert row.attempt_token == first.attempt_token

    fresh = _owned(factory, intent)
    assert fresh.attempt_generation == first.attempt_generation + 1


def test_receipt_lock_timeout_is_bounded_503_with_retry_after(database, catalog):
    factory = _factory(database)
    intent = _intent(catalog, "lock-timeout")
    _owned(factory, intent)

    blocker = factory()
    try:
        repo.begin_primary(blocker)
        assert repo.lock_receipt(blocker, intent.project_id, intent.client_upload_id) is not None
        started = time.monotonic()
        with pytest.raises(DomainError) as caught:
            reserve_or_replay(factory, intent)
        elapsed = time.monotonic() - started
        assert (caught.value.status, caught.value.code, caught.value.retry_after) == (
            503, "DATABASE_UNAVAILABLE", 5
        )
        assert 4.5 <= elapsed < 9.0
    finally:
        blocker.rollback()
        blocker.close()
