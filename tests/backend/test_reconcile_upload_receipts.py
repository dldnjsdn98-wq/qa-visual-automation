"""Focused receipt-aware maintenance and exact-object checks."""

import hashlib
import io
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID
from uuid import uuid4

import pytest

from backend.app.maintenance.reconcile_storage import (
    DatabaseInventory,
    ProcessingReference,
    ScreenshotReference,
    StorageInventory,
    classify_candidates,
    inventory_storage_complete,
)
from backend.app.storage.base import ObjectMismatch, StoredObject
from backend.app.storage.local import LocalStorage
from backend.app.maintenance import reconcile_storage as maintenance
from backend.app.models import UploadReceipt, Screenshot
from sqlalchemy import delete, event, select, text
from sqlalchemy.exc import DBAPIError


NOW = 2_000_000_000
PAYLOAD = b"receipt candidate bytes"


@pytest.fixture
def receipt_case(client, catalog):
    """Real committed receipts, real local objects, independent PostgreSQL sessions."""
    project = UUID(catalog["project"]["id"])
    storage = client.storage

    def object_key(age=90000):
        key = f"objects/{project}/{uuid4()}.png"
        storage.publish(storage.stage(io.BytesIO(PAYLOAD), 1000), key)
        os.utime(storage.root / key, (NOW - age, NOW - age))
        return key

    def receipt(key=None, expired=False):
        key = key or object_key()
        identity = uuid4()
        with client.factory() as session:
            session.add(UploadReceipt(
                project_id=project, client_upload_id=identity,
                fingerprint_version=1, upload_protocol_version=1,
                request_fingerprint=hashlib.sha256(b"{}").hexdigest(),
                canonical_request=b"{}", state="PROCESSING", attempt_generation=1,
                attempt_token=uuid4(), candidate_screenshot_id=UUID(key.split("/")[-1][:-4]),
                candidate_storage_key=key,
                lease_expires_at=datetime.now(timezone.utc) + timedelta(seconds=-60 if expired else 3600),
            ))
            session.commit()
        return key

    def screenshot(key):
        with client.factory() as session:
            session.add(Screenshot(
                id=UUID(key.split("/")[-1][:-4]), project_id=project,
                build_id=UUID(catalog["build"]["id"]), locale_id=UUID(catalog["locale"]["id"]),
                category_id=UUID(catalog["category"]["id"]), situation_id=UUID(catalog["situation"]["id"]),
                source="manual", original_filename="proof.png", storage_key=key,
                file_hash=hashlib.sha256(PAYLOAD).hexdigest(), media_type="image/png",
                size_bytes=len(PAYLOAD), width=1, height=1,
            ))
            session.commit()

    def states():
        with client.factory() as session:
            return {r.candidate_storage_key: (r.state, r.lease_expires_at, r.last_error_code)
                    for r in session.scalars(select(UploadReceipt).where(UploadReceipt.project_id == project))}

    yield client, object_key, receipt, screenshot, states
    with client.factory() as session:
        session.execute(delete(UploadReceipt).where(UploadReceipt.project_id == project))
        session.execute(delete(Screenshot).where(Screenshot.project_id == project))
        session.commit()


class Barrier:
    def __init__(self, point, callback):
        self.point, self.callback = point, callback
        self.hits = 0

    def hit(self, point, context):
        if point == self.point:
            self.hits += 1
            self.callback(context)


def run(case, **kwargs):
    return maintenance.reconcile(case[0].factory, case[0].storage,
                                 writers_stopped=True, now=NOW, **kwargs)


def test_postgres_dry_run_protects_live_expired_and_screenshot(receipt_case):
    client, obj, receipt, screenshot, states = receipt_case
    live, expired, committed, orphan = receipt(), receipt(expired=True), obj(), obj()
    screenshot(committed)
    before = states()
    report = run(receipt_case)
    assert set(report["would_mark_failed"]) == {live, expired}
    assert report["orphans"] == [orphan]
    assert report["deleted"] == report["marked_failed"] == []
    assert states() == before
    assert all((client.storage.root / k).read_bytes() == PAYLOAD for k in (live, expired, committed, orphan))


