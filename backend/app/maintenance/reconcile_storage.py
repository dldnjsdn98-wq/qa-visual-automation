"""Exclusive storage maintenance. Stop all upload activity before invoking it."""

import argparse
import json
import time
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy import func, select, text

from backend.app.api.dependencies import get_storage
from backend.app.db import SessionFactory
from backend.app.models import Screenshot, UploadReceipt
from backend.app.storage.base import ObjectMismatch, ObjectNotFound, StoredObject


MAX_PAGE_SIZE = 100
MINIMUM_OBJECT_AGE_SECONDS = 24 * 60 * 60
MAINTENANCE_LOCK_ID = 7_217_330_448_012_229_715
ABANDONED_ERROR_CODE = "MAINTENANCE_ABANDONED"

AFTER_INVENTORY = "RECONCILE_AFTER_INVENTORY"
AFTER_ABANDONED_FAILED_COMMIT = "RECONCILE_AFTER_ABANDONED_FAILED_COMMIT"
BEFORE_DELETE_RECHECK = "RECONCILE_BEFORE_DELETE_RECHECK"
AFTER_RECHECK_BEFORE_DELETE = "RECONCILE_AFTER_RECHECK_BEFORE_DELETE"


class ReconcileFaultInjector(Protocol):
    def hit(self, point: str, context: dict[str, Any]) -> None: ...


class NoopReconcileFaultInjector:
    def hit(self, point: str, context: dict[str, Any]) -> None:
        return None


@dataclass(frozen=True)
class ScreenshotReference:
    storage_key: str
    file_hash: str
    size_bytes: int


@dataclass(frozen=True)
class ProcessingReference:
    project_id: str
    client_upload_id: str
    candidate_storage_key: str


@dataclass(frozen=True)
class DatabaseInventory:
    screenshots: tuple[ScreenshotReference, ...]
    processing: tuple[ProcessingReference, ...]

    @property
    def protected_keys(self) -> set[str]:
        keys = {row.storage_key for row in self.screenshots}
        keys.update(row.candidate_storage_key for row in self.processing)
        return keys


@dataclass(frozen=True)
class StorageInventory:
    objects: tuple[StoredObject, ...]
    staging: tuple[StoredObject, ...]


def _assert_primary(session) -> None:
    if session.scalar(text("SELECT pg_is_in_recovery()")):
        raise ValueError("Maintenance requires the primary database")


def assert_exclusive_primary(session, writers_stopped: bool) -> None:
    """Validate the operator assertion and hold one maintenance lock per primary."""
    if not writers_stopped:
        raise ValueError(
            "Stop upload writers, lease renewers, recovery jobs, and in-flight "
            "transactions first"
        )
    _assert_primary(session)
    acquired = session.scalar(
        text("SELECT pg_try_advisory_lock(:lock_id)"),
        {"lock_id": MAINTENANCE_LOCK_ID},
    )
    if not acquired:
        raise ValueError("Another storage maintenance operation is active")


def inventory_db_references(session) -> DatabaseInventory:
    """Read every durable object reference; expired PROCESSING is still protected."""
    screenshot_rows = session.execute(
        select(Screenshot.storage_key, Screenshot.file_hash, Screenshot.size_bytes)
    ).all()
    processing_rows = session.execute(
        select(
            UploadReceipt.project_id,
            UploadReceipt.client_upload_id,
            UploadReceipt.candidate_storage_key,
        ).where(UploadReceipt.state == "PROCESSING")
    ).all()
    return DatabaseInventory(
        screenshots=tuple(
            ScreenshotReference(row.storage_key, row.file_hash, row.size_bytes)
            for row in screenshot_rows
        ),
        processing=tuple(
            ProcessingReference(
                str(row.project_id),
                str(row.client_upload_id),
                row.candidate_storage_key,
            )
            for row in processing_rows
        ),
    )


def _inventory_complete(method) -> tuple[StoredObject, ...]:
    items: list[StoredObject] = []
    seen: set[str] = set()
    offset = 0
    while True:
        page = method(offset, MAX_PAGE_SIZE)
        if not page:
            return tuple(items)
        if len(page) > MAX_PAGE_SIZE:
            raise RuntimeError("Storage inventory returned an oversized page")
        for item in page:
            if item.key in seen:
                raise RuntimeError("Storage inventory returned a duplicate key")
            seen.add(item.key)
            items.append(item)
        offset += len(page)


def inventory_storage_complete(storage) -> StorageInventory:
    """Finish both inventories before any state transition or deletion."""
    return StorageInventory(
        objects=_inventory_complete(storage.list_objects),
        staging=_inventory_complete(storage.list_staging),
    )


def mark_abandoned_processing(factory) -> tuple[ProcessingReference, ...]:
    """Under caller-held exclusivity, durably fail all remaining PROCESSING rows."""
    with factory() as session:
        _assert_primary(session)
        receipts = list(
            session.scalars(
                select(UploadReceipt)
                .where(UploadReceipt.state == "PROCESSING")
                .with_for_update()
            )
        )
        abandoned = tuple(
            ProcessingReference(
                str(receipt.project_id),
                str(receipt.client_upload_id),
                receipt.candidate_storage_key,
            )
            for receipt in receipts
        )
        for receipt in receipts:
            receipt.state = "FAILED"
            receipt.lease_expires_at = None
            receipt.last_error_code = ABANDONED_ERROR_CODE
            receipt.updated_at = func.clock_timestamp()
        session.commit()
        return abandoned


