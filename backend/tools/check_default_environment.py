"""Read-only, sanitized diagnosis of the configured persistent PostgreSQL."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.app.config import Settings
import psycopg
from dotenv import dotenv_values

def docker(*args):
    result = subprocess.run(["docker", *args], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("Docker command failed (output suppressed)")
    return json.loads(result.stdout)

def main():
    settings = Settings()
    compose = docker("compose", "config", "--format", "json")
    env = compose["services"]["postgres"]["environment"]
    container = docker("inspect", "qa-visual-automation-postgres-1")[0]
    actual = dict(item.split("=", 1) for item in container["Config"]["Env"] if "=" in item)
    file_env = dotenv_values(ROOT / ".env")
    print(json.dumps({
        "target": {"host": settings.database_host, "port": settings.database_port,
                   "database": settings.postgres_db, "user": settings.postgres_user},
        "container_status": container["State"]["Status"],
        "volumes": [{"name": v.get("Name"), "destination": v["Destination"]} for v in container["Mounts"]],
        "password_equal": {"app_compose": settings.postgres_password == env.get("POSTGRES_PASSWORD"),
                           "app_container": settings.postgres_password == actual.get("POSTGRES_PASSWORD"),
                           "app_dotenv": settings.postgres_password == file_env.get("POSTGRES_PASSWORD")},
        "process_override_keys": [k for k in ("POSTGRES_PASSWORD", "POSTGRES_USER", "POSTGRES_DB", "DATABASE_HOST", "DATABASE_PORT") if k in os.environ],
    }))
    try:
        with psycopg.connect(host=settings.database_host, port=settings.database_port,
                             dbname=settings.postgres_db, user=settings.postgres_user,
                             password=settings.postgres_password, connect_timeout=5) as conn:
            print(json.dumps({"authenticated_query": conn.execute("SELECT 1, current_database(), current_user").fetchone()}))
            exists = conn.execute("SELECT to_regclass('public.alembic_version')").fetchone()[0]
            print(json.dumps({"migration": conn.execute("SELECT version_num FROM alembic_version").fetchall() if exists else None}))
    except psycopg.Error as exc:
        print(json.dumps({"authenticated_query": "FAIL", "error_type": type(exc).__name__, "sqlstate": exc.sqlstate}))
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
