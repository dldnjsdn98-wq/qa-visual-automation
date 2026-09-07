import json
from uuid import uuid4
import pytest
from conftest import created


def test_project_crud(client):
    row = created(client, "/api/v1/projects", {"slug": "p-" + uuid4().hex, "name": "게임 😀", "description": "keep"})
    path = "/api/v1/projects/" + row["id"]
    assert client.get(path).json()["name"] == "게임 😀"
    assert client.patch(path, json={"name": "new"}).json()["description"] == "keep"
    assert client.patch(path, json={"description": None}).json()["description"] is None
    for invalid in ({}, {"name": None}, {"slug": "changed"}, {"name": "\0"}):
        assert client.patch(path, json=invalid).status_code == 422
    assert client.get("/api/v1/projects?limit=1").json()["limit"] == 1
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == client.delete(path).status_code == 404


@pytest.mark.parametrize("resource,body,patch", [
    ("builds", {"label": "extra", "description": "before"}, {"description": None}),
    ("locales", {"code": "ko-kr", "name": "Korean"}, {"name": "한국어"}),
    ("categories", {"slug": "extra", "name": "Extra"}, {"name": "변경"}),
    ("situations", {"slug": "extra", "name": "Extra"}, {"description": "변경"}),
    ("string-keys", {"string_id": "welcome.key", "description": "before"}, {"description": None}),
])
def test_scoped_crud(client, catalog, resource, body, patch):
    body = dict(body)
    if resource == "situations":
        body["category_id"] = catalog["category"]["id"]
    collection = catalog["p"] + "/" + resource
    row = created(client, collection, body)
    path = collection + "/" + row["id"]
    assert client.post(collection, json=body).status_code == 409
    assert client.get(path).json()["id"] == row["id"]
    changed = client.patch(path, json=patch)
    assert changed.status_code == 200, changed.text
    assert all(changed.json()[k] == v for k, v in patch.items())
    assert any(item["id"] == row["id"] for item in client.get(collection).json()["items"])
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404


def test_relationships_filters_and_locale(client, catalog):
    p = catalog["p"]
    foreign = created(client, "/api/v1/projects", {"slug": "p-" + uuid4().hex, "name": "other"})
    fp = "/api/v1/projects/" + foreign["id"]
    assert client.get(fp + "/builds/" + catalog["build"]["id"]).status_code == 404
    assert client.post(fp + "/situations", json={"category_id": catalog["category"]["id"], "slug": "s", "name": "s"}).status_code == 404
    assert client.get(p + "/situations?category_id=" + str(uuid4())).status_code == 404
    assert client.get(p + "/situations?category_id=" + catalog["category"]["id"]).json()["total"] == 1
    assert client.delete(p).status_code == 409
    assert client.delete(p + "/categories/" + catalog["category"]["id"]).status_code == 409
    assert catalog["locale"]["code"] == "ja-JP"
    assert client.post(p + "/locales", json={"code": "JA-JP", "name": "duplicate"}).status_code == 409
    assert client.post(p + "/locales", json={"code": "en-US-x-test", "name": "invalid"}).json()["error"]["code"] == "UNSUPPORTED_LOCALE_CODE"
    for query in ("limit=0", "limit=101", "offset=-1", "limit=1&limit=2", "unknown=x", "name=%FF"):
        response = client.get(p + "/builds?" + query)
        assert response.status_code == 422, response.text


@pytest.mark.parametrize("text", ["", "ようこそ 한글 e\u0301\r\n\t", "😀", "😀" * 10000, r"literal\ud800"], ids=["empty", "multilingual", "emoji", "scalar-limit", "literal-escape"])
def test_strings_unicode_and_expected(client, catalog, text):
    p, build, locale, situation = catalog["p"], catalog["build"]["id"], catalog["locale"]["id"], catalog["situation"]["id"]
    key = created(client, p + "/string-keys", {"string_id": "welcome"})
    created(client, p + "/string-keys", {"string_id": "missing"})
    body = dict(build_id=build, locale_id=locale, string_id="welcome", text=text)
    entry = created(client, p + "/strings", body)
    path = p + "/strings/" + entry["id"]
    assert client.get(path).json()["text"] == text
    assert client.post(p + "/strings", json=body).status_code == 409
    mapping = p + "/situations/" + situation + "/expected-string-keys?build_id=" + build
    assert client.put(mapping, json={"string_ids": ["missing", "welcome"]}).status_code == 200
    expected = p + "/situations/" + situation + "/expected-strings?build_id=" + build + "&locale_id=" + locale
    result = client.get(expected).json()
    assert result["items"][0]["text"] is None and result["missing_count"] == 1
    assert result["items"][1]["text"] == text and result["items"][1]["translation_status"] == "present"
    assert client.get(p + "/strings", params=dict(build_id=build, locale_id=locale, string_id="welcome")).json()["total"] == 1
    assert client.get(p + "/strings?string_id=missing").json()["total"] == 0
    assert client.get(p + "/strings?string_id=unknown").status_code == 404
    assert client.put(mapping, json={"string_ids": ["welcome", "welcome"]}).status_code == 422
    assert client.put(mapping, json={"string_ids": ["unknown"]}).status_code == 404
    assert len(client.get(mapping).json()["items"]) == 2
    assert client.delete(p + "/string-keys/" + key["id"]).status_code == 409
    assert client.patch(path, json={"text": "updated"}).json()["text"] == "updated"
    assert client.delete(path).status_code == 204
    assert client.get(expected).json()["missing_count"] == 2
    assert client.put(mapping, json={"string_ids": []}).json()["items"] == []


@pytest.mark.parametrize("value", ["a\0b", "\ud800", "\udfff", "\udfff\ud800", "😀" * 10001], ids=["nul", "high-surrogate", "low-surrogate", "reversed-pair", "over-limit"])
def test_invalid_string_create_patch_no_write(client, catalog, value, monkeypatch):
    p = catalog["p"]
    created(client, p + "/string-keys", {"string_id": "key"})
    body = dict(build_id=catalog["build"]["id"], locale_id=catalog["locale"]["id"], string_id="key", text="original")
    entry = created(client, p + "/strings", body)
    def forbidden(*args, **kwargs):
        pytest.fail("invalid Unicode reached write")
    monkeypatch.setattr("backend.app.repositories.catalog.insert", forbidden)
    for method, path, payload in [("POST", p + "/strings", dict(body, text=value)), ("PATCH", p + "/strings/" + entry["id"], {"text": value})]:
        response = client.request(method, path, content=json.dumps(payload), headers={"Content-Type": "application/json"})
        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert response.json()["error"]["details"][0]["field"] == "body.text"
    assert client.get(p + "/strings/" + entry["id"]).json()["text"] == "original"


def test_error_envelope_transport_and_cors(client):
    for method, path, kwargs, status in [("GET", "/api/v1/unknown", {}, 404), ("PUT", "/api/v1/projects", {"json": {}}, 405), ("POST", "/api/v1/projects", {"content": b'{"name":"\xff"}', "headers": {"Content-Type": "application/json"}}, 422), ("POST", "/api/v1/projects", {"content": "{}", "headers": {"Content-Type": "text/plain"}}, 415)]:
        response = client.request(method, path, **kwargs)
        assert response.status_code == status, response.text
        assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
    response = client.options("/api/v1/projects", headers={"Origin": "http://localhost:3001", "Access-Control-Request-Method": "PATCH", "Access-Control-Request-Headers": "Content-Type"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3001"