def test_postgres_failed_is_committed_before_delete_and_strict_age(receipt_case, monkeypatch):
    client, obj, receipt, screenshot, states = receipt_case
    old, boundary, young = [receipt(obj(age), expired=True) for age in (86401, 86400, 86399)]
    stages = []
    for age in (86401, 86400, 86399):
        stage = client.storage.stage(io.BytesIO(PAYLOAD), 1000)
        key = f"staging/{stage.token}"
        os.utime(client.storage.root / key, (NOW-age, NOW-age))
        stages.append(key)
    original = client.storage.delete
    observed = []
    def checked_delete(key):
        # A different physical connection must see the committed FAILED state.
        assert all(v == ("FAILED", None, maintenance.ABANDONED_ERROR_CODE) for v in states().values())
        observed.append(key)
        original(key)
    monkeypatch.setattr(client.storage, "delete", checked_delete)
    report = run(receipt_case, apply=True)
    assert set(report["marked_failed"]) == {old, boundary, young}
    assert report["eligible_after_failed"] == [old]
    assert set(report["deleted"]) == {old, stages[0]}
    assert observed == [old]
    assert all((client.storage.root / key).exists() for key in (boundary, young, *stages[1:]))


@pytest.mark.parametrize("point", [maintenance.AFTER_ABANDONED_FAILED_COMMIT, maintenance.BEFORE_DELETE_RECHECK])
@pytest.mark.parametrize("kind", ["screenshot", "processing"])
def test_postgres_fresh_reference_blocks_delete(receipt_case, point, kind):
    client, obj, receipt, screenshot, states = receipt_case
    key = receipt(expired=True)
    def insert_reference(context):
        if kind == "screenshot":
            screenshot(key)
        else:
            with client.factory() as session:
                row = session.scalar(select(UploadReceipt).where(UploadReceipt.candidate_storage_key == key))
                row.state = "PROCESSING"
                row.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=60)
                row.last_error_code = None
                session.commit()
    barrier = Barrier(point, insert_reference)
    report = run(receipt_case, apply=True, fault_injector=barrier)
    assert barrier.hits == 1
    assert report["deleted"] == []
    assert (client.storage.root / key).read_bytes() == PAYLOAD
    if point == maintenance.AFTER_ABANDONED_FAILED_COMMIT:
        assert report["orphans"] == []  # Proves refresh, not only predelete filtering.
    else:
        assert report["orphans"] == [key]


@pytest.mark.parametrize("point", [maintenance.AFTER_INVENTORY, maintenance.AFTER_ABANDONED_FAILED_COMMIT,
                                   maintenance.BEFORE_DELETE_RECHECK, maintenance.AFTER_RECHECK_BEFORE_DELETE])
def test_postgres_fault_barriers_fail_closed(receipt_case, point):
    client, obj, receipt, screenshot, states = receipt_case
    key = receipt(expired=True)
    def fail(context):
        raise RuntimeError("injected barrier failure")
    with pytest.raises(RuntimeError, match="injected barrier failure"):
        run(receipt_case, apply=True, fault_injector=Barrier(point, fail))
    assert (client.storage.root / key).read_bytes() == PAYLOAD
    assert states()[key][0] == ("PROCESSING" if point == maintenance.AFTER_INVENTORY else "FAILED")
    # A new maintenance run also proves the previous session advisory lock was released.
    run(receipt_case)


@pytest.mark.parametrize("method", ["list_objects", "list_staging", "verify_exact", "delete"])
def test_postgres_storage_errors_fail_closed(receipt_case, monkeypatch, method):
    client, obj, receipt, screenshot, states = receipt_case
    key = receipt(expired=True)
    screenshot(obj())
    def fail(*args, **kwargs):
        raise OSError("injected storage failure")
    monkeypatch.setattr(client.storage, method, fail)
    with pytest.raises(OSError, match="injected storage failure"):
        run(receipt_case, apply=True)
    assert (client.storage.root / key).read_bytes() == PAYLOAD
    assert states()[key][0] == ("FAILED" if method == "delete" else "PROCESSING")


@pytest.mark.parametrize("phase", ["inventory", "transition", "refresh", "predelete"])
def test_postgres_database_errors_fail_closed(receipt_case, monkeypatch, phase):
    client, obj, receipt, screenshot, states = receipt_case
    key = receipt(expired=True)
    original = client.factory
    calls = 0
    target = {"inventory": 1, "transition": 2, "refresh": 3, "predelete": 4}[phase]
    def factory():
        nonlocal calls
        calls += 1
        session = original()
        if calls == target:
            # Actual PostgreSQL error leaves this transaction aborted. No fake DB rows.
            try:
                session.execute(text("SELECT 1 / 0"))
            except DBAPIError:
                pass
        return session
    with pytest.raises(DBAPIError):
        maintenance.reconcile(factory, client.storage, writers_stopped=True, apply=True, now=NOW)
    assert (client.storage.root / key).read_bytes() == PAYLOAD
    assert states()[key][0] == ("PROCESSING" if target <= 2 else "FAILED")
    run(receipt_case)


