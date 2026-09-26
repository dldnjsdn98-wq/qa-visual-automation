"""Contract-facing API regression tests for Phase 3 OCR runs.

These tests deliberately exercise the HTTP boundary only.  They assume the
Phase 3 test deployment registers at least one AVAILABLE disposable profile
through the profile registry; no profile is inserted through a public API.
The OCR runner is not required for creation/snapshot tests and is expected to
leave newly-created runs pending for result-not-ready assertions.
"""

import io
import hashlib
import json
from datetime import datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
import rfc8785
from PIL import Image

from backend.app.services import verification_runs
from backend.app.errors import DomainError
from conftest import created


@pytest.fixture(autouse=True)
def disposable_profile_registry(monkeypatch):
    """Inject a synthetic exact admission predicate, never qualification evidence."""
    manifest = {
        "adapter_version": 1,
        "profile_id": "api-fixture-" + uuid4().hex,
        "production_eligible": True,
        "engine": {
            "name": "fixture-engine",
            "version": "1",
            "packages": [],
            "native_packages": [],
        },
        "models": ["fixture-model"],
        "artifacts": [],
        "coordinate_space": "original-raster-v1",
        "normalization_version": "norm-v1",
        "matching_version": "one-to-one-levenshtein-v1",
        "unicode_version": "15.0.0",
        "rapidfuzz_version": "3.14.6",
        "language_map": {
            "version": "api-fixture-map-v1",
            "aliases": [{"input": "ja", "family": "ja"}, {"input": "ja-JP", "family": "ja"}],
        },
        "preprocessing": {
            "exif_policy": "ignored-v1",
            "document_orientation": False,
            "image_unwarping": False,
            "textline_orientation": False,
            "steps": ["identity"],
        },
        "engine_options": [],
        "runtime_policy": {
            "python": "3.12",
            "device": "cpu",
            "numeric_mode": "fp32",
            "thread_count": 1,
            "network_allowed": False,
        },
        "qualification": {
            "status": "QUALIFIED",
            "unavailable_code": None,
            "platforms": ["fixture-only"],
            "evidence_sha256": [],
        },
    }
    canonical = rfc8785.dumps(manifest)
    document = SimpleNamespace(
        profile_id=manifest["profile_id"],
        canonical_bytes=canonical,
        sha256=hashlib.sha256(canonical).hexdigest(),
        manifest=manifest,
        availability="AVAILABLE",
        unavailable_code=None,
        production_eligible=True,
    )
    state = SimpleNamespace(enabled=True, digest=document.sha256)
    snapshot = SimpleNamespace(
        admitted=lambda profile_id, profile_digest: (
            state.enabled
            and profile_id == document.profile_id
            and profile_digest == state.digest
        )
    )
    monkeypatch.setattr(verification_runs, "_profile_documents", lambda: {document.profile_id: document})
    monkeypatch.setattr(
        verification_runs,
        "load_admission_snapshot",
        lambda: snapshot if state.enabled else None,
    )
    state.document = document
    return state


def _image_bytes():
    stream = io.BytesIO()
    Image.new("RGB", (12, 8), (14, 35, 75)).save(stream, format="PNG")
    return stream.getvalue()


def _screenshot_metadata(catalog):
    return {
        "build_id": catalog["build"]["id"],
        "locale_id": catalog["locale"]["id"],
        "category_id": catalog["category"]["id"],
        "situation_id": catalog["situation"]["id"],
        "source": "manual",
    }


def _upload(client, catalog):
    data = _image_bytes()
    response = client.post(
        catalog["p"] + "/screenshots",
        files={
            "file": ("ocr-api.png", data, "image/png"),
            "metadata": (None, json.dumps(_screenshot_metadata(catalog)), "application/json"),
        },
    )
    assert response.status_code == 201, response.text
    return response.json(), data


