from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID
from backend.app.main import app
from backend.app.models import Build
from backend.app.services import catalog as service, expected_strings
from backend.app.errors import DomainError
from conftest import created


def test_concurrent_duplicate_build(client, catalog):
    barrier = Barrier(2)
    def create():
        with client.factory() as session:
            barrier.wait()
            try:
                service.create(session, Build, {"label": "concurrent"}, UUID(catalog["project"]["id"]))
                return 201
            except DomainError as error:
                return error.status
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: create(), range(2))) == [201, 409]


def test_concurrent_expected_replacements_are_atomic(client, catalog):
    p = catalog["p"]
    for value in ("one", "two"):
        created(client, p + "/string-keys", {"string_id": value})
    barrier = Barrier(2)
    def replace(values):
        with client.factory() as session:
            barrier.wait()
            return expected_strings.replace(session, UUID(catalog["project"]["id"]), UUID(catalog["build"]["id"]), UUID(catalog["situation"]["id"]), values)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(replace, [["one", "two"], ["two"]]))
    assert [[i["string_id"] for i in r["items"]] for r in results] == [["one", "two"], ["two"]]
    response = client.get(p + "/situations/" + catalog["situation"]["id"] + "/expected-string-keys", params={"build_id": catalog["build"]["id"]})
    assert [x["string_id"] for x in response.json()["items"]] in (["one", "two"], ["two"])


def test_openapi_contract():
    schema = app.openapi()
    paths, models = schema["paths"], schema["components"]["schemas"]
    assert {
        "/health",
        "/ready",
        "/api/v1/projects",
        "/api/v1/projects/{project_id}/screenshots/{screenshot_id}/verification-runs",
        "/api/v1/projects/{project_id}/ocr-profiles",
    } <= set(paths)
    assert models["ProjectPatch"]["properties"]["name"]["type"] == "string"
    assert "required" not in models["ProjectPatch"]
    assert models["BuildPatch"]["required"] == ["description"]
    assert {"type": "null"} in models["BuildPatch"]["properties"]["description"]["anyOf"]
    assert "id" in models["StringEntry"]["required"] and "string_id" in models["StringEntry"]["required"]
    upload = paths["/api/v1/projects/{project_id}/screenshots"]["post"]
    assert upload["requestBody"]["content"]["multipart/form-data"]["schema"]["required"] == ["file", "metadata"]
    assert "ScreenshotUpload" in models
    verification_post = paths[
        "/api/v1/projects/{project_id}/screenshots/{screenshot_id}/verification-runs"
    ]["post"]
    assert verification_post["responses"]["202"]["headers"]["Idempotency-Replayed"]["schema"]["enum"] == ["false"]
    assert verification_post["responses"]["202"]["headers"]["Retry-After"]["schema"]["const"] == 2
    assert verification_post["responses"]["200"]["headers"]["Idempotency-Replayed"]["schema"]["enum"] == ["true"]
    assert "Location" in verification_post["responses"]["200"]["headers"]
    for path, operations in paths.items():
        if path.startswith("/api/v1"):
            for method, operation in operations.items():
                assert operation["responses"]["422"]["content"]["application/json"]["schema"]["$ref"].endswith("/Error")
                assert all(p["name"] != "identity" for p in operation.get("parameters", []))
