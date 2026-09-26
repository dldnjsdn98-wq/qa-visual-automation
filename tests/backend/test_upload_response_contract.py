"""HTTP upload contract checks that never open a database connection."""

import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.api.dependencies import get_session, get_storage
from backend.app.errors import DomainError
from backend.app.main import app
from backend.app.schemas.screenshots import AgentScreenshotUpload, Screenshot, ScreenshotUpload
from backend.app.services.upload_types import UploadOutcome


def agent_metadata():
    return {
        "upload_protocol_version": 1,
        "client_upload_id": str(uuid4()),
        "build_id": str(uuid4()),
        "locale_id": str(uuid4()),
        "category_id": str(uuid4()),
        "situation_id": str(uuid4()),
        "source": "agent",
        "metadata_version": 1,
        "metadata": {},
    }


def screenshot(metadata, project_id):
    return {
        "id": uuid4(),
        "project_id": project_id,
        "build_id": metadata["build_id"],
        "locale_id": metadata["locale_id"],
        "category_id": metadata["category_id"],
        "situation_id": metadata["situation_id"],
        "source": metadata["source"],
        "original_filename": "image.png",
        "uploaded_at": datetime.now(timezone.utc),
        "file_hash": "a" * 64,
        "media_type": "image/png",
        "size_bytes": 3,
        "width": 1,
        "height": 1,
        "metadata_version": 1,
        "metadata": {},
        "client_upload_id": metadata.get("client_upload_id"),
        "content_url": f"/api/v1/projects/{project_id}/screenshots/content",
    }


@pytest.fixture
def isolated_client():
    app.dependency_overrides[get_session] = lambda: object()
    app.dependency_overrides[get_storage] = lambda: object()
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def send(client, project_id, values, headers=None):
    return client.post(
        f"/api/v1/projects/{project_id}/screenshots",
        files={
            "file": ("image.png", b"abc", "image/png"),
            "metadata": (None, json.dumps(values), "application/json"),
        },
        headers=headers,
    )


def test_agent_schema_presence_null_and_closed_fields():
    values = agent_metadata()
    assert AgentScreenshotUpload.model_validate(values).expected_file_hash is None
    assert AgentScreenshotUpload.model_validate(dict(values, expected_file_hash="a" * 64)).expected_file_hash == "a" * 64
    for bad in (
        dict(values, client_upload_id=None),
        {key: value for key, value in values.items() if key != "client_upload_id"},
        dict(values, expected_file_hash=None),
        dict(values, expected_file_hash="A" * 64),
        dict(values, unexpected=True),
    ):
        with pytest.raises(ValidationError):
            AgentScreenshotUpload.model_validate(bad)
    manual = {key: values[key] for key in ("build_id", "locale_id", "category_id", "situation_id")}
    manual["source"] = "manual"
    assert ScreenshotUpload.model_validate(manual).source == "manual"
    for key in ("client_upload_id", "expected_file_hash", "upload_protocol_version"):
        with pytest.raises(ValidationError):
            ScreenshotUpload.model_validate(dict(manual, **{key: None}))


def test_header_presence_has_fixed_422_even_before_multipart(isolated_client):
    project_id = uuid4()
    for value in ("", "invalid", str(uuid4())):
        response = isolated_client.post(
            f"/api/v1/projects/{project_id}/screenshots",
            content=b"invalid multipart",
            headers={"Content-Type": "multipart/form-data; boundary=x", "Idempotency-Key": value},
        )
        assert response.status_code == 422
        assert response.json()["error"]["details"] == [{"field": "body", "reason": "Idempotency-Key is not supported; use client_upload_id for agent uploads"}]
    response = isolated_client.post(
        f"/api/v1/projects/{project_id}/screenshots",
        content=b"invalid",
        headers={"Content-Type": "application/json", "Idempotency-Key": "x"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "body"


def test_first_replay_manual_and_error_headers(isolated_client, monkeypatch):
    project_id = uuid4()
    values = agent_metadata()
    row = screenshot(values, project_id)
    calls = iter((UploadOutcome(row, 201, False), UploadOutcome(row, 200, True)))
    monkeypatch.setattr("backend.app.api.v1.screenshots.service.upload", lambda *args: next(calls))
    first = send(isolated_client, project_id, values)
    replay = send(isolated_client, project_id, values)
    assert (first.status_code, first.headers["idempotency-replayed"]) == (201, "false")
    assert (replay.status_code, replay.headers["idempotency-replayed"]) == (200, "true")
    assert first.headers["location"] == replay.headers["location"]
    assert first.json() == replay.json()
    assert first.headers["x-request-id"] != replay.headers["x-request-id"]

    manual = dict(values, source="manual")
    for key in ("upload_protocol_version", "client_upload_id"):
        manual.pop(key)
    manual_row = screenshot(manual, project_id)
    monkeypatch.setattr("backend.app.api.v1.screenshots.service.upload", lambda *args: UploadOutcome(manual_row, 201, None))
    manual_response = send(isolated_client, project_id, manual)
    assert manual_response.status_code == 201
    assert "idempotency-replayed" not in manual_response.headers
    assert manual_response.json()["client_upload_id"] is None

    for error, status, retry in (
        (DomainError(409, "IDEMPOTENCY_CONFLICT", "Conflict"), 409, None),
        (DomainError(409, "UPLOAD_IN_PROGRESS", "Busy", retry_after=7), 409, "7"),
        (DomainError(503, "DATABASE_UNAVAILABLE", "Unavailable"), 503, "5"),
    ):
        def raise_error(*args):
            raise error
        monkeypatch.setattr("backend.app.api.v1.screenshots.service.upload", raise_error)
        response = send(isolated_client, project_id, values)
        assert response.status_code == status
        assert response.json()["error"]["code"] == error.code
        assert response.headers.get("retry-after") == retry
        assert "idempotency-replayed" not in response.headers


def test_source_filter_and_cors_contract(isolated_client, monkeypatch):
    schema = app.openapi()
    path = schema["paths"]["/api/v1/projects/{project_id}/screenshots"]
    assert "200" in path["post"]["responses"]
    assert "Idempotency-Replayed" not in schema["paths"]["/api/v1/projects"]["post"]["responses"]["201"]["headers"]
    content_schema = path["post"]["requestBody"]["content"]["multipart/form-data"]["schema"]["properties"]["metadata"]["contentSchema"]
    assert {item["$ref"] for item in content_schema["oneOf"]} == {"#/components/schemas/ScreenshotUpload", "#/components/schemas/AgentScreenshotUpload"}
    assert "null" not in json.dumps(schema["components"]["schemas"]["AgentScreenshotUpload"]["properties"]["expected_file_hash"])
    assert set(Screenshot.model_fields["source"].annotation.__args__) == {"manual", "agent", "automation"}
    monkeypatch.setattr("backend.app.api.v1.screenshots.validate_references", lambda *args, **kwargs: None)
    monkeypatch.setattr("backend.app.api.v1.screenshots.repo.page", lambda *args, **kwargs: ([], 0))
    for source in ("manual", "agent", "automation"):
        response = isolated_client.get(f"/api/v1/projects/{uuid4()}/screenshots", params={"source": source})
        assert response.status_code == 200
    response = isolated_client.get("/health", headers={"Origin": "http://localhost:3001"})
    exposed = {part.strip().lower() for part in response.headers["access-control-expose-headers"].split(",")}
    assert {"location", "x-request-id", "retry-after", "idempotency-replayed"} <= exposed