def _run_path(screenshot, run_id=None):
    path = screenshot["content_url"].removesuffix("/content") + "/verification-runs"
    return path if run_id is None else f"{path}/{run_id}"


def _run_body(profile_id, *, client_run_id=None, verification=None, **extra):
    body = {
        "protocol_version": 1,
        "client_run_id": str(client_run_id or uuid4()),
        "profile_id": profile_id,
    }
    if verification is not None:
        body["verification"] = verification
    body.update(extra)
    return body


def _replace_fixture_manifest(state, manifest):
    canonical = rfc8785.dumps(manifest)
    digest = hashlib.sha256(canonical).hexdigest()
    state.document.manifest = manifest
    state.document.canonical_bytes = canonical
    state.document.sha256 = digest
    state.document.production_eligible = manifest.get("production_eligible") is True
    state.digest = digest


@pytest.fixture
def available_profile(client, catalog):
    response = client.get(catalog["p"] + "/ocr-profiles")
    assert response.status_code == 200, response.text
    profiles = response.json()["items"]
    available = [item for item in profiles if item["availability"] == "AVAILABLE"]
    if not available:
        pytest.fail(
            "Phase 3 API tests require an AVAILABLE disposable profile in the "
            "test registry; profile qualification is outside this API slice"
        )
    return sorted(available, key=lambda item: item["profile_id"])[0]["profile_id"]


@pytest.fixture
def screenshot(client, catalog):
    row, data = _upload(client, catalog)
    return {"row": row, "data": data, "catalog": catalog}


@pytest.fixture
def expected_screenshot(client, catalog):
    project_path = catalog["p"]
    present_key = created(client, project_path + "/string-keys", {"string_id": "ocr.present"})
    empty_key = created(client, project_path + "/string-keys", {"string_id": "ocr.empty"})
    missing_key = created(client, project_path + "/string-keys", {"string_id": "ocr.missing"})
    created(
        client,
        project_path + "/strings",
        {
            "build_id": catalog["build"]["id"],
            "locale_id": catalog["locale"]["id"],
            "string_id": "ocr.present",
            "text": "before",
        },
    )
    created(
        client,
        project_path + "/strings",
        {
            "build_id": catalog["build"]["id"],
            "locale_id": catalog["locale"]["id"],
            "string_id": "ocr.empty",
            "text": "",
        },
    )
    mapping = (
        project_path
        + "/situations/"
        + catalog["situation"]["id"]
        + "/expected-string-keys?build_id="
        + catalog["build"]["id"]
    )
    response = client.put(
        mapping,
        json={"string_ids": ["ocr.present", "ocr.empty", "ocr.missing"]},
    )
    assert response.status_code == 200, response.text
    row, data = _upload(client, catalog)
    return {
        "row": row,
        "data": data,
        "catalog": catalog,
        "keys": {"present": present_key, "empty": empty_key, "missing": missing_key},
    }


def _assert_page_shape(response):
    assert response.status_code == 200, response.text
    payload = response.json()
    assert set(("items", "total", "limit", "offset")) <= payload.keys()
    assert isinstance(payload["items"], list)
    return payload


def test_profile_manifest_object_must_match_its_canonical_bytes():
    canonical_manifest = {"profile_id": "canonical-profile", "availability": "UNAVAILABLE"}
    canonical = rfc8785.dumps(canonical_manifest)
    document = SimpleNamespace(
        profile_id="canonical-profile",
        canonical_bytes=canonical,
        sha256=hashlib.sha256(canonical).hexdigest(),
        manifest={"profile_id": "different-profile", "availability": "AVAILABLE"},
    )

    with pytest.raises(DomainError) as caught:
        verification_runs._manifest(document)

    assert caught.value.code == "OCR_PROFILE_UNAVAILABLE"


