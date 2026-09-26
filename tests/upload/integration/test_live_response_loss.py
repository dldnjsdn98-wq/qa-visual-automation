from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from uuid import uuid4

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy import URL

from agent.screenshot_upload.manifest import load_ready_item
from agent.screenshot_upload.origin import BindingGuard, initialize_binding
from agent.screenshot_upload.producer import Producer
from agent.screenshot_upload.state import QueueStatus
from agent.screenshot_upload.state_store import StateStore


ROOT = Path(__file__).resolve().parents[3]
HELPER = Path(__file__).with_name("response_loss_agent.py")


def _free_port() -> int:
    with socket.socket() as stream:
        stream.bind(("127.0.0.1", 0))
        return stream.getsockname()[1]


def _migrate(engine) -> None:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "backend" / "migrations"))
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


def _start_postgres(port: int, name: str) -> tuple[subprocess.CompletedProcess, URL]:
    user = "upload_test"
    password = "upload_test_password"
    result = subprocess.run(
        [
            "docker", "run", "--rm", "-d", "--name", name,
            "-e", f"POSTGRES_USER={user}", "-e", f"POSTGRES_PASSWORD={password}",
            "-e", "POSTGRES_DB=postgres", "-p", f"127.0.0.1:{port}:5432",
            "postgres:17-alpine",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    url = URL.create(
        "postgresql+psycopg", username=user, password=password,
        host="127.0.0.1", port=port, database="postgres",
    )
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        probe = create_engine(url, connect_args={"connect_timeout": 1})
        try:
            with probe.connect() as connection:
                connection.exec_driver_sql("SELECT 1")
            return result, url
        except Exception:
            time.sleep(0.1)
        finally:
            probe.dispose()
    logs = subprocess.run(["docker", "logs", name], check=False, capture_output=True, text=True, timeout=10)
    raise RuntimeError(f"disposable PostgreSQL did not become ready: {logs.stdout}{logs.stderr}")


def _stop_postgres(name: str) -> None:
    subprocess.run(
        ["docker", "stop", "--time", "5", name],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )


def _start_api(port: int, database_name: str, storage_root: Path, database_url: URL):
    environment = os.environ.copy()
    environment.update(
        POSTGRES_DB=database_name,
        POSTGRES_USER=database_url.username or "",
        POSTGRES_PASSWORD=database_url.password or "",
        DATABASE_HOST=database_url.host or "127.0.0.1",
        DATABASE_PORT=str(database_url.port),
        STORAGE_ROOT=str(storage_root),
    )
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    origin = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(f"uvicorn exited during startup: {output}")
        try:
            if httpx.get(origin + "/health", timeout=0.5).status_code == 200:
                return process, origin
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    process.terminate()
    output = process.communicate(timeout=5)[0]
    raise RuntimeError(f"uvicorn did not become ready: {output}")


def _stop_api(process) -> str:
    if process.poll() is None:
        process.terminate()
    try:
        return process.communicate(timeout=10)[0]
    except subprocess.TimeoutExpired:
        process.kill()
        return process.communicate(timeout=5)[0]


def _created(client: httpx.Client, path: str, body: dict) -> dict:
    response = client.post(path, json=body)
    assert response.status_code == 201, response.text
    return response.json()


def test_real_backend_restart_and_uploader_restart_replay_one_receipt(request, tmp_path, png_bytes):
    if not request.config.getoption("--run-live-upload"):
        pytest.skip("pass --run-live-upload for disposable PostgreSQL/uvicorn integration")

    database_name = "qa_upload_live_" + uuid4().hex
    postgres_name = "qa-upload-live-" + uuid4().hex
    postgres_port = _free_port()
    postgres = None
    admin = None
    engine = None
    api = None
    try:
        postgres, admin_url = _start_postgres(postgres_port, postgres_name)
        admin = create_engine(admin_url, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5})
        with admin.connect() as connection:
            connection.exec_driver_sql(f'CREATE DATABASE "{database_name}" ENCODING \'UTF8\' TEMPLATE template0')
        database_url = admin_url.set(database=database_name)
        engine = create_engine(database_url, connect_args={"connect_timeout": 5})
        _migrate(engine)
        port = _free_port()
        storage_root = tmp_path / "backend-storage"
        api, origin = _start_api(port, database_name, storage_root, database_url)
        with httpx.Client(base_url=origin, timeout=10) as client:
            project = _created(client, "/api/v1/projects", {"slug": "live-" + uuid4().hex, "name": "Live"})
            prefix = f"/api/v1/projects/{project['id']}"
            build = _created(client, prefix + "/builds", {"label": "1.0"})
            locale = _created(client, prefix + "/locales", {"code": "ko-KR", "name": "한국어"})
            category = _created(client, prefix + "/categories", {"slug": "tutorial", "name": "Tutorial"})
            situation = _created(
                client,
                prefix + "/situations",
                {"category_id": category["id"], "slug": "welcome", "name": "Welcome"},
            )

        spool_root = tmp_path / "captures"
        initialize_binding(spool_root, origin)
        guard = BindingGuard(spool_root, origin)
        item = Producer(spool_root, guard).publish(
            png_bytes,
            project_id=project["id"],
            original_filename="실제-응답손실.png",
            request={
                "build_id": build["id"],
                "locale_id": locale["id"],
                "category_id": category["id"],
                "situation_id": situation["id"],
                "source": "agent",
                "metadata_version": 1,
                "metadata": {"checkpoint": "응답 손실", "resolution": {"width": 2, "height": 3}},
            },
        )

        first_agent = subprocess.run(
            [
                sys.executable, str(HELPER), "--spool", str(spool_root), "--backend-origin", origin,
                "--observed-response", str(tmp_path / "discarded-response.json"),
            ],
            cwd=ROOT,
            check=False,
            timeout=30,
        )
        assert first_agent.returncode == 97
        durable = StateStore(guard.check).load(item)
        assert durable.state is QueueStatus.RETRY_WAIT
        assert durable.attempt_count == 1
        first_response = json.loads((tmp_path / "discarded-response.json").read_text(encoding="utf-8"))
        assert first_response["status"] == 201
        assert first_response["headers"]["idempotency-replayed"] == "false"

        _stop_api(api)
        api = None
        api, _ = _start_api(port, database_name, storage_root, database_url)
        resumed = subprocess.run(
            [sys.executable, "-m", "agent.screenshot_upload", "run", "--spool", str(spool_root), "--backend-origin", origin],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert resumed.returncode == 0, resumed.stderr

        uploaded = load_ready_item(spool_root / "uploaded" / item.client_upload_id)
        final_state = StateStore(guard.check).load(uploaded)
        assert final_state.state is QueueStatus.UPLOADED
        assert final_state.attempt_count == 2
        assert final_state.ack.status == 200
        assert final_state.ack.idempotency_replayed is True
        assert final_state.ack.screenshot["id"] == first_response["body"]["id"]
        assert final_state.ack.screenshot["uploaded_at"] == first_response["body"]["uploaded_at"]
        assert final_state.ack.location == first_response["headers"]["location"]

        with httpx.Client(base_url=origin, timeout=10) as client:
            listing = client.get(prefix + "/screenshots").json()
            assert listing["total"] == 1
            screenshot = listing["items"][0]
            assert screenshot["client_upload_id"] == item.client_upload_id
            assert screenshot["metadata"]["checkpoint"] == "응답 손실"
            detail = client.get(prefix + f"/screenshots/{screenshot['id']}")
            content = client.get(prefix + f"/screenshots/{screenshot['id']}/content")
            assert detail.status_code == 200
            assert content.status_code == 200
            assert sha256(content.content).hexdigest() == item.file_hash
        with engine.connect() as connection:
            assert connection.execute(text("SELECT count(*) FROM screenshots")).scalar_one() == 1
            assert connection.execute(text("SELECT count(*) FROM upload_receipts WHERE state='COMPLETED'")).scalar_one() == 1
        assert len([path for path in storage_root.rglob("*") if path.is_file()]) == 1
    finally:
        if api is not None:
            _stop_api(api)
        if engine is not None:
            engine.dispose()
        if admin is not None:
            with admin.connect() as connection:
                connection.exec_driver_sql(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)')
            admin.dispose()
        if postgres is not None:
            _stop_postgres(postgres_name)
