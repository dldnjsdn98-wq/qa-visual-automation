import hashlib
import io
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import UUID, uuid4
import pytest
from PIL import Image
from sqlalchemy import select, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from backend.app.models import Screenshot, UploadReceipt
from backend.app.services import upload_receipts
from backend.app.services.screenshots import LeaseKeeper
from backend.app.services.upload_types import AttemptFence, UploadOutcome
from backend.app.errors import DomainError
from conftest import created


def image_bytes(kind="PNG"):
    stream = io.BytesIO()
    Image.new("RGB", (12, 8), (14, 35, 75)).save(stream, format=kind)
    return stream.getvalue()


def metadata(catalog, **extra):
    return dict(build_id=catalog["build"]["id"], locale_id=catalog["locale"]["id"], category_id=catalog["category"]["id"], situation_id=catalog["situation"]["id"], source="manual", **extra)


def agent_metadata(catalog, client_upload_id=None, data=None, **extra):
    data = image_bytes() if data is None else data
    return dict(
        upload_protocol_version=1,
        client_upload_id=str(client_upload_id or uuid4()),
        build_id=catalog["build"]["id"],
        locale_id=catalog["locale"]["id"],
        category_id=catalog["category"]["id"],
        situation_id=catalog["situation"]["id"],
        source="agent",
        expected_file_hash=hashlib.sha256(data).hexdigest(),
        **extra,
    )


def upload(client, catalog, values=None, data=None, filename="tutorial.png", mime="image/png"):
    return client.post(catalog["p"] + "/screenshots", files={"file": (filename, data if data is not None else image_bytes(), mime), "metadata": (None, json.dumps(values if values is not None else metadata(catalog)), "application/json")})


@pytest.mark.parametrize("kind,mime", [("PNG", "image/png"), ("JPEG", "image/jpeg")])
def test_upload_list_detail_content_expected(client, catalog, kind, mime):
    data = image_bytes(kind)
    values = metadata(catalog, metadata={"device": "기기 😀", "resolution": {"width": 12, "height": 8}, "steps": [{"note": "e\u0301"}]})
    response = upload(client, catalog, values, data, "C:/capture/화면.png", mime)
    assert response.status_code == 201, response.text
    row = response.json()
    assert row["original_filename"] == "화면.png"
    assert row["metadata"] == values["metadata"]
    assert row["file_hash"] == hashlib.sha256(data).hexdigest()
    assert row["size_bytes"] == len(data)
    assert "storage_key" not in row and "capture_metadata" not in row
    assert row["content_url"] == catalog["p"] + "/screenshots/" + row["id"] + "/content"
    detail = response.headers["location"]
    assert client.get(detail).json() == row
    content = client.get(row["content_url"])
    assert content.content == data
    assert content.headers["content-type"] == mime
    assert content.headers["x-content-type-options"] == "nosniff"
    assert client.get(detail + "/expected-strings").json()["total"] == 0
    filters = {key: row[key] for key in ("build_id", "locale_id", "category_id", "situation_id", "source")}
    assert client.get(catalog["p"] + "/screenshots", params=filters).json()["total"] == 1
    assert client.get(catalog["p"] + "/screenshots", params=dict(filters, offset=50)).json()["items"] == []
    assert client.get(catalog["p"] + "/screenshots", params=dict(filters, offset=50)).json()["total"] == 1
    other_build = created(client, catalog["p"] + "/builds", {"label": "other"})
    assert client.get(catalog["p"] + "/screenshots", params=dict(filters, build_id=other_build["id"])).json()["total"] == 0
    assert upload(client, catalog, values, data, mime=mime).json()["id"] != row["id"]
    assert client.get(catalog["p"] + "/screenshots").json()["items"][0]["id"] != row["id"]
    assert client.delete(catalog["p"] + "/builds/" + row["build_id"]).status_code == 409
    assert client.get(catalog["p"] + "/screenshots/" + str(uuid4())).status_code == 404
    assert client.get(catalog["p"] + "/screenshots?build_id=" + str(uuid4())).status_code == 404
    assert client.get(catalog["p"] + "/screenshots", params={"uploaded_to": row["uploaded_at"]}).json()["total"] == 0
    assert client.get(catalog["p"] + "/screenshots", params={"uploaded_from": row["uploaded_at"]}).json()["total"] == 2
    assert client.get(catalog["p"] + "/screenshots?uploaded_from=2026-01-01T00:00:00").status_code == 422


