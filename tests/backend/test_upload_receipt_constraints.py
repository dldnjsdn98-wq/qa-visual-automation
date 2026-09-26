from uuid import UUID, uuid1, uuid4

import pytest
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from backend.app.models import Screenshot, UploadReceipt


def _screenshot_values(catalog, *, source="agent", client_upload_id=None, screenshot_id=None):
    return {
        "id": screenshot_id or uuid4(),
        "project_id": UUID(catalog["project"]["id"]),
        "build_id": UUID(catalog["build"]["id"]),
        "locale_id": UUID(catalog["locale"]["id"]),
        "category_id": UUID(catalog["category"]["id"]),
        "situation_id": UUID(catalog["situation"]["id"]),
        "source": source,
        "original_filename": "capture.png",
        "storage_key": f"objects/{catalog['project']['id']}/{uuid4()}.png",
        "file_hash": "a" * 64,
        "media_type": "image/png",
        "size_bytes": 10,
        "width": 1,
        "height": 1,
        "client_upload_id": client_upload_id,
    }


def _receipt_values(catalog, *, client_upload_id=None, state="PROCESSING", **overrides):
    project_id = UUID(catalog["project"]["id"])
    client_upload_id = client_upload_id or uuid4()
    candidate_id = overrides.pop("candidate_screenshot_id", uuid4())
    values = {
        "project_id": project_id,
        "client_upload_id": client_upload_id,
        "fingerprint_version": 1,
        "upload_protocol_version": 1,
        "request_fingerprint": "b" * 64,
        "canonical_request": b"{}",
        "state": state,
        "attempt_generation": 1,
        "attempt_token": uuid4(),
        "candidate_screenshot_id": candidate_id,
        "candidate_storage_key": f"objects/{project_id}/{candidate_id}.png",
        "screenshot_id": None,
        "lease_expires_at": "2030-01-01T00:00:00Z" if state == "PROCESSING" else None,
        "last_error_code": None,
    }
    values.update(overrides)
    return values


def test_screenshot_source_and_client_upload_id_pairs_are_enforced(database, catalog):
    manual = _screenshot_values(catalog, source="manual", client_upload_id=None)
    with database.begin() as connection:
        connection.execute(insert(Screenshot).values(manual))

    for source, client_upload_id in (("manual", uuid4()), ("agent", None), ("automation", None), ("other", uuid4())):
        with pytest.raises(IntegrityError):
            with database.begin() as connection:
                connection.execute(
                    insert(Screenshot).values(
                        _screenshot_values(catalog, source=source, client_upload_id=client_upload_id)
                    )
                )


def test_receipt_state_shape_and_candidate_key_are_enforced(database, catalog):
    with pytest.raises(IntegrityError):
        with database.begin() as connection:
            connection.execute(
                insert(UploadReceipt).values(_receipt_values(catalog, lease_expires_at=None))
            )

    with pytest.raises(IntegrityError):
        with database.begin() as connection:
            connection.execute(
                insert(UploadReceipt).values(
                    _receipt_values(catalog, candidate_storage_key="objects/wrong.png")
                )
            )

    with pytest.raises(IntegrityError):
        with database.begin() as connection:
            connection.execute(
                insert(UploadReceipt).values(
                    _receipt_values(catalog, state="COMPLETED", screenshot_id=uuid4())
                )
            )

    for override in (
        {"attempt_generation": 0},
        {"attempt_token": uuid1()},
        {"client_upload_id": uuid1()},
        {"fingerprint_version": 2},
        {"upload_protocol_version": 2},
    ):
        with pytest.raises(IntegrityError):
            with database.begin() as connection:
                connection.execute(insert(UploadReceipt).values(_receipt_values(catalog, **override)))


def test_completed_receipt_requires_its_own_agent_screenshot(database, catalog):
    client_upload_id = uuid4()
    screenshot_id = uuid4()
    receipt = _receipt_values(
        catalog,
        client_upload_id=client_upload_id,
        state="COMPLETED",
        candidate_screenshot_id=screenshot_id,
        screenshot_id=screenshot_id,
    )
    with database.begin() as connection:
        connection.execute(
            insert(Screenshot).values(
                _screenshot_values(
                    catalog,
                    client_upload_id=client_upload_id,
                    screenshot_id=screenshot_id,
                )
            )
        )
        connection.execute(insert(UploadReceipt).values(receipt))

    wrong_client_upload_id = uuid4()
    with pytest.raises(IntegrityError):
        with database.begin() as connection:
            connection.execute(
                insert(UploadReceipt).values(
                    _receipt_values(
                        catalog,
                        client_upload_id=wrong_client_upload_id,
                        state="COMPLETED",
                        candidate_screenshot_id=screenshot_id,
                        screenshot_id=screenshot_id,
                    )
                )
            )


def test_receipt_identity_and_candidate_uniqueness_are_scoped_and_durable(database, catalog):
    receipt = _receipt_values(catalog)
    with database.begin() as connection:
        connection.execute(insert(UploadReceipt).values(receipt))

    duplicate_identity = _receipt_values(
        catalog,
        client_upload_id=receipt["client_upload_id"],
    )
    with pytest.raises(IntegrityError):
        with database.begin() as connection:
            connection.execute(insert(UploadReceipt).values(duplicate_identity))

    duplicate_candidate = _receipt_values(
        catalog,
        candidate_screenshot_id=receipt["candidate_screenshot_id"],
        candidate_storage_key=receipt["candidate_storage_key"],
    )
    with pytest.raises(IntegrityError):
        with database.begin() as connection:
            connection.execute(insert(UploadReceipt).values(duplicate_candidate))


def test_receipts_reject_an_unknown_project(database, catalog):
    project_id = uuid4()
    candidate_id = uuid4()
    with pytest.raises(IntegrityError):
        with database.begin() as connection:
            connection.execute(
                insert(UploadReceipt).values(
                    _receipt_values(
                        catalog,
                        project_id=project_id,
                        state="FAILED",
                        candidate_screenshot_id=candidate_id,
                        candidate_storage_key=f"objects/{project_id}/{candidate_id}.png",
                    )
                )
            )
