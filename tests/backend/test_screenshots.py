import hashlib
import io
import json
from uuid import uuid4
import pytest
from PIL import Image
from sqlalchemy import select, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from backend.app.models import Screenshot
from conftest import created


def image_bytes(kind="PNG"):
    stream = io.BytesIO()
    Image.new("RGB", (12, 8), (14, 35, 75)).save(stream, format=kind)
    return stream.getvalue()


def metadata(catalog, **extra):
    return dict(build_id=catalog["build"]["id"], locale_id=catalog["locale"]["id"], category_id=catalog["category"]["id"], situation_id=catalog["situation"]["id"], source="manual", **extra)


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