def test_postgres_failed_transition_commit_error_rolls_back(receipt_case):
    client, obj, receipt, screenshot, states = receipt_case
    key = receipt(expired=True)
    original = client.factory
    calls = 0
    def factory():
        nonlocal calls
        calls += 1
        session = original()
        if calls == 2:
            def fail_commit(session):
                session.flush()  # FAILED update reaches PostgreSQL but is not committed.
                assert states()[key][0] == "PROCESSING"
                session.execute(text("SELECT 1 / 0"))
            event.listen(session, "before_commit", fail_commit)
        return session
    with pytest.raises(DBAPIError):
        maintenance.reconcile(factory, client.storage, writers_stopped=True, apply=True, now=NOW)
    assert states()[key][0] == "PROCESSING"
    assert (client.storage.root / key).read_bytes() == PAYLOAD
    run(receipt_case)


def test_postgres_partial_inventory_error_never_mutates(receipt_case, monkeypatch):
    client, obj, receipt, screenshot, states = receipt_case
    key = receipt(expired=True)
    original = client.storage.list_objects
    offsets = []
    def partial(offset, limit):
        offsets.append(offset)
        if offset:
            raise OSError("second inventory page failed")
        return original(offset, limit)
    monkeypatch.setattr(client.storage, "list_objects", partial)
    with pytest.raises(OSError, match="second inventory page failed"):
        run(receipt_case, apply=True)
    assert offsets == [0, 1]
    assert states()[key][0] == "PROCESSING"
    assert (client.storage.root / key).read_bytes() == PAYLOAD


def test_postgres_maintenance_lock_and_writer_assertion_fail_closed(receipt_case):
    client, obj, receipt, screenshot, states = receipt_case
    key = receipt(expired=True)
    with pytest.raises(ValueError, match="Stop upload writers"):
        maintenance.reconcile(client.factory, client.storage, writers_stopped=False, apply=True, now=NOW)
    with client.factory() as lock_owner:
        lock_owner.execute(text("SELECT pg_advisory_lock(:id)"), {"id": maintenance.MAINTENANCE_LOCK_ID})
        try:
            with pytest.raises(ValueError, match="Another storage maintenance"):
                run(receipt_case, apply=True)
        finally:
            lock_owner.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": maintenance.MAINTENANCE_LOCK_ID})
    assert states()[key][0] == "PROCESSING"
    assert (client.storage.root / key).read_bytes() == PAYLOAD
    run(receipt_case)


def test_processing_candidate_is_protected_regardless_of_lease_age():
    now = 2_000_000_000
    processing_key = f"objects/{uuid4()}/{uuid4()}.png"
    screenshot_key = f"objects/{uuid4()}/{uuid4()}.png"
    orphan_key = f"objects/{uuid4()}/{uuid4()}.png"
    database = DatabaseInventory(
        (ScreenshotReference(screenshot_key, "a" * 64, 1),),
        (ProcessingReference(str(uuid4()), str(uuid4()), processing_key),),
    )
    storage = StorageInventory(
        tuple(StoredObject(key, 1, now - 90_000) for key in
              (processing_key, screenshot_key, orphan_key)),
        (),
    )
    assert classify_candidates(database, storage, now=now) == ([orphan_key], [])


def test_incomplete_storage_inventory_fails_closed():
    class BrokenStorage:
        def list_objects(self, offset=0, limit=100):
            raise OSError("incomplete inventory")

        def list_staging(self, offset=0, limit=100):
            pytest.fail("staging inventory should not hide object inventory failure")

    with pytest.raises(OSError, match="incomplete inventory"):
        inventory_storage_complete(BrokenStorage())


def test_exact_verification_checks_hash_and_size_without_replacing(tmp_path):
    storage = LocalStorage(tmp_path / "storage")
    original = b"original bytes"
    staged = storage.stage(io.BytesIO(original), 100)
    key = f"objects/{uuid4()}/{uuid4()}.png"
    storage.publish(staged, key)
    digest = hashlib.sha256(original).hexdigest()
    assert storage.verify_exact(key, sha256=digest, byte_count=len(original)).byte_count == len(original)
    with pytest.raises(ObjectMismatch):
        storage.verify_exact(key, sha256="0" * 64, byte_count=len(original))
    with pytest.raises(ObjectMismatch):
        storage.verify_exact(key, sha256=digest, byte_count=len(original) + 1)
    with storage.open_read(key)[0] as stream:
        assert stream.read() == original