def test_profile_list_is_scoped_deterministic_and_safe(client, catalog):
    response = client.get(catalog["p"] + "/ocr-profiles", headers={"Origin": "http://localhost:3001"})
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert [item["profile_id"] for item in items] == sorted(item["profile_id"] for item in items)
    required = {
        "profile_id",
        "profile_digest",
        "engine_name",
        "engine_version",
        "model_ids",
        "language_tags",
        "coordinate_space",
        "normalization_version",
        "matching_version",
        "availability",
        "unavailable_code",
    }
    for item in items:
        assert required <= item.keys()
        assert item["coordinate_space"] == "original-raster-v1"
        assert item["availability"] in {"AVAILABLE", "UNAVAILABLE"}
        assert not {"path", "install_path", "credentials", "model_url"} & item.keys()


def test_list_and_fresh_create_share_exact_admission(
    client, catalog, screenshot, disposable_profile_registry, monkeypatch
):
    state = disposable_profile_registry
    state.enabled = False
    loads = []
    monkeypatch.setattr(
        verification_runs,
        "load_admission_snapshot",
        lambda: loads.append("loaded"),
    )

    profiles = client.get(catalog["p"] + "/ocr-profiles")
    assert profiles.status_code == 200, profiles.text
    assert loads == ["loaded"]
    item = next(row for row in profiles.json()["items"] if row["profile_id"] == state.document.profile_id)
    assert item["availability"] == "UNAVAILABLE"
    assert item["unavailable_code"] == "UNQUALIFIED_RUNTIME"

    response = client.post(
        _run_path(screenshot["row"]),
        json=_run_body(state.document.profile_id),
    )
    assert response.status_code == 503, response.text
    assert response.headers["retry-after"] == "5"
    assert response.json()["error"]["code"] == "OCR_PROFILE_UNAVAILABLE"
    assert loads == ["loaded", "loaded"]


def test_admission_digest_mismatch_is_unavailable(
    client, catalog, screenshot, disposable_profile_registry
):
    state = disposable_profile_registry
    state.digest = "b" * 64

    profiles = client.get(catalog["p"] + "/ocr-profiles")
    item = next(row for row in profiles.json()["items"] if row["profile_id"] == state.document.profile_id)
    assert item["availability"] == "UNAVAILABLE"

    response = client.post(
        _run_path(screenshot["row"]),
        json=_run_body(state.document.profile_id),
    )
    assert response.status_code == 503, response.text
    assert response.headers["retry-after"] == "5"


def test_api_local_profile_availability_cannot_override_shared_admission(
    client, catalog, screenshot, disposable_profile_registry
):
    state = disposable_profile_registry
    state.document.availability = "UNAVAILABLE"
    state.document.unavailable_code = "UNQUALIFIED_RUNTIME"

    profiles = client.get(catalog["p"] + "/ocr-profiles")
    assert profiles.status_code == 200, profiles.text
    item = next(row for row in profiles.json()["items"] if row["profile_id"] == state.document.profile_id)
    assert item["availability"] == "AVAILABLE"
    assert item["unavailable_code"] is None

    response = client.post(
        _run_path(screenshot["row"]),
        json=_run_body(state.document.profile_id),
    )
    assert response.status_code == 202, response.text


def test_true_admission_cannot_override_immutable_unqualified_status(
    client, catalog, screenshot, disposable_profile_registry
):
    state = disposable_profile_registry
    manifest = dict(state.document.manifest)
    manifest["qualification"] = dict(
        manifest["qualification"],
        status="UNQUALIFIED",
        unavailable_code="UNQUALIFIED_RUNTIME",
    )
    _replace_fixture_manifest(state, manifest)
    state.document.availability = "AVAILABLE"
    state.document.unavailable_code = None

    profiles = client.get(catalog["p"] + "/ocr-profiles")
    assert profiles.status_code == 200, profiles.text
    item = next(row for row in profiles.json()["items"] if row["profile_id"] == state.document.profile_id)
    assert item["availability"] == "UNAVAILABLE"
    assert item["unavailable_code"] == "UNQUALIFIED_RUNTIME"

    response = client.post(
        _run_path(screenshot["row"]),
        json=_run_body(state.document.profile_id),
    )
    assert response.status_code == 503, response.text
    assert response.headers["retry-after"] == "5"