def classify_candidates(
    database: DatabaseInventory,
    storage: StorageInventory,
    *,
    now: float,
) -> tuple[list[str], list[str]]:
    cutoff = now - MINIMUM_OBJECT_AGE_SECONDS
    protected = database.protected_keys
    objects = [
        item.key
        for item in storage.objects
        if item.key not in protected and item.modified_at < cutoff
    ]
    staging = [item.key for item in storage.staging if item.modified_at < cutoff]
    return objects, staging


def recheck_delete_eligibility(factory, key: str) -> bool:
    """Use a fresh primary transaction immediately before one exact deletion."""
    with factory() as session:
        _assert_primary(session)
        screenshot_id = session.scalar(
            select(Screenshot.id).where(Screenshot.storage_key == key).limit(1)
        )
        processing_project = session.scalar(
            select(UploadReceipt.project_id)
            .where(
                UploadReceipt.candidate_storage_key == key,
                UploadReceipt.state == "PROCESSING",
            )
            .limit(1)
        )
        return screenshot_id is None and processing_project is None


def delete_exact_candidate(storage, key: str) -> None:
    if key.startswith("staging/"):
        storage.discard_stage(key.removeprefix("staging/"))
    else:
        storage.delete(key)


def _verify_screenshot_objects(storage, database, report) -> None:
    for row in database.screenshots:
        try:
            storage.verify_exact(
                row.storage_key,
                sha256=row.file_hash,
                byte_count=row.size_bytes,
            )
        except ObjectNotFound:
            report["missing"].append(row.storage_key)
        except ObjectMismatch:
            report["mismatches"].append(row.storage_key)


def _unlock_maintenance(session) -> None:
    released = session.scalar(
        text("SELECT pg_advisory_unlock(:lock_id)"),
        {"lock_id": MAINTENANCE_LOCK_ID},
    )
    if not released:
        raise RuntimeError("Storage maintenance lock was not held")


def reconcile(
    factory,
    storage,
    *,
    writers_stopped,
    apply=False,
    now=None,
    fault_injector=None,
):
    now = time.time() if now is None else now
    faults = fault_injector or NoopReconcileFaultInjector()
    report = {
        "apply": apply,
        "orphans": [],
        "staging": [],
        "missing": [],
        "mismatches": [],
        "would_mark_failed": [],
        "marked_failed": [],
        "eligible_after_failed": [],
        "deleted": [],
    }

    control = factory()
    locked = False
    active_error = False
    try:
        assert_exclusive_primary(control, writers_stopped)
        locked = True
        database = inventory_db_references(control)
        storage_inventory = inventory_storage_complete(storage)
        _verify_screenshot_objects(storage, database, report)
        report["would_mark_failed"] = [
            row.candidate_storage_key for row in database.processing
        ]

        faults.hit(
            AFTER_INVENTORY,
            {
                "apply": apply,
                "processing": tuple(report["would_mark_failed"]),
                "objects": tuple(item.key for item in storage_inventory.objects),
            },
        )

        if apply:
            abandoned = mark_abandoned_processing(factory)
            report["marked_failed"] = [
                row.candidate_storage_key for row in abandoned
            ]
            faults.hit(
                AFTER_ABANDONED_FAILED_COMMIT,
                {"marked_failed": tuple(report["marked_failed"])},
            )
            # The transition committed in another transaction. A fresh inventory is
            # required; the original REPEATABLE READ snapshot cannot prove eligibility.
            with factory() as session:
                _assert_primary(session)
                database = inventory_db_references(session)

        orphans, staging = classify_candidates(
            database,
            storage_inventory,
            now=now,
        )
        report["orphans"] = orphans
        report["staging"] = staging
        abandoned_keys = set(report["would_mark_failed"])
        report["eligible_after_failed"] = [
            key for key in orphans if key in abandoned_keys
        ]

        if apply:
            for key in [*orphans, *staging]:
                faults.hit(BEFORE_DELETE_RECHECK, {"key": key})
                if not recheck_delete_eligibility(factory, key):
                    continue
                faults.hit(AFTER_RECHECK_BEFORE_DELETE, {"key": key})
                delete_exact_candidate(storage, key)
                report["deleted"].append(key)
        return report
    except BaseException:
        active_error = True
        raise
    finally:
        if locked:
            try:
                _unlock_maintenance(control)
            except BaseException:
                # An invalidated backend connection cannot retain a session lock.
                try:
                    control.connection().invalidate()
                except BaseException:
                    pass
                if not active_error:
                    raise
        control.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--writers-stopped", action="store_true", required=True)
    parser.add_argument("--apply", action="store_true", help="Default is dry run")
    args = parser.parse_args()
    report = reconcile(
        SessionFactory,
        get_storage(),
        writers_stopped=args.writers_stopped,
        apply=args.apply,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