@pytest.mark.parametrize("value", [{"note": "\0"}, {"steps": [{"note": "\ud800"}]}, {"steps": [{"bad\udfff": "x"}]}, {"bad\0": "x"}, {"device": None}, {"resolution": {"width": True, "height": 8}}, {"resolution": {"width": 11, "height": 8}}, {"data": [[[[[[]]]]]]}, {"device": "x" * 201}], ids=["nul-value", "surrogate-value", "surrogate-key", "nul-key", "null-device", "bool-resolution", "wrong-resolution", "too-deep", "long-device"])
def test_invalid_metadata_never_publishes(client, catalog, value, monkeypatch):
    def forbidden(*args):
        pytest.fail("invalid metadata reached publication")
    monkeypatch.setattr(client.storage, "publish", forbidden)
    response = upload(client, catalog, metadata(catalog, metadata=value))
    assert response.status_code == 422, response.text
    assert not client.storage.list_objects()
    assert not client.storage.list_staging()
    with client.factory() as session:
        assert session.scalar(select(func.count()).select_from(Screenshot).where(Screenshot.project_id == catalog["project"]["id"])) == 0


def raw_upload(client, catalog, filename=b"image.png", raw_metadata=None):
    raw_metadata = raw_metadata if raw_metadata is not None else json.dumps(metadata(catalog)).encode()
    body = b'--boundary\r\nContent-Disposition: form-data; name="file"; filename="' + filename + b'"\r\nContent-Type: image/png\r\n\r\n' + image_bytes() + b'\r\n--boundary\r\nContent-Disposition: form-data; name="metadata"\r\n\r\n' + raw_metadata + b'\r\n--boundary--\r\n'
    return client.post(catalog["p"] + "/screenshots", content=body, headers={"Content-Type": "multipart/form-data; boundary=boundary"})


@pytest.mark.parametrize("filename", [b"before\0/image.png", b"C:\\before\0\\image.png", b"bad\xff.png"])
def test_filename_unicode_before_sanitization(client, catalog, filename, monkeypatch):
    monkeypatch.setattr(client.storage, "publish", lambda *args: pytest.fail("published invalid filename"))
    response = raw_upload(client, catalog, filename)
    assert response.status_code == 422, response.text
    assert response.json()["error"]["details"][0]["field"] == "file.filename"


@pytest.mark.parametrize("data,mime,status", [(b"", "image/png", 422), (b"invalid", "image/png", 422), (image_bytes()[:-20], "image/png", 422), (image_bytes(), "image/jpeg", 415), (b"GIF89a", "image/gif", 415), (b"x" * 20_971_521, "image/png", 413)], ids=["empty", "corrupt", "truncated", "mime-mismatch", "unsupported", "file-too-large"])
def test_upload_file_validation(client, catalog, data, mime, status):
    response = upload(client, catalog, data=data, mime=mime)
    assert response.status_code == status, response.text
    assert not client.storage.list_objects()


def test_scope_form_and_time_filters(client, catalog):
    extra_category = created(client, catalog["p"] + "/categories", {"slug": "other", "name": "Other"})
    values = metadata(catalog)
    values["category_id"] = extra_category["id"]
    assert upload(client, catalog, values).json()["error"]["code"] == "RELATIONSHIP_MISMATCH"
    values["build_id"] = str(uuid4())
    assert upload(client, catalog, values).status_code == 404
    for extra in ({"client_upload_id": str(uuid4())}, {"source": "agent"}):
        values = metadata(catalog)
        values.update(extra)
        assert upload(client, catalog, values).status_code == 422
    path = catalog["p"] + "/screenshots"
    assert client.post(path, files={"file": ("image.png", image_bytes(), "image/png")}).status_code == 422
    assert client.post(path, content=b"bad", headers={"Content-Type": "multipart/form-data; boundary=boundary"}).status_code == 400
    assert raw_upload(client, catalog, raw_metadata=b'{"note":"\xff"}').status_code == 422
    assert client.get(path, params={"category_id": extra_category["id"], "situation_id": catalog["situation"]["id"]}).status_code == 422
    assert client.get(path, params={"uploaded_from": "2026-09-06T01:00:00Z", "uploaded_to": "2026-09-06T00:00:00Z"}).status_code == 422
    assert client.post(path, content=b"x" * 22_020_097, headers={"Content-Type": "multipart/form-data; boundary=x"}).status_code == 413