@pytest.mark.parametrize("eligibility_source", ["canonical", "document"])
def test_true_admission_cannot_override_non_production_document(
    client, catalog, screenshot, disposable_profile_registry, eligibility_source
):
    state = disposable_profile_registry
    if eligibility_source == "canonical":
        manifest = dict(state.document.manifest)
        manifest["production_eligible"] = False
        _replace_fixture_manifest(state, manifest)
        state.document.production_eligible = True
    else:
        state.document.production_eligible = False
    state.document.availability = "AVAILABLE"

    profiles = client.get(catalog["p"] + "/ocr-profiles")
    item = next(row for row in profiles.json()["items"] if row["profile_id"] == state.document.profile_id)
    assert item["availability"] == "UNAVAILABLE"

    response = client.post(
        _run_path(screenshot["row"]),
        json=_run_body(state.document.profile_id),
    )
    assert response.status_code == 503, response.text
    assert response.headers["retry-after"] == "5"


@pytest.mark.parametrize("invalid_document", ["absent_status", "malformed_status", "tampered"])
def test_true_admission_cannot_override_invalid_immutable_document(
    client, catalog, screenshot, disposable_profile_registry, invalid_document
):
    state = disposable_profile_registry
    if invalid_document in {"absent_status", "malformed_status"}:
        manifest = dict(state.document.manifest)
        qualification = dict(manifest["qualification"])
        if invalid_document == "absent_status":
            del qualification["status"]
        else:
            qualification["status"] = {"invalid": True}
        manifest["qualification"] = qualification
        _replace_fixture_manifest(state, manifest)
    else:
        state.document.sha256 = "0" * 64

    profiles = client.get(catalog["p"] + "/ocr-profiles")
    assert profiles.status_code == 200, profiles.text
    assert all(
        item["profile_id"] != state.document.profile_id
        for item in profiles.json()["items"]
    )

    response = client.post(
        _run_path(screenshot["row"]),
        json=_run_body(state.document.profile_id),
    )
    assert response.status_code == 503, response.text
    assert response.headers["retry-after"] == "5"


@pytest.mark.parametrize("invalid_document", ["absent_status", "malformed_status", "tampered"])
def test_invalid_current_document_preserves_historical_profile_run_and_replay(
    client, catalog, screenshot, disposable_profile_registry, invalid_document
):
    state = disposable_profile_registry
    client_run_id = uuid4()
    path = _run_path(screenshot["row"])
    body = _run_body(state.document.profile_id, client_run_id=client_run_id)
    created_run = client.post(path, json=body)
    assert created_run.status_code == 202, created_run.text
    run_id = created_run.json()["id"]
    historical_digest = created_run.json()["profile_digest"]

    if invalid_document in {"absent_status", "malformed_status"}:
        manifest = dict(state.document.manifest)
        qualification = dict(manifest["qualification"])
        if invalid_document == "absent_status":
            del qualification["status"]
        else:
            qualification["status"] = {"invalid": True}
        manifest["qualification"] = qualification
        _replace_fixture_manifest(state, manifest)
    else:
        state.document.sha256 = "0" * 64

    profiles = client.get(catalog["p"] + "/ocr-profiles")
    assert profiles.status_code == 200, profiles.text
    historical_profile = next(
        item for item in profiles.json()["items"]
        if item["profile_id"] == state.document.profile_id
    )
    assert historical_profile["availability"] == "UNAVAILABLE"

    history = client.get(_run_path(screenshot["row"], run_id))
    assert history.status_code == 200, history.text
    assert history.json()["profile_digest"] == historical_digest

    replay = client.post(path, json=body)
    assert replay.status_code == 200, replay.text
    assert replay.json()["id"] == run_id
    assert replay.headers["idempotency-replayed"] == "true"

    fresh = client.post(path, json=_run_body(state.document.profile_id))
    assert fresh.status_code == 503, fresh.text
    assert fresh.headers["retry-after"] == "5"


