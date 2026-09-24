"""Run tests against a disposable PostgreSQL 17 container; preserve existing DBs."""
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


def main():
    name = "qa-backend-test-" + uuid4().hex[:12]
    env = dict(os.environ, POSTGRES_PASSWORD=secrets.token_urlsafe(32), POSTGRES_USER="qa_visual", POSTGRES_DB="qa_visual")
    def docker(*args):
        return subprocess.run(["docker", *args], env=env, check=True, text=True, capture_output=True).stdout.strip()
    started = False
    network = False
    try:
        docker("network", "create", name)
        network = True
        docker("run", "--rm", "-d", "--name", name, "--network", name, "-e", "POSTGRES_PASSWORD", "-e", "POSTGRES_USER", "-e", "POSTGRES_DB", "-p", "127.0.0.1::5432", "postgres:17-alpine")
        started = True
        port = docker("port", name, "5432/tcp").rsplit(":", 1)[1]
        for attempt in range(30):
            try:
                docker("exec", name, "pg_isready", "-U", "qa_visual", "-d", "qa_visual")
                break
            except subprocess.CalledProcessError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Test PostgreSQL did not become ready")
        env.update(DATABASE_HOST="127.0.0.1", DATABASE_PORT=port)
        args = sys.argv[1:] or ["-q", "--tb=short"]
        if "--linux" in args:
            args.remove("--linux")
            env.update(DATABASE_HOST=name, DATABASE_PORT="5432")
            result = subprocess.run(["docker", "run", "--rm", "--network", name, "-e", "POSTGRES_PASSWORD", "-e", "POSTGRES_USER", "-e", "POSTGRES_DB", "-e", "DATABASE_HOST", "-e", "DATABASE_PORT", "qa-backend-test-runtime:local", "python", "-m", "pytest", "tests/backend", *(args or ["-q", "--tb=short"])], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            print(result.stdout, end="")
            report = ROOT / ".orchestration/reports/backend-linux.txt"
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(result.stdout, encoding="utf-8")
            return result.returncode
        temporary = ".pytest_cache/" + name
        result = subprocess.run([sys.executable, "-m", "pytest", "tests/backend", f"--basetemp={temporary}", *args], cwd=ROOT, env=env)
        return result.returncode
    finally:
        if started:
            docker("stop", name)
        if network:
            docker("network", "rm", name)


if __name__ == "__main__":
    raise SystemExit(main())
