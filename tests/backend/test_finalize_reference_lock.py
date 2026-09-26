from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from queue import Queue
from threading import Event
import time
from uuid import UUID, uuid4

import pytest
import rfc8785
from sqlalchemy import delete, select, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.app.errors import DomainError
from backend.app.models import Build, Screenshot, UploadReceipt
from backend.app.repositories import catalog as catalog_repo
from backend.app.services.upload_receipts import UploadIntent, finalize_attempt, reserve_or_replay
from backend.app.services.upload_types import ReservationState


class PauseAt:
    def __init__(self, phase):
        self.phase = phase
        self.reached = Event()
        self.proceed = Event()

    def hit(self, phase, context):
        if phase == self.phase:
            self.reached.set()
            if not self.proceed.wait(10):
                raise RuntimeError(f"timed out at {phase}")


def _intent(catalog):
    payload = {
        "fingerprint_version": 1,
        "upload_protocol_version": 1,
        "project_id": catalog["project"]["id"],
        "build_id": catalog["build"]["id"],
        "locale_id": catalog["locale"]["id"],
        "category_id": catalog["category"]["id"],
        "situation_id": catalog["situation"]["id"],
        "source": "agent",
        "original_filename": "capture.png",
        "metadata_version": 1,
        "metadata": {"checkpoint": "finalize-lock"},
        "file_hash": "a" * 64,
        "media_type": "image/png",
        "size_bytes": 3,
        "width": 1,
        "height": 1,
    }
    canonical = rfc8785.dumps(payload)
    return UploadIntent(
        UUID(catalog["project"]["id"]), uuid4(), canonical, sha256(canonical).hexdigest()
    )


def _factory(database):
    return sessionmaker(database, expire_on_commit=False)


def _reserve(factory, intent):
    reservation = reserve_or_replay(factory, intent)
    assert reservation.state == ReservationState.OWNED
    return reservation.fence


def _delete_build(factory, build_id, pid_queue=None):
    with factory() as session:
        session.connection(execution_options={"isolation_level": "READ COMMITTED"})
        session.execute(text("SET LOCAL lock_timeout = '5s'"))
        if pid_queue is not None:
            pid_queue.put(session.scalar(text("SELECT pg_backend_pid()")))
        session.execute(delete(Build).where(Build.id == build_id))
        session.commit()


def _wait_until_lock_wait(database, pid):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        with database.connect() as connection:
            waiting = connection.scalar(text(
                "SELECT wait_event_type = 'Lock' FROM pg_stat_activity WHERE pid = :pid"
            ), {"pid": pid})
        if waiting:
            return
        time.sleep(0.02)
    pytest.fail("concurrent parent delete never reached a PostgreSQL lock wait")


def test_catalog_parent_lock_uses_postgresql_key_share():
    class RecordingSession:
        statement = None

        def scalar(self, statement):
            self.statement = statement
            return object()

    session = RecordingSession()
    catalog_repo.get(session, Build, uuid4(), uuid4(), key_share=True)
    sql = str(session.statement.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    ))
    assert sql.endswith("FOR KEY SHARE")

    catalog_repo.get(session, Build, uuid4(), uuid4(), lock=True)
    existing_lock_sql = str(session.statement.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    ))
    assert existing_lock_sql.endswith("FOR UPDATE")


def test_finalize_parent_locks_hold_until_screenshot_insert(database, catalog):
    factory = _factory(database)
    intent = _intent(catalog)
    fence = _reserve(factory, intent)
    pause = PauseAt("AFTER_FINAL_REFERENCES_BEFORE_SCREENSHOT_INSERT")
    build_id = UUID(catalog["build"]["id"])
    pid_queue = Queue()

    with ThreadPoolExecutor(max_workers=2) as pool:
        finalizing = pool.submit(finalize_attempt, factory, fence, intent, faults=pause)
        assert pause.reached.wait(3)
        deleting = pool.submit(_delete_build, factory, build_id, pid_queue)
        delete_pid = pid_queue.get(timeout=3)
        _wait_until_lock_wait(database, delete_pid)
        pause.proceed.set()

        outcome = finalizing.result(timeout=5)
        assert (outcome.status_code, outcome.replayed) == (201, False)
        with pytest.raises(IntegrityError) as caught:
            deleting.result(timeout=5)
        assert getattr(caught.value.orig, "sqlstate", None) == "23503"

    with factory() as session:
        assert session.get(Build, build_id) is not None
        receipt = session.get(UploadReceipt, (intent.project_id, intent.client_upload_id))
        assert receipt.state == "COMPLETED"
        assert receipt.screenshot_id == fence.candidate_screenshot_id
        assert session.get(Screenshot, fence.candidate_screenshot_id) is not None


def test_parent_deleted_before_finalize_returns_404_and_fences_failed_generation(database, catalog):
    factory = _factory(database)
    intent = _intent(catalog)
    fence = _reserve(factory, intent)
    pause = PauseAt("BEFORE_FINAL_LOCK")
    build_id = UUID(catalog["build"]["id"])

    with ThreadPoolExecutor(max_workers=1) as pool:
        finalizing = pool.submit(finalize_attempt, factory, fence, intent, faults=pause)
        assert pause.reached.wait(3)
        _delete_build(factory, build_id)
        pause.proceed.set()
        with pytest.raises(DomainError) as caught:
            finalizing.result(timeout=5)

    assert (caught.value.status, caught.value.code) == (404, "RESOURCE_NOT_FOUND")
    with factory() as session:
        receipt = session.get(UploadReceipt, (intent.project_id, intent.client_upload_id))
        assert receipt.state == "FAILED"
        assert receipt.attempt_generation == fence.attempt_generation
        assert receipt.attempt_token == fence.attempt_token
        assert receipt.candidate_screenshot_id == fence.candidate_screenshot_id
        assert receipt.candidate_storage_key == fence.candidate_storage_key
        assert receipt.lease_expires_at is None
        assert receipt.last_error_code == "RESOURCE_NOT_FOUND"
        assert session.scalar(select(Screenshot).where(
            Screenshot.id == fence.candidate_screenshot_id
        )) is None