def test_unready_retry_reuses_unreserved_client_id(
    client, screenshot, disposable_profile_registry
):
    state = disposable_profile_registry
    client_run_id = uuid4()
    path = _run_path(screenshot["row"])
    body = _run_body(state.document.profile_id, client_run_id=client_run_id)
    state.enabled = False

    unavailable = client.post(path, json=body)
    assert unavailable.status_code == 503, unavailable.text
    assert unavailable.headers["retry-after"] == "5"

    state.enabled = True
    created_run = client.post(path, json=body)
    assert created_run.status_code == 202, created_run.text
    assert created_run.headers["idempotency-replayed"] == "false"


def test_unknown_profile_is_422_before_admission(client, screenshot, monkeypatch):
    calls = []
    monkeypatch.setattr(verification_runs, "_profile_documents", lambda: {})
    monkeypatch.setattr(
        verification_runs,
        "load_admission_snapshot",
        lambda: calls.append("loaded"),
    )

    response = client.post(
        _run_path(screenshot["row"]),
        json=_run_body("never-registered-profile"),
    )
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "OCR_PROFILE_UNKNOWN"
    assert calls == []


def test_create_replay_and_same_id_conflict_have_contract_headers(client, screenshot, available_profile):
    row = screenshot["row"]
    run_id = uuid4()
    body = _run_body(available_profile, client_run_id=run_id)
    path = _run_path(row)

    first = client.post(path, json=body, headers={"Origin": "http://localhost:3001"})
    assert first.status_code == 202, first.text
    assert first.headers["location"].endswith(first.json()["id"])
    assert first.headers["retry-after"] == "2"
    assert first.headers["idempotency-replayed"] == "false"
    UUID(first.headers["x-request-id"])
    exposed = {part.strip().lower() for part in first.headers.get("access-control-expose-headers", "").split(",")}
    assert {"location", "retry-after", "idempotency-replayed", "x-request-id"} <= exposed

    replay = client.post(path, json=body)
    assert replay.status_code == 200, replay.text
    assert replay.json()["id"] == first.json()["id"]
    assert replay.headers["location"] == first.headers["location"]
    assert replay.headers["idempotency-replayed"] == "true"

    conflict = client.post(
        path,
        json=_run_body(
            available_profile,
            client_run_id=run_id,
            verification={"pass_threshold": 96, "review_threshold": 85},
        ),
    )
    assert conflict.status_code == 409, conflict.text
    assert conflict.json()["error"]["code"] == "RUN_IDEMPOTENCY_CONFLICT"


def test_replay_and_conflict_precede_removed_unready_profile(
    client, screenshot, available_profile, disposable_profile_registry, monkeypatch
):
    run_id = uuid4()
    path = _run_path(screenshot["row"])
    body = _run_body(available_profile, client_run_id=run_id)
    first = client.post(path, json=body)
    assert first.status_code == 202, first.text

    disposable_profile_registry.enabled = False
    monkeypatch.setattr(verification_runs, "_profile_documents", lambda: {})

    replay = client.post(path, json=body)
    assert replay.status_code == 200, replay.text
    assert replay.json()["id"] == first.json()["id"]
    assert replay.headers["idempotency-replayed"] == "true"

    conflict = client.post(
        path,
        json=_run_body(
            available_profile,
            client_run_id=run_id,
            verification={"pass_threshold": 96, "review_threshold": 85},
        ),
    )
    assert conflict.status_code == 409, conflict.text
    assert conflict.json()["error"]["code"] == "RUN_IDEMPOTENCY_CONFLICT"


