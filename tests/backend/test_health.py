from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from backend.app.main import app

client = TestClient(app)


def test_liveness():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_returns_unavailable_without_exposing_db_error(monkeypatch):
    def fail():
        raise OperationalError("secret query", {}, Exception("secret credential"))
    monkeypatch.setattr("backend.app.main.engine.connect", fail)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_openapi_contains_operations_and_current_routes():
    paths = client.get("/openapi.json").json()["paths"]
    assert {
        "/health",
        "/ready",
        "/api/v1/projects",
        "/api/v1/projects/{project_id}/screenshots/{screenshot_id}/verification-runs",
        "/api/v1/projects/{project_id}/ocr-profiles",
    } <= set(paths)