def test_storage_failure_and_missing_content(client, catalog, monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(client.storage, "publish", lambda *args: (_ for _ in ()).throw(OSError("disk unavailable")))
        response = upload(client, catalog)
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "STORAGE_UNAVAILABLE"
        assert response.headers["retry-after"] == "5"
    response = upload(client, catalog)
    assert response.status_code == 201, response.text
    client.storage.delete(client.storage.list_objects()[0].key)
    assert client.get(response.json()["content_url"]).status_code == 503
    assert client.get(response.headers["location"]).status_code == 200


@pytest.mark.parametrize(
    "mutation,expected_status",
    [
        ("normal", 200),
        ("missing", 503),
        ("length-changed", 503),
        ("same-length-changed", 503),
    ],
)
def test_content_read_verifies_returned_bytes_and_preserves_state(
    client, catalog, monkeypatch, mutation, expected_status
):
    data = image_bytes()
    values = agent_metadata(catalog, data=data)
    uploaded = upload(client, catalog, values, data)
    assert uploaded.status_code == 201, uploaded.text

    stored = client.storage.list_objects()[0]
    object_path = client.storage.root / stored.key
    expected_object = data
    if mutation == "missing":
        object_path.unlink()
        expected_object = None
    elif mutation == "length-changed":
        expected_object = data + b"x"
        object_path.write_bytes(expected_object)
    elif mutation == "same-length-changed":
        changed = bytearray(data)
        changed[-1] ^= 1
        expected_object = bytes(changed)
        object_path.write_bytes(expected_object)

    open_calls = 0
    original_open_read = client.storage.open_read

    def counted_open_read(key):
        nonlocal open_calls
        open_calls += 1
        return original_open_read(key)

    monkeypatch.setattr(client.storage, "open_read", counted_open_read)
    response = client.get(uploaded.json()["content_url"])
    assert response.status_code == expected_status, response.text
    assert open_calls == 1
    if expected_status == 200:
        assert response.content == data
    else:
        assert response.json()["error"]["code"] == "STORAGE_UNAVAILABLE"

    screenshot_id = UUID(uploaded.json()["id"])
    project_id = UUID(catalog["project"]["id"])
    client_upload_id = UUID(values["client_upload_id"])
    with client.factory() as session:
        screenshot = session.get(Screenshot, screenshot_id)
        receipt = session.get(UploadReceipt, (project_id, client_upload_id))
        assert screenshot is not None
        assert screenshot.file_hash == hashlib.sha256(data).hexdigest()
        assert receipt is not None
        assert receipt.state == "COMPLETED"
        assert receipt.screenshot_id == screenshot_id

    if expected_object is None:
        assert not object_path.exists()
    else:
        assert object_path.read_bytes() == expected_object


def test_known_rollback_compensates(client, catalog, monkeypatch):
    def fail(*args):
        raise OperationalError("injected insert failure", {}, Exception())
    monkeypatch.setattr("backend.app.repositories.catalog.insert", fail)
    response = upload(client, catalog)
    assert response.status_code == 503
    assert client.storage.list_objects() == []


@pytest.mark.parametrize("actually_committed", [False, True])
def test_ambiguous_commit_never_deletes(client, catalog, monkeypatch, actually_committed):
    original = Session.commit
    def uncertain(session):
        if actually_committed:
            original(session)
        raise OperationalError("ambiguous commit", {}, Exception())
    monkeypatch.setattr(Session, "commit", uncertain)
    response = upload(client, catalog)
    assert response.status_code == (201 if actually_committed else 503), response.text
    assert len(client.storage.list_objects()) == 1


def test_agent_first_replay_conflict_and_hash_non_dedup(client, catalog):
    data = image_bytes()
    upload_id = uuid4()
    values = agent_metadata(
        catalog,
        upload_id,
        data,
        metadata={"device": "에이전트 😀", "note": "e\u0301"},
    )

    first = upload(client, catalog, values, data)
    assert first.status_code == 201, first.text
    assert first.headers["idempotency-replayed"] == "false"
    assert first.json()["client_upload_id"] == str(upload_id)
    assert first.json()["source"] == "agent"

    replay = upload(client, catalog, values, data)
    assert replay.status_code == 200, replay.text
    assert replay.headers["idempotency-replayed"] == "true"
    assert replay.headers["location"] == first.headers["location"]
    assert replay.json() == first.json()

    conflict_values = dict(values, metadata={"device": "changed"})
    conflict = upload(client, catalog, conflict_values, data)
    assert conflict.status_code == 409, conflict.text
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert "retry-after" not in conflict.headers

    distinct = upload(client, catalog, agent_metadata(catalog, data=data), data)
    assert distinct.status_code == 201, distinct.text
    assert distinct.json()["id"] != first.json()["id"]
    assert distinct.json()["file_hash"] == first.json()["file_hash"]

    with client.factory() as session:
        project_id = catalog["project"]["id"]
        assert session.scalar(select(func.count()).select_from(Screenshot).where(Screenshot.project_id == project_id)) == 2
        assert session.scalar(select(func.count()).select_from(UploadReceipt).where(UploadReceipt.project_id == project_id)) == 2
    assert len(client.storage.list_objects()) == 2


def test_agent_hash_assertion_and_duplicate_keys_never_reserve(client, catalog):
    values = agent_metadata(catalog)
    values["expected_file_hash"] = "0" * 64
    mismatch = upload(client, catalog, values)
    assert mismatch.status_code == 422, mismatch.text

    raw = json.dumps(agent_metadata(catalog), ensure_ascii=False)
    raw = raw.replace('"metadata_version": 1,', '') if '"metadata_version": 1,' in raw else raw
    raw = raw[:-1] + ',"metadata":{"a":1,"a":2}}'
    duplicate = raw_upload(client, catalog, raw_metadata=raw.encode("utf-8"))
    assert duplicate.status_code == 422, duplicate.text

    with client.factory() as session:
        project_id = catalog["project"]["id"]
        assert session.scalar(select(func.count()).select_from(Screenshot).where(Screenshot.project_id == project_id)) == 0
        assert session.scalar(select(func.count()).select_from(UploadReceipt).where(UploadReceipt.project_id == project_id)) == 0
    assert client.storage.list_objects() == []


def test_lease_keeper_resolves_fenced_owner_from_fresh_receipt(monkeypatch):
    called = threading.Event()
    fence = AttemptFence(
        uuid4(), uuid4(), "a" * 64, 1, uuid4(), uuid4(),
        f"objects/{uuid4()}/{uuid4()}.png",
        datetime.now(timezone.utc),
    )
    replay = UploadOutcome({"id": str(uuid4())}, 200, True)

    def lost(*args, **kwargs):
        called.set()
        return False

    monkeypatch.setattr(upload_receipts, "RENEW_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr(upload_receipts, "renew_attempt", lost)
    monkeypatch.setattr(upload_receipts, "recover_finalize_commit", lambda *args: replay)
    keeper = LeaseKeeper(object(), fence, object(), object())
    keeper.start()
    assert called.wait(1)
    assert keeper.stop_and_join() is replay


def test_lease_keeper_propagates_fresh_lease_delay(monkeypatch):
    called = threading.Event()
    fence = AttemptFence(
        uuid4(), uuid4(), "a" * 64, 1, uuid4(), uuid4(),
        f"objects/{uuid4()}/{uuid4()}.png",
        datetime.now(timezone.utc),
    )

    def lost(*args, **kwargs):
        called.set()
        return False

    def busy(*args):
        raise DomainError(409, "UPLOAD_IN_PROGRESS", "Upload in progress", retry_after=7)

    monkeypatch.setattr(upload_receipts, "RENEW_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr(upload_receipts, "renew_attempt", lost)
    monkeypatch.setattr(upload_receipts, "recover_finalize_commit", busy)
    keeper = LeaseKeeper(object(), fence, object(), object())
    keeper.start()
    assert called.wait(1)
    with pytest.raises(DomainError) as caught:
        keeper.stop_and_join()
    assert caught.value.code == "UPLOAD_IN_PROGRESS"
    assert caught.value.retry_after == 7


def test_concurrent_agent_request_has_one_owner_and_lease_delay(client, catalog, monkeypatch):
    data = image_bytes()
    values = agent_metadata(catalog, data=data)
    entered = threading.Event()
    release = threading.Event()
    original_publish = client.storage.publish

    def blocked_publish(*args, **kwargs):
        entered.set()
        assert release.wait(3)
        return original_publish(*args, **kwargs)

    monkeypatch.setattr(client.storage, "publish", blocked_publish)
    with ThreadPoolExecutor(max_workers=1) as pool:
        owner = pool.submit(upload, client, catalog, values, data)
        assert entered.wait(3)
        competitor = upload(client, catalog, values, data)
        assert competitor.status_code == 409, competitor.text
        assert competitor.json()["error"]["code"] == "UPLOAD_IN_PROGRESS"
        assert int(competitor.headers["retry-after"]) > 0
        release.set()
        first = owner.result(timeout=3)

    assert first.status_code == 201, first.text
    replay = upload(client, catalog, values, data)
    assert replay.status_code == 200, replay.text
    assert replay.json()["id"] == first.json()["id"]