def test_create_closed_body_and_header_validation_does_not_reserve_run(client, screenshot, available_profile):
    path = _run_path(screenshot["row"])
    run_id = uuid4()
    body = _run_body(available_profile, client_run_id=run_id)

    unknown_body = client.post(path, json=dict(body, unexpected=True))
    assert unknown_body.status_code == 422, unknown_body.text
    assert unknown_body.json()["error"]["code"] == "VALIDATION_ERROR"

    null_verification = client.post(path, json=dict(body, verification=None))
    assert null_verification.status_code == 422, null_verification.text

    forbidden_header = client.post(path, json=body, headers={"Idempotency-Key": "legacy"})
    assert forbidden_header.status_code == 422, forbidden_header.text

    valid = client.post(path, json=body)
    assert valid.status_code == 202, valid.text


def test_snapshot_is_immutable_while_current_catalog_changes(client, expected_screenshot, available_profile):
    row = expected_screenshot["row"]
    catalog = expected_screenshot["catalog"]
    body = _run_body(available_profile)
    created_run = client.post(_run_path(row), json=body)
    assert created_run.status_code == 202, created_run.text
    run_id = created_run.json()["id"]

    expected_path = _run_path(row, run_id) + "/expected"
    before = _assert_page_shape(client.get(expected_path))
    before_by_key = {item["string_id"]: item for item in before["items"]}
    assert before_by_key["ocr.present"]["expected_text"] == "before"
    assert before_by_key["ocr.empty"]["expected_text"] == ""
    assert before_by_key["ocr.empty"]["translation_status"] == "present"
    assert before_by_key["ocr.missing"]["expected_text"] is None
    assert before_by_key["ocr.missing"]["translation_status"] == "missing"

    string_path = catalog["p"] + "/strings/" + before_by_key["ocr.present"]["entry_id"]
    changed = client.patch(string_path, json={"text": "after"})
    assert changed.status_code == 200, changed.text

    snapshot = _assert_page_shape(client.get(expected_path))
    snapshot_by_key = {item["string_id"]: item for item in snapshot["items"]}
    assert snapshot_by_key["ocr.present"]["expected_text"] == "before"
    assert client.get(catalog["p"] + "/screenshots/" + row["id"] + "/expected-strings").json()["items"][0]["text"] == "after"

    new_run = client.post(_run_path(row), json=_run_body(available_profile))
    assert new_run.status_code == 202, new_run.text
    new_expected = _assert_page_shape(client.get(_run_path(row, new_run.json()["id"]) + "/expected"))
    assert {item["string_id"]: item for item in new_expected["items"]}["ocr.present"]["expected_text"] == "after"


def test_history_selection_order_and_pagination(client, screenshot, available_profile):
    row = screenshot["row"]
    run_ids = []
    for _ in range(3):
        response = client.post(_run_path(row), json=_run_body(available_profile))
        assert response.status_code == 202, response.text
        run_ids.append(response.json()["id"])

    all_runs = _assert_page_shape(client.get(_run_path(row) + "?selection=all&limit=100&offset=0"))
    assert all_runs["total"] >= 3
    assert all(run_id in {item["id"] for item in all_runs["items"]} for run_id in run_ids)
    ordered = [(datetime.fromisoformat(item["created_at"]), UUID(item["id"])) for item in all_runs["items"]]
    assert ordered == sorted(ordered, reverse=True)

    page_one = _assert_page_shape(client.get(_run_path(row) + "?limit=1&offset=0"))
    page_two = _assert_page_shape(client.get(_run_path(row) + "?limit=1&offset=1"))
    assert page_one["limit"] == page_two["limit"] == 1
    assert page_one["offset"] == 0 and page_two["offset"] == 1
    assert page_one["items"][0]["id"] != page_two["items"][0]["id"]

    succeeded = _assert_page_shape(client.get(_run_path(row) + "?selection=succeeded"))
    assert succeeded["total"] == 0
    assert succeeded["items"] == []
    assert client.get(_run_path(row) + "?selection=finished").status_code == 422
    assert client.get(_run_path(row) + "?unknown=1").status_code == 422


