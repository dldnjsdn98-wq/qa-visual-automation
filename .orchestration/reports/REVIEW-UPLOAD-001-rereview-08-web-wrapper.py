from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from uuid import uuid4

from sqlalchemy import URL, create_engine


ROOT = Path(r"C:\Dev\qa-visual-automation")
HARNESS = ROOT / "tests" / "frontend" / "run_integration.py"
EVIDENCE = ROOT / ".orchestration" / "reports" / "REVIEW-UPLOAD-001-rereview-08-c-evidence.json"
STOP_FILE = EVIDENCE.with_suffix(".stop")


def load_harness():
    spec = importlib.util.spec_from_file_location("review08_current_web_harness", HARNESS)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load current Web harness")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.EVIDENCE = EVIDENCE
    module.STOP_FILE = STOP_FILE
    return module


def main() -> int:
    module = load_harness()
    container = "qa-review08-c-pg-" + uuid4().hex
    password = secrets.token_urlsafe(32)
    env = dict(os.environ, POSTGRES_PASSWORD=password)
    try:
        subprocess.run(
            ["docker", "run", "--rm", "-d", "--name", container,
             "-e", "POSTGRES_PASSWORD", "-p", "127.0.0.1::5432", "postgres:17-alpine"],
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        os.environ["QA_VERIFY_POSTGRES_IMAGE"] = subprocess.check_output(
            ["docker", "image", "inspect", "postgres:17-alpine", "--format", "{{.Id}}"],
            text=True,
        ).strip()
        reference = subprocess.run(
            ["docker", "image", "inspect", "qa-backend-review-rework-03:local", "--format", "{{.Id}}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if reference.returncode == 0:
            os.environ["QA_VERIFY_BACKEND_REFERENCE_IMAGE"] = reference.stdout.strip()
        port = int(
            subprocess.check_output(["docker", "port", container, "5432/tcp"], text=True)
            .strip().rsplit(":", 1)[1]
        )
        test_url = URL.create(
            "postgresql+psycopg",
            username="postgres",
            password=password,
            host="127.0.0.1",
            port=port,
            database="postgres",
        )
        for _ in range(120):
            probe = create_engine(test_url, connect_args={"connect_timeout": 1})
            try:
                with probe.connect() as connection:
                    connection.exec_driver_sql("SELECT 1")
                break
            except Exception:
                time.sleep(0.25)
            finally:
                probe.dispose()
        else:
            raise RuntimeError("isolated PostgreSQL did not become reachable")
        sys.argv = [str(HARNESS), "--verify-upload-web"]
        return module.main(test_url)
    finally:
        subprocess.run(["docker", "rm", "-f", container], stdout=subprocess.DEVNULL, check=False)
        if EVIDENCE.exists():
            evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
            evidence["cleanup"]["postgres_container"] = "removed"
            EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        STOP_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
