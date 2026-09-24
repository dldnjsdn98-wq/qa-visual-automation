"""Run the real Frontend client against FastAPI + an isolated PostgreSQL DB.

Usage from project root: .venv/Scripts/python.exe tests/frontend/run_integration.py
Add --serve for manual browser QA on loopback port 8001 (Ctrl+C cleans up).
Never migrates or clears the configured user database.
"""
import os
from pathlib import Path
import shutil
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
import uvicorn
from backend.app.config import get_settings
from backend.app.main import app
from backend.app.api.dependencies import get_session, get_storage
from backend.app.storage.local import LocalStorage


def main(test_url=None):
    serve = "--serve" in sys.argv
    name = "qa_frontend_test_" + uuid4().hex
    url = test_url or get_settings().database_url
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5})
    with admin.connect() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE "{name}" ENCODING \'UTF8\' TEMPLATE template0')
    engine = create_engine(url.set(database=name), isolation_level="REPEATABLE READ", connect_args={"client_encoding": "utf8", "connect_timeout": 5})
    server = None
    worker = None
    listener = socket.socket()
    try:
        config = Config(str(ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(ROOT / "backend/migrations"))
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        factory = sessionmaker(engine, expire_on_commit=False)
        def sessions():
            with factory() as session:
                yield session
        with tempfile.TemporaryDirectory(prefix="qa_frontend_storage_") as directory:
            storage = LocalStorage(Path(directory) / "storage")
            app.dependency_overrides[get_session] = sessions
            app.dependency_overrides[get_storage] = lambda: storage
            listener.bind(("127.0.0.1", 8001 if serve else 0))
            port = listener.getsockname()[1]
            server = uvicorn.Server(uvicorn.Config(app, log_level="warning"))
            worker = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
            worker.start()
            for _ in range(100):
                if server.started:
                    break
                if not worker.is_alive():
                    raise RuntimeError("Integration server stopped during startup")
                time.sleep(0.05)
            if not server.started:
                raise RuntimeError("Integration server startup timed out")
            print(f"ISOLATED FRONTEND API http://127.0.0.1:{port} database={name}", flush=True)
            try:
                if serve:
                    while worker.is_alive():
                        time.sleep(0.25)
                    return 0
                env = dict(os.environ, QA_API_BASE_URL=f"http://127.0.0.1:{port}")
                npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
                if not npm:
                    raise RuntimeError("npm must be available on PATH")
                return subprocess.run([npm, "run", "test:integration"], cwd=ROOT / "frontend", env=env).returncode
            finally:
                server.should_exit = True
                worker.join(timeout=10)
    finally:
        if server:
            server.should_exit = True
        if worker:
            worker.join(timeout=10)
        listener.close()
        app.dependency_overrides.clear()
        engine.dispose()
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        admin.dispose()
        print("Isolated frontend database removed.", flush=True)


if __name__ == "__main__":
    container = None
    try:
        test_url = None
        if "--isolated-postgres" in sys.argv:
            container = "qa-frontend-test-" + uuid4().hex
            password = secrets.token_urlsafe(32)
            env = dict(os.environ, POSTGRES_PASSWORD=password)
            subprocess.run(["docker", "run", "--rm", "-d", "--name", container, "-e", "POSTGRES_PASSWORD", "-p", "127.0.0.1::5432", "postgres:17-alpine"], env=env, check=True, stdout=subprocess.DEVNULL)
            port = int(subprocess.check_output(["docker", "port", container, "5432/tcp"], text=True).strip().rsplit(":", 1)[1])
            for _ in range(120):
                ready = subprocess.run(["docker", "exec", container, "pg_isready", "-U", "postgres"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if ready.returncode == 0:
                    break
                time.sleep(0.25)
            test_url = URL.create("postgresql+psycopg", username="postgres", password=password, host="127.0.0.1", port=port, database="postgres")
        sys.exit(main(test_url))
    except KeyboardInterrupt:
        pass
    finally:
        if container:
            subprocess.run(["docker", "rm", "-f", container], stdout=subprocess.DEVNULL, check=False)