def test_result_resources_are_not_ready_before_completion(client, screenshot, available_profile):
    response = client.post(_run_path(screenshot["row"]), json=_run_body(available_profile))
    assert response.status_code == 202, response.text
    run_id = response.json()["id"]
    base = _run_path(screenshot["row"], run_id)

    for suffix in ("/ocr", "/verification", "/ocr/regions", "/verification/items"):
        result = client.get(base + suffix)
        assert result.status_code == 409, result.text
        assert result.json()["error"]["code"] == "RESULT_NOT_READY"
        assert result.json()["error"]["request_id"] == result.headers["x-request-id"]


def test_expected_and_result_pages_validate_closed_query_and_paging(client, expected_screenshot, available_profile):
    response = client.post(_run_path(expected_screenshot["row"]), json=_run_body(available_profile))
    assert response.status_code == 202, response.text
    base = _run_path(expected_screenshot["row"], response.json()["id"])

    expected = _assert_page_shape(client.get(base + "/expected?limit=2&offset=0"))
    assert expected["limit"] == 2 and expected["offset"] == 0
    for suffix in ("/expected", "/ocr/regions", "/verification/items"):
        assert client.get(base + suffix + "?limit=0").status_code == 422
        assert client.get(base + suffix + "?limit=101").status_code == 422
        assert client.get(base + suffix + "?offset=-1").status_code == 422
        assert client.get(base + suffix + "?unknown=1").status_code == 422


def test_scoped_ids_return_404_without_cross_project_leakage(client, catalog, screenshot, available_profile):
    foreign = created(client, "/api/v1/projects", {"slug": "foreign-" + uuid4().hex, "name": "Foreign"})
    foreign_path = "/api/v1/projects/" + foreign["id"]
    row = screenshot["row"]
    foreign_profiles = client.get(foreign_path + "/ocr-profiles")
    assert foreign_profiles.status_code == 200
    assert foreign_profiles.json()["items"]  # Deployment profiles are shared, route scope still requires a real project.
    assert client.get(foreign_path + "/screenshots/" + row["id"] + "/verification-runs").status_code == 404
    assert client.get(catalog["p"] + "/screenshots/" + str(uuid4()) + "/verification-runs").status_code == 404

    created_run = client.post(_run_path(row), json=_run_body(available_profile))
    assert created_run.status_code == 202, created_run.text
    run_id = created_run.json()["id"]
    foreign_run_path = foreign_path + "/screenshots/" + row["id"] + "/verification-runs/" + run_id
    assert client.get(foreign_run_path).status_code == 404
    assert client.get(_run_path(row, str(uuid4()))).status_code == 404


def test_phase2_screenshot_and_current_expected_contract_remain_unchanged(client, expected_screenshot):
    row = expected_screenshot["row"]
    catalog = expected_screenshot["catalog"]
    data = expected_screenshot["data"]
    detail = client.get(catalog["p"] + "/screenshots/" + row["id"])
    assert detail.status_code == 200, detail.text
    assert detail.json()["id"] == row["id"]
    assert "storage_key" not in detail.json()
    content = client.get(catalog["p"] + "/screenshots/" + row["id"] + "/content")
    assert content.status_code == 200
    assert content.content == data
    assert content.headers["content-type"] == "image/png"

    current = client.get(catalog["p"] + "/screenshots/" + row["id"] + "/expected-strings")
    assert current.status_code == 200, current.text
    by_key = {item["string_id"]: item for item in current.json()["items"]}
    assert by_key["ocr.empty"]["text"] == ""
    assert by_key["ocr.empty"]["translation_status"] == "present"
    assert by_key["ocr.missing"]["text"] is None
    assert by_key["ocr.missing"]["translation_status"] == "missing"
