"""One-shot Linux parent-OOM and durable PostgreSQL lease recovery evidence.

This is a parent-reviewed diagnostic harness, not a pytest test or a production
runner.  The host mode is the only public entry point.  The remaining modes run
inside the exact reviewed Linux image.  No mode downloads dependencies, loads a
model, changes application source, or connects to any database except the
randomly named database created by this invocation.

The host deliberately does not use the general evidence capture helper: it must
retain a stopped OOM container long enough to inspect Docker's authoritative
State.OOMKilled/ExitCode fields before removing that exact owned container.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import time
from uuid import UUID, uuid4


IMAGE_TAG = "qa-backend-ocr-native-diagnostic:20260925b"
IMAGE_ID = "sha256:56c45fb0dac074888d84484e414107c95342ab325e148c916fe55e454f1df662"
MEMORY_BYTES = 512 * 1024 * 1024
OWNER_LABEL = "BACKEND-OCR-001-native-diagnostic-parent-oom-03"
DATABASE_RE = re.compile(r"qa_backend_parent_oom_[0-9a-f]{32}\Z")
CONTAINER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
IMAGE_ID_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
EXPECTED_SOURCE_HASHES = {
    "backend/app/workers/ocr_containment.py": "ef7d7ffe6dbc0b8f620ae9416818614cf9aa9dc5ceb822fdee11d4feca76bec5",
    "backend/app/services/verification_jobs.py": "6c1689d1d197e298c689c66554ae93990ecc210157c6b1efb67cc57a293d488a",
    "backend/app/repositories/verification_runs.py": "40baa349c9ca23ed4feac7734b837907c9d9abbbb0f83f5fe9a7588e16a0ca06",
    "tests/backend/test_ocr_jobs.py": "13eea9e356f528b432e8ca9fade6257a8f4fd6bef37fa033665d7e527ab5197c",
    "tests/backend/test_ocr_runtime_db.py": "88bf8639bff1b1c0fb6d9b89491d454b5c06b98d2684f27c02e597e63d89692f",
    "tests/backend/test_ocr_containment.py": "382257cfb9747b2fe9d7aa87fedd5d50d5f853745c483be5b1764c3c958ade1b",
    "backend/migrations/versions/0004_phase3_ocr_verification.py": "8132cd7b43aba5a543d3acbdc3be218ceab7f3e303729a4ac9e7f7d0ccb0d024",
    "backend/Dockerfile.test": "5f93a520ceee7612def4fae20ed2d9d6ef06ff5d83efebdba54592c828ab8418",
}
_RETAINED_HANDLES = []


class HarnessError(RuntimeError):
    pass


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    raise TypeError(type(value).__name__)


def _atomic_json(path: Path, value: dict) -> None:
    """Publish and file-fsync evidence; directory fsync is POSIX-only."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    payload = (json.dumps(value, indent=2, sort_keys=True, default=_json_value) + "\n").encode()
    with temporary.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    if os.name == "posix":
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)


def _source_hashes(root: Path) -> dict[str, str]:
    values = {}
    for relative in EXPECTED_SOURCE_HASHES:
        path = root / relative
        if not path.is_file():
            raise HarnessError(f"required source missing: {relative}")
        values[relative] = _sha256(path)
    return values


def _require_exact_sources(root: Path) -> dict[str, str]:
    actual = _source_hashes(root)
    mismatches = {
        name: {"expected": EXPECTED_SOURCE_HASHES[name], "actual": digest}
        for name, digest in actual.items()
        if digest != EXPECTED_SOURCE_HASHES[name]
    }
    if mismatches:
        raise HarnessError("exact-source gate failed: " + json.dumps(mismatches, sort_keys=True))
    return actual


def _safe_database_name(value: str) -> str:
    if not DATABASE_RE.fullmatch(value):
        raise HarnessError("database name is outside this harness's unique namespace")
    return value


def _safe_container_ref(value: str) -> str:
    if not CONTAINER_RE.fullmatch(value):
        raise HarnessError("invalid container reference")
    return value


def _run(argv: list[str], *, timeout: float = 60, check: bool = True) -> subprocess.CompletedProcess:
    """Run without a shell and never echo argv or inherited/environment-file values."""
    result = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=timeout, check=False)
    if check and result.returncode != 0:
        raise HarnessError(f"external command failed with exit {result.returncode}")
    return result


def _docker_inspect(ref: str, field: str) -> str:
    return _run(["docker", "container", "inspect", "--format", "{{" + field + "}}", ref]).stdout.strip()


def _container_exists(ref: str) -> bool:
    # A successful formatted list is authoritative for absence. Any daemon,
    # access or transport failure is ambiguous and must fail closed.
    result = _run([
        "docker", "container", "ls", "-a", "--no-trunc",
        "--filter", "name=^/" + ref + "$", "--format", "{{.ID}} {{.Names}}",
    ], check=False)
    if result.returncode != 0:
        raise HarnessError("container existence query unavailable")
    rows = [line.split(" ", 1) for line in result.stdout.splitlines() if line.strip()]
    if any(len(row) != 2 or row[1] != ref for row in rows) or len(rows) > 1:
        raise HarnessError("container existence query returned ambiguous identity")
    return len(rows) == 1


def _owned_container(ref: str, expected_id: str, nonce: str) -> bool:
    if not _container_exists(ref):
        return False
    return (
        _docker_inspect(ref, ".Id") == expected_id
        and _docker_inspect(ref, ".Name").lstrip("/") == ref
        and _docker_inspect(ref, 'index .Config.Labels "qa.visual.owner"') == OWNER_LABEL
        and _docker_inspect(ref, 'index .Config.Labels "qa.visual.nonce"') == nonce
    )


def _stop_and_remove_owned(ref: str, expected_id: str, nonce: str) -> dict:
    result = {"container": ref, "id": expected_id, "stopped": False, "removed": False}
    if not _container_exists(ref):
        result["already_absent"] = True
        return result
    if not _owned_container(ref, expected_id, nonce):
        raise HarnessError("refusing cleanup: container identity/ownership mismatch")
    if _docker_inspect(ref, ".State.Running").lower() == "true":
        stopped = _run(["docker", "stop", "--time", "2", expected_id], timeout=15, check=False)
        result["stop_exit_code"] = stopped.returncode
        result["stopped"] = stopped.returncode == 0
    if _docker_inspect(ref, ".State.Running").lower() == "true":
        raise HarnessError("owned container did not stop; retained for review")
    removed = _run(["docker", "rm", expected_id], timeout=15, check=False)
    result["remove_exit_code"] = removed.returncode
    result["removed"] = removed.returncode == 0
    if not result["removed"]:
        raise HarnessError("exact owned container removal failed")
    return result


def _inside_root() -> Path:
    root = Path("/app")
    if not root.is_dir():
        raise HarnessError("inner mode requires the reviewed /app image")
    os.chdir(root)
    application_root = str(root)
    backend_tests = str(root / "tests/backend")
    if application_root not in sys.path:
        sys.path.insert(0, application_root)
    if backend_tests not in sys.path:
        sys.path.insert(0, backend_tests)
    return root


def _database_urls(database: str):
    from backend.app.config import get_settings

    base = get_settings().database_url
    return base.set(database="postgres"), base.set(database=database)


def _create_catalog(connection) -> dict:
    from sqlalchemy import text

    values = {name: str(uuid4()) for name in ("project", "build", "locale", "category", "situation")}
    nonce = uuid4().hex
    connection.execute(text("INSERT INTO projects (id,slug,name) VALUES (:id,:slug,'Parent OOM')"),
                       {"id": values["project"], "slug": "parent-oom-" + nonce})
    connection.execute(text("INSERT INTO builds (id,project_id,label) VALUES (:id,:p,'diagnostic')"),
                       {"id": values["build"], "p": values["project"]})
    connection.execute(text("INSERT INTO locales (id,project_id,code,name) VALUES (:id,:p,'ja-JP','Japanese')"),
                       {"id": values["locale"], "p": values["project"]})
    connection.execute(text("INSERT INTO categories (id,project_id,slug,name) VALUES (:id,:p,'diagnostic','Diagnostic')"),
                       {"id": values["category"], "p": values["project"]})
    connection.execute(text("""
        INSERT INTO situations (id,project_id,category_id,slug,name)
        VALUES (:id,:p,:category,'parent-oom','Parent OOM')
    """), {"id": values["situation"], "p": values["project"], "category": values["category"]})
    return {name: {"id": value} for name, value in values.items()}


def _setup_mode(args) -> int:
    root = _inside_root()
    sources = _require_exact_sources(root)
    database = _safe_database_name(args.database)
    evidence = Path(args.evidence)

    from sqlalchemy import create_engine, text
    from conftest import migrate

    admin_url, database_url = _database_urls(database)
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5})
    with admin.connect() as connection:
        exists = connection.scalar(text("SELECT 1 FROM pg_database WHERE datname=:name"), {"name": database})
        if exists:
            raise HarnessError("unique diagnostic database unexpectedly exists")
        connection.exec_driver_sql(f'CREATE DATABASE "{database}" ENCODING \'UTF8\' TEMPLATE template0')

    engine = create_engine(database_url, isolation_level="REPEATABLE READ",
                           connect_args={"client_encoding": "utf8", "connect_timeout": 5})
    migrate(engine)
    helpers = runpy.run_path(str(root / "tests/backend/test_ocr_jobs.py"))
    with engine.begin() as connection:
        database_oid = connection.scalar(text("SELECT oid FROM pg_database WHERE datname=current_database()"))
        connection.execute(text("""
            CREATE TABLE qa_parent_oom_diagnostic_owner (
              singleton boolean PRIMARY KEY CHECK (singleton),
              owner text NOT NULL,
              nonce text NOT NULL,
              database_name text NOT NULL,
              database_oid oid NOT NULL
            )
        """))
        connection.execute(text("""
            INSERT INTO qa_parent_oom_diagnostic_owner
              (singleton,owner,nonce,database_name,database_oid)
            VALUES (true,:owner,:nonce,:database,:oid)
        """), {"owner": OWNER_LABEL, "nonce": args.nonce,
                 "database": database, "oid": database_oid})
        catalog = _create_catalog(connection)
        project_id, run_id, _, _ = helpers["_insert_run"](connection, catalog)
    with engine.connect() as connection:
        seed = connection.execute(text("""
            SELECT clock_timestamp() AS db_now,j.state,j.stage,j.attempt_count,
                   j.generation,j.lease_expires_at,
                   (SELECT count(*) FROM verification_attempts a WHERE a.run_id=j.run_id) AS attempts
            FROM verification_jobs j WHERE j.project_id=:project AND j.run_id=:run
        """), {"project": project_id, "run": run_id}).mappings().one()
    if (seed["state"], seed["stage"], seed["attempt_count"], seed["generation"],
            seed["lease_expires_at"], seed["attempts"]) != ("PENDING", "QUEUED", 0, 0, None, 0):
        raise HarnessError("setup did not leave exactly one unclaimed PENDING job")
    # This file is deletion authority only together with the matching marker
    # row and live pg_database OID.  If creation or marker commit is uncertain,
    # no marker is published and the host must leave the database unresolved.
    _atomic_json(evidence / "database-created.json", {
        "schema_version": 1, "owner": OWNER_LABEL, "nonce": args.nonce,
        "database": database, "database_oid": database_oid,
        "created_utc": _utc(), "scope": "unique disposable diagnostic database",
    })
    _atomic_json(evidence / "setup.json", {
        "schema_version": 1,
        "phase": "pending_seeded_unclaimed",
        "owner": OWNER_LABEL,
        "nonce": args.nonce,
        "database": database,
        "database_oid": database_oid,
        "project_id": project_id,
        "run_id": run_id,
        "generation": seed["generation"],
        "attempt_count": seed["attempt_count"],
        "job_state": seed["state"],
        "stage": seed["stage"],
        "attempt_rows": seed["attempts"],
        "lease_expires_at": seed["lease_expires_at"],
        "db_observed_at": seed["db_now"],
        "source_sha256": sources,
        "helper_reuse": ["_insert_run"],
        "fixture_lifecycle_reused": False,
        "ended_utc": _utc(),
    })
    engine.dispose()
    admin.dispose()
    return 0


_TINY_CHILD = r"""
import os, sys
payload = bytearray(1024 * 1024)
payload[::4096] = b'x' * len(payload[::4096])
sys.stdout.buffer.write(b'R')
sys.stdout.buffer.flush()
sys.stdin.buffer.read(1)
"""


def _read_cgroup_events() -> dict[str, int]:
    result = {}
    for line in Path("/sys/fs/cgroup/memory.events").read_text(encoding="ascii").splitlines():
        key, value = line.split()
        result[key] = int(value)
    return result


def _fence_digest(row) -> str:
    fields = (
        row["project_id"], row["run_id"], row["generation"],
        row["attempt_token"], row["claim_request_id"], row["lease_expires_at"],
    )
    return hashlib.sha256("|".join(str(value) for value in fields).encode("ascii")).hexdigest()


def _oom_mode(args) -> int:
    root = _inside_root()
    sources = _require_exact_sources(root)
    database = _safe_database_name(args.database)
    evidence = Path(args.evidence)
    if os.getpid() != 1:
        raise HarnessError("controlled OOM parent must be container PID 1")

    from sqlalchemy import create_engine, text
    from backend.app.services.verification_jobs import VerificationJobService
    from backend.app.workers.ocr_containment import launch_contained

    _, database_url = _database_urls(database)
    engine = create_engine(database_url, isolation_level="REPEATABLE READ",
                           connect_args={"client_encoding": "utf8", "connect_timeout": 5})
    helpers = runpy.run_path(str(root / "tests/backend/test_ocr_jobs.py"))
    factory = helpers["_factory"](engine)
    claim = VerificationJobService(factory).claim()
    if claim is None or claim.fence.run_id != UUID(args.run_id):
        raise HarnessError("OOM PID 1 did not acquire the seeded job")
    if claim.attempt_count != 1 or claim.fence.generation != 1:
        raise HarnessError("OOM PID 1 initial durable claim was not generation 1")
    with engine.connect() as connection:
        owner = connection.execute(text("""
            SELECT clock_timestamp() AS db_now,j.project_id,j.run_id,j.state,j.stage,
                   j.attempt_count,j.generation,j.attempt_token,j.lease_expires_at,
                   a.claim_request_id,a.claimed_at,a.lease_at_claim,a.outcome,
                   j.last_error_code,
                   r.ocr_result_id AS run_ocr_result_id,
                   r.verification_result_id AS run_verification_result_id,
                   EXISTS(SELECT 1 FROM ocr_results o WHERE o.run_id=j.run_id) AS has_ocr_result,
                   EXISTS(SELECT 1 FROM verification_results v WHERE v.run_id=j.run_id) AS has_verification_result
            FROM verification_jobs j
            JOIN verification_runs r ON r.project_id=j.project_id AND r.id=j.run_id
            JOIN verification_attempts a ON a.project_id=j.project_id AND a.run_id=j.run_id
                 AND a.generation=j.generation AND a.attempt_token=j.attempt_token
            WHERE j.run_id=:run_id
        """), {"run_id": UUID(args.run_id)}).mappings().one()
    engine.dispose()
    if owner["state"] != "RUNNING" or owner["generation"] != 1 or owner["outcome"] != "STARTED":
        raise HarnessError("OOM claiming parent does not observe its live generation-1 claim")
    if owner["lease_expires_at"] != claim.lease_expires_at:
        raise HarnessError("OOM claiming parent lease identity changed after claim")
    if owner["lease_at_claim"] != claim.lease_expires_at:
        raise HarnessError("attempt lease identity differs from the OOM parent's claim")
    if owner["lease_expires_at"] - owner["claimed_at"] != __import__("datetime").timedelta(seconds=60):
        raise HarnessError("generation-1 claim did not receive the real 60-second DB lease")
    remaining = (owner["lease_expires_at"] - owner["db_now"]).total_seconds()
    if remaining < 45:
        raise HarnessError("less than 45 seconds remain; refuse a weakened parent-OOM observation")
    if (owner["last_error_code"] is not None or owner["run_ocr_result_id"] is not None
            or owner["run_verification_result_id"] is not None
            or owner["has_ocr_result"] or owner["has_verification_result"]):
        raise HarnessError("claim was already settled before parent OOM")

    memory_max = Path("/sys/fs/cgroup/memory.max").read_text(encoding="ascii").strip()
    swap_max = Path("/sys/fs/cgroup/memory.swap.max").read_text(encoding="ascii").strip()
    if memory_max != str(MEMORY_BYTES) or swap_max != "0":
        raise HarnessError("container is not the reviewed 512MiB/no-extra-swap cgroup")
    events_before = _read_cgroup_events()
    if any(events_before.get(key, -1) != 0 for key in ("oom", "oom_kill")):
        raise HarnessError("OOM container did not start with fresh OOM counters")

    child_dir = Path("/tmp/parent-oom-child")
    child_dir.mkdir(mode=0o700)
    child_env = {
        "LANG": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
    }
    handle = launch_contained(
        [sys.executable, "-I", "-S", "-c", _TINY_CHILD],
        env=child_env,
        cwd=str(child_dir),
        memory_limit_bytes=MEMORY_BYTES,
    )
    if handle.stdout.read(1) != b"R" or handle.poll() is not None:
        raise HarnessError("tiny contained child did not reach its DB-free wait state")
    if handle.memory_exceeded():
        raise HarnessError("memory event occurred before deliberate parent allocation")
    _atomic_json(evidence / "oom-ready.json", {
        "schema_version": 1,
        "phase": "parent_allocation_about_to_start",
        "recorded_utc": _utc(),
        "database": database,
        "project_id": owner["project_id"],
        "run_id": owner["run_id"],
        "parent_pid": os.getpid(),
        "parent_role": "process that called claim(), owns generation 1, and is allocation target",
        "child_pid": handle.pid,
        "child_role": "1MiB DB-free contained wait process",
        "child_environment_keys": sorted(child_env),
        "child_has_database_environment": False,
        "job_state": owner["state"],
        "stage": owner["stage"],
        "generation": owner["generation"],
        "attempt_count": owner["attempt_count"],
        "attempt_outcome": owner["outcome"],
        "last_error_code": owner["last_error_code"],
        "has_results": owner["has_ocr_result"] or owner["has_verification_result"],
        "lease_expires_at": owner["lease_expires_at"],
        "claimed_at": owner["claimed_at"],
        "fence_identity_sha256": _fence_digest(owner),
        "db_observed_at": owner["db_now"],
        "lease_remaining_seconds": remaining,
        "lease_seconds": 60,
        "memory_max": int(memory_max),
        "memory_swap_max": int(swap_max),
        "memory_events_before": events_before,
        "containment_info": handle.containment_info,
        "source_sha256": sources,
    })

    # The parent becomes by far the largest anonymous-memory consumer.  A real
    # cgroup OOM must kill PID 1.  MemoryError/survival is a failed diagnostic,
    # never rewritten as OOM evidence and never retried by this harness.
    held = []
    try:
        while True:
            chunk = bytearray(16 * 1024 * 1024)
            chunk[::4096] = b"x" * len(chunk[::4096])
            held.append(chunk)
    except MemoryError:
        _atomic_json(evidence / "oom-survived.json", {
            "schema_version": 1,
            "status": "FAILED_PARENT_SURVIVED_ALLOCATION_DENIAL",
            "recorded_utc": _utc(),
            "allocated_chunks": len(held),
            "memory_events": _read_cgroup_events(),
        })
        deadline = time.monotonic() + 2
        stopped = handle.stop(deadline)
        if stopped:
            handle.close()
        else:
            _RETAINED_HANDLES.append(handle)
        return 70


def _recovery_snapshot(connection, run_id: UUID):
    from sqlalchemy import text

    return connection.execute(text("""
        SELECT clock_timestamp() AS db_now,j.project_id,j.run_id,j.state,j.stage,
               j.attempt_count,j.generation,j.attempt_token,j.lease_expires_at,
               j.last_error_code,a.claim_request_id,a.claimed_at,a.lease_at_claim,
               a.error_code AS attempt_error_code,a.outcome,
               r.ocr_result_id AS run_ocr_result_id,
               r.verification_result_id AS run_verification_result_id,
               EXISTS(SELECT 1 FROM ocr_results o WHERE o.run_id=j.run_id) AS has_ocr_result,
               EXISTS(SELECT 1 FROM verification_results v WHERE v.run_id=j.run_id) AS has_verification_result
        FROM verification_jobs j
        JOIN verification_runs r ON r.project_id=j.project_id AND r.id=j.run_id
        JOIN verification_attempts a ON a.project_id=j.project_id AND a.run_id=j.run_id
             AND a.generation=j.generation AND a.attempt_token=j.attempt_token
        WHERE j.run_id=:run_id
    """), {"run_id": run_id}).mappings().one()


def _recover_mode(args) -> int:
    root = _inside_root()
    sources = _require_exact_sources(root)
    database = _safe_database_name(args.database)
    evidence = Path(args.evidence)

    from sqlalchemy import create_engine
    from backend.app.services.ocr_types import JobFence, LostFence
    from backend.app.services.verification_jobs import VerificationJobService

    _, database_url = _database_urls(database)
    engine = create_engine(database_url, isolation_level="REPEATABLE READ",
                           connect_args={"client_encoding": "utf8", "connect_timeout": 5})
    run_id = UUID(args.run_id)
    oom_ready = json.loads((evidence / "oom-ready.json").read_text(encoding="utf-8"))
    wait_started = time.monotonic()
    with engine.connect() as connection:
        first = _recovery_snapshot(connection, run_id)
    if first["state"] != "RUNNING" or first["generation"] != 1 or first["outcome"] != "STARTED":
        raise HarnessError("generation-1 lease was not left live by the dead parent")
    if (_fence_digest(first) != oom_ready.get("fence_identity_sha256")
            or first["lease_expires_at"].isoformat() != oom_ready.get("lease_expires_at")):
        raise HarnessError("post-death generation-1 fence/lease differs from OOM-ready evidence")
    if (first["last_error_code"] is not None or first["attempt_error_code"] is not None
            or first["run_ocr_result_id"] is not None or first["run_verification_result_id"] is not None
            or first["has_ocr_result"] or first["has_verification_result"]):
        raise HarnessError("dead parent unexpectedly persisted failure or results")
    original_identity = (
        first["project_id"], first["run_id"], first["generation"], first["attempt_token"],
        first["claim_request_id"], first["lease_expires_at"], first["claimed_at"],
        first["lease_at_claim"],
    )

    # Poll only DB clock and this exact row.  There is no lease rewrite, fake
    # clock, shared-database mutation, or claim attempt before real equality.
    while True:
        with engine.connect() as connection:
            current = _recovery_snapshot(connection, run_id)
        current_identity = (
            current["project_id"], current["run_id"], current["generation"],
            current["attempt_token"], current["claim_request_id"], current["lease_expires_at"],
            current["claimed_at"], current["lease_at_claim"],
        )
        if current_identity != original_identity:
            raise HarnessError("generation-1 fence or original lease changed while awaiting expiry")
        if (current["state"] != "RUNNING" or current["stage"] != "OCR"
                or current["outcome"] != "STARTED" or current["last_error_code"] is not None
                or current["attempt_error_code"] is not None
                or current["run_ocr_result_id"] is not None
                or current["run_verification_result_id"] is not None
                or current["has_ocr_result"] or current["has_verification_result"]):
            raise HarnessError("generation-1 job changed before real lease expiry")
        if current["db_now"] >= current["lease_expires_at"]:
            expired = current
            break
        if time.monotonic() - wait_started > 90:
            raise HarnessError("real 60-second lease did not expire within the 90-second observation bound")
        remaining = (current["lease_expires_at"] - current["db_now"]).total_seconds()
        time.sleep(max(0.05, min(1.0, remaining)))
    if (expired["state"] != "RUNNING" or expired["stage"] != "OCR"
            or expired["generation"] != 1 or expired["outcome"] != "STARTED"
            or expired["last_error_code"] is not None or expired["attempt_error_code"] is not None
            or expired["run_ocr_result_id"] is not None
            or expired["run_verification_result_id"] is not None
            or expired["has_ocr_result"] or expired["has_verification_result"]):
        raise HarnessError("another actor changed the unique diagnostic job before takeover")

    stale = JobFence(expired["project_id"], expired["run_id"], expired["generation"],
                     expired["attempt_token"], expired["claim_request_id"])
    helpers = runpy.run_path(str(root / "tests/backend/test_ocr_jobs.py"))
    factory = helpers["_factory"](engine)
    service = VerificationJobService(factory)
    replacement = service.claim()
    if replacement is None or replacement.fence.run_id != run_id or replacement.fence.generation != 2:
        raise HarnessError("expired generation-1 job was not recovered as generation 2")
    stale_denials = {}
    for operation in ("renew", "stage"):
        try:
            getattr(service, operation)(stale)
        except LostFence:
            stale_denials[operation] = "LostFence"
        else:
            raise HarnessError(f"stale generation-1 {operation} was not fenced")
    run, job, attempts = helpers["_rows"](factory, replacement.fence.project_id, run_id)
    if [attempt.outcome for attempt in attempts] != ["EXPIRED", "STARTED"]:
        raise HarnessError("durable attempt history does not show expiry then takeover")
    if job.generation != job.attempt_count or job.generation != 2:
        raise HarnessError("recovered job generation/attempt count mismatch")
    if (run.status, run.stage, job.state, job.stage) != ("RUNNING", "OCR", "RUNNING", "OCR"):
        raise HarnessError("generation-2 takeover did not preserve RUNNING/OCR state")
    if ([attempt.error_code for attempt in attempts] != ["LEASE_EXPIRED", None]
            or run.error_code is not None or job.last_error_code is not None
            or run.ocr_result_id is not None or run.verification_result_id is not None):
        raise HarnessError("takeover error/result invariants are not exact")
    with engine.connect() as connection:
        after = _recovery_snapshot(connection, run_id)
    if (after["has_ocr_result"] or after["has_verification_result"]
            or after["run_ocr_result_id"] is not None
            or after["run_verification_result_id"] is not None):
        raise HarnessError("takeover created or linked result rows")
    if replacement.lease_expires_at - attempts[1].claimed_at != __import__("datetime").timedelta(seconds=60):
        raise HarnessError("replacement did not receive a fresh real 60-second lease")
    _atomic_json(evidence / "recovery.json", {
        "schema_version": 1,
        "phase": "durable_lease_takeover_complete",
        "database": database,
        "project_id": replacement.fence.project_id,
        "run_id": run_id,
        "first_recovery_db_observed_at": first["db_now"],
        "original_lease_expires_at": first["lease_expires_at"],
        "expiry_observed_at_db_clock": expired["db_now"],
        "wait_elapsed_seconds": time.monotonic() - wait_started,
        "pre_takeover_state": expired["state"],
        "pre_takeover_generation": expired["generation"],
        "pre_takeover_attempt_outcome": expired["outcome"],
        "pre_takeover_last_error_code": expired["last_error_code"],
        "pre_takeover_has_results": expired["has_ocr_result"] or expired["has_verification_result"],
        "replacement_generation": replacement.fence.generation,
        "replacement_attempt_count": replacement.attempt_count,
        "replacement_claimed_at": attempts[1].claimed_at,
        "replacement_lease_expires_at": replacement.lease_expires_at,
        "replacement_lease_seconds": (replacement.lease_expires_at - attempts[1].claimed_at).total_seconds(),
        "run_status": run.status,
        "job_state": job.state,
        "attempt_outcomes": [attempt.outcome for attempt in attempts],
        "attempt_error_codes": [attempt.error_code for attempt in attempts],
        "stale_generation_denials": stale_denials,
        "source_sha256": sources,
        "ended_utc": _utc(),
    })
    engine.dispose()
    return 0


def _cleanup_mode(args) -> int:
    _inside_root()
    database = _safe_database_name(args.database)
    evidence = Path(args.evidence)
    from sqlalchemy import create_engine, text

    authority_path = evidence / "database-created.json"
    if not authority_path.is_file():
        raise HarnessError("database ownership marker absent; database retained unresolved")
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    if (authority.get("owner"), authority.get("nonce"), authority.get("database")) != (
            OWNER_LABEL, args.nonce, database):
        raise HarnessError("database file ownership marker mismatch; database retained")
    expected_oid = authority.get("database_oid")
    if type(expected_oid) is not int or expected_oid <= 0:
        raise HarnessError("database ownership OID invalid; database retained")

    admin_url, database_url = _database_urls(database)
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5})
    with admin.connect() as connection:
        actual_oid = connection.scalar(text("SELECT oid FROM pg_database WHERE datname=:name"),
                                       {"name": database})
    if actual_oid != expected_oid:
        admin.dispose()
        raise HarnessError("database name/OID ownership mismatch; database retained")
    owned = create_engine(database_url, connect_args={"connect_timeout": 5})
    with owned.connect() as connection:
        marker = connection.execute(text("""
            SELECT owner,nonce,database_name,database_oid
            FROM qa_parent_oom_diagnostic_owner WHERE singleton=true
        """)).mappings().one_or_none()
        current_oid = connection.scalar(text("SELECT oid FROM pg_database WHERE datname=current_database()"))
    owned.dispose()
    if marker is None or (marker["owner"], marker["nonce"], marker["database_name"],
                          marker["database_oid"], current_oid) != (
            OWNER_LABEL, args.nonce, database, expected_oid, expected_oid):
        admin.dispose()
        raise HarnessError("database internal ownership marker mismatch; database retained")
    with admin.connect() as connection:
        connection.exec_driver_sql(f'DROP DATABASE "{database}" WITH (FORCE)')
    with admin.connect() as connection:
        remains = bool(connection.scalar(text("SELECT 1 FROM pg_database WHERE datname=:name"),
                                         {"name": database}))
    admin.dispose()
    if remains:
        raise HarnessError("exact owned diagnostic database remains after cleanup")
    _atomic_json(evidence / "cleanup.json", {
        "schema_version": 1, "owner": OWNER_LABEL, "nonce": args.nonce,
        "database": database, "database_oid": expected_oid,
        "removed": True, "ended_utc": _utc(),
    })
    return 0


def _host_common_docker(args, *, name: str, database: str, evidence: Path,
                        script: Path, postgres_id: str, nonce: str) -> list[str]:
    command = [
        "docker", "run",
        "--name", name,
        "--label", f"qa.visual.owner={OWNER_LABEL}",
        "--label", f"qa.visual.nonce={nonce}",
        "--memory", str(MEMORY_BYTES),
        "--memory-swap", str(MEMORY_BYTES),
        "--network", "container:" + postgres_id,
        "--env-file", str(args.env_file),
        "-e", "DATABASE_HOST=127.0.0.1",
        "-e", "DATABASE_PORT=5432",
        "-e", "POSTGRES_DB=" + database,
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        "--read-only",
        "--tmpfs", "/tmp:rw,nosuid,nodev,size=32m",
        "--mount", f"type=bind,source={evidence},target=/evidence",
        "--mount", f"type=bind,source={script},target=/diagnostic/harness.py,readonly",
    ]
    command.extend([args.image_id, "python", "/diagnostic/harness.py"])
    return command


def _start_owned(command: list[str], name: str, nonce: str) -> str:
    detached = list(command)
    detached.insert(2, "-d")
    try:
        started = _run(detached, timeout=30)
        container_id = started.stdout.strip()
    except (HarnessError, subprocess.TimeoutExpired):
        # docker run may create/start the named container before its CLI is
        # interrupted. Recover only this exact named/labelled identity through
        # formatted nonsecret fields so the caller can stop/remove it.
        if not _container_exists(name):
            raise
        container_id = _docker_inspect(name, ".Id")
    if not re.fullmatch(r"[0-9a-f]{64}", container_id):
        raise HarnessError("Docker did not yield a recoverable full container ID")
    if not _owned_container(name, container_id, nonce):
        raise HarnessError("started container identity/ownership could not be pinned")
    return container_id


def _wait_owned(container_id: str, timeout: float) -> int | None:
    try:
        waited = _run(["docker", "wait", container_id], timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return None
    value = waited.stdout.strip()
    return int(value) if re.fullmatch(r"-?[0-9]+", value) else None


def _creation_authority(evidence: Path, database: str, nonce: str) -> dict | None:
    path = evidence / "database-created.json"
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if (value.get("owner"), value.get("nonce"), value.get("database")) != (
            OWNER_LABEL, nonce, database):
        return None
    if type(value.get("database_oid")) is not int or value["database_oid"] <= 0:
        return None
    return value


def _host_mode(args) -> int:
    script = Path(__file__).resolve()
    root = script.parents[2]
    report_root = (root / ".orchestration/reports").resolve()
    evidence = args.evidence_dir.resolve()
    if evidence.parent != report_root or not evidence.name.startswith(
            "BACKEND-OCR-001-native-diagnostic-parent-oom-evidence-03-"):
        raise HarnessError("evidence directory must be a new direct child of .orchestration/reports with the approved prefix")
    if evidence.exists():
        raise HarnessError("immutable evidence directory already exists")
    if not args.env_file.is_file():
        raise HarnessError("env file is absent; its values were not read or logged")
    if args.image != IMAGE_TAG or args.image_id != IMAGE_ID or not IMAGE_ID_RE.fullmatch(args.image_id):
        raise HarnessError("image tag/ID differs from the reviewed immutable 20260925b image")
    postgres_ref = _safe_container_ref(args.postgres_container)
    local_before = _require_exact_sources(root)
    evidence.mkdir(parents=False)

    manifest = {
        "schema_version": 1,
        "status": "RUNNING",
        "started_utc": _utc(),
        "image_tag": args.image,
        "expected_image_id": args.image_id,
        "memory_bytes": MEMORY_BYTES,
        "memory_swap_bytes": MEMORY_BYTES,
        "extra_swap_bytes": 0,
        "network_mode": "container:<validated-existing-postgres-id>",
        "env_file": "provided to containers; path and values omitted",
        "evidence_persistence": {
            "file_fsync_before_replace": True,
            "directory_fsync": "POSIX inner modes only",
            "host_limitation": "Windows host does not provide this harness a directory-fsync proof",
        },
        "source_before": local_before,
        "script_sha256": _sha256(script),
        "executions": [],
        "cleanup": {},
    }
    _atomic_json(evidence / "manifest.json", manifest)

    image_id = _run(["docker", "image", "inspect", args.image, "--format", "{{.Id}}"]).stdout.strip()
    if image_id != args.image_id:
        raise HarnessError("reviewed image tag no longer resolves to the approved immutable ID")
    postgres_id = _docker_inspect(postgres_ref, ".Id")
    if _docker_inspect(postgres_ref, ".State.Running").lower() != "true":
        raise HarnessError("existing PostgreSQL container is not running")

    nonce = uuid4().hex
    database = "qa_backend_parent_oom_" + nonce
    setup_name = "qa-ocr-parent-oom-setup-" + nonce[:12]
    oom_name = "qa-ocr-parent-oom-" + nonce[:12]
    recovery_name = "qa-ocr-parent-oom-recovery-" + nonce[:12]
    cleanup_name = "qa-ocr-parent-oom-cleanup-" + nonce[:12]
    for name in (setup_name, oom_name, recovery_name, cleanup_name):
        if _container_exists(name):
            raise HarnessError("unique diagnostic container name unexpectedly exists")
    manifest.update(nonce=nonce, database=database, postgres_container_id=postgres_id,
                    resolved_image_id=image_id, oom_container_name=oom_name)
    _atomic_json(evidence / "manifest.json", manifest)

    owned_ids = {"setup": None, "oom": None, "recovery": None, "cleanup": None}
    launch_uncertain = {"setup": False, "oom": False, "recovery": False, "cleanup": False}
    run_id = None
    primary_error = None
    try:
        setup = _host_common_docker(args, name=setup_name, database=database, evidence=evidence,
                                    script=script, postgres_id=postgres_id, nonce=nonce)
        setup.extend(["setup", "--database", database, "--nonce", nonce,
                      "--evidence", "/evidence"])
        launch_uncertain["setup"] = True
        owned_ids["setup"] = _start_owned(setup, setup_name, nonce)
        setup_exit = _wait_owned(owned_ids["setup"], 90)
        manifest["executions"].append({"phase": "setup", "container_id": owned_ids["setup"],
                                       "exit_code": setup_exit})
        manifest["cleanup"]["setup_container"] = _stop_and_remove_owned(
            setup_name, owned_ids["setup"], nonce)
        owned_ids["setup"] = None
        launch_uncertain["setup"] = False
        if setup_exit != 0 or not (evidence / "setup.json").is_file():
            raise HarnessError("setup container failed; raw output omitted to protect env-file values")
        setup_record = json.loads((evidence / "setup.json").read_text(encoding="utf-8"))
        run_id = setup_record["run_id"]

        oom = _host_common_docker(args, name=oom_name, database=database, evidence=evidence,
                                  script=script, postgres_id=postgres_id, nonce=nonce)
        oom.extend(["oom", "--database", database, "--run-id", run_id,
                    "--evidence", "/evidence"])
        launch_uncertain["oom"] = True
        owned_ids["oom"] = _start_owned(oom, oom_name, nonce)
        wait_exit = _wait_owned(owned_ids["oom"], 45)
        if wait_exit is None:
            raise HarnessError("OOM container did not terminate naturally within the causal wait bound")
        # No host stop is permitted before this inspect: a causal pass requires
        # natural docker wait=137 from the controlled container-level OOM.
        oom_id = owned_ids["oom"]
        inspect_record = {
            "schema_version": 1,
            "recorded_utc": _utc(),
            "container_name": _docker_inspect(oom_id, ".Name").lstrip("/"),
            "container_id": _docker_inspect(oom_id, ".Id"),
            "image_id": _docker_inspect(oom_id, ".Image"),
            "owner_label": _docker_inspect(oom_id, 'index .Config.Labels "qa.visual.owner"'),
            "nonce_label": _docker_inspect(oom_id, 'index .Config.Labels "qa.visual.nonce"'),
            "oom_killed": _docker_inspect(oom_id, ".State.OOMKilled").lower() == "true",
            "exit_code": int(_docker_inspect(oom_id, ".State.ExitCode")),
            "docker_wait_exit_code": wait_exit,
            "state_error": _docker_inspect(oom_id, ".State.Error"),
            "started_at": _docker_inspect(oom_id, ".State.StartedAt"),
            "finished_at": _docker_inspect(oom_id, ".State.FinishedAt"),
            "memory_bytes": int(_docker_inspect(oom_id, ".HostConfig.Memory")),
            "memory_swap_bytes": int(_docker_inspect(oom_id, ".HostConfig.MemorySwap")),
            "network_mode": _docker_inspect(oom_id, ".HostConfig.NetworkMode"),
            "environment_inspected": False,
            "host_stop_before_inspect": False,
            "attribution_limit": (
                "container-level OOMKilled/exit137 proves PID1 container death, but does not "
                "independently prove the tiny child was not an earlier OOM victim"
            ),
        }
        _atomic_json(evidence / "oom-container-inspect.json", inspect_record)
        manifest["executions"].append({"phase": "parent_oom", "container_id": oom_id,
                                       "oom_killed": inspect_record["oom_killed"],
                                       "exit_code": inspect_record["exit_code"]})
        if not (evidence / "oom-ready.json").is_file():
            raise HarnessError("parent died before publishing the controlled pre-OOM boundary")
        if not inspect_record["oom_killed"] or inspect_record["exit_code"] != 137 or wait_exit != 137:
            raise HarnessError("Docker did not prove parent OOM death with OOMKilled=true and exit 137")
        if inspect_record["image_id"] != args.image_id:
            raise HarnessError("OOM container did not use the pinned image ID")
        if (inspect_record["memory_bytes"], inspect_record["memory_swap_bytes"]) != (MEMORY_BYTES, MEMORY_BYTES):
            raise HarnessError("OOM container limits differ from reviewed 512MiB/no-extra-swap values")
        if inspect_record["network_mode"] != "container:" + postgres_id:
            raise HarnessError("OOM container did not share only the pinned PostgreSQL network namespace")

        manifest["cleanup"]["oom_container"] = _stop_and_remove_owned(oom_name, oom_id, nonce)
        owned_ids["oom"] = None
        launch_uncertain["oom"] = False

        recovery = _host_common_docker(args, name=recovery_name, database=database, evidence=evidence,
                                       script=script, postgres_id=postgres_id, nonce=nonce)
        recovery.extend(["recover", "--database", database, "--run-id", run_id,
                         "--evidence", "/evidence"])
        launch_uncertain["recovery"] = True
        owned_ids["recovery"] = _start_owned(recovery, recovery_name, nonce)
        recovery_exit = _wait_owned(owned_ids["recovery"], 110)
        manifest["executions"].append({"phase": "lease_recovery",
                                       "container_id": owned_ids["recovery"],
                                       "exit_code": recovery_exit})
        manifest["cleanup"]["recovery_container"] = _stop_and_remove_owned(
            recovery_name, owned_ids["recovery"], nonce)
        owned_ids["recovery"] = None
        launch_uncertain["recovery"] = False
        if recovery_exit != 0 or not (evidence / "recovery.json").is_file():
            raise HarnessError("recovery container failed; raw output omitted to protect env-file values")
        manifest["status"] = "PASS"
    except BaseException as exc:
        primary_error = exc
        manifest["status"] = "FAIL"
        manifest["error_type"] = type(exc).__name__
    finally:
        names = {"setup": setup_name, "oom": oom_name, "recovery": recovery_name}
        for phase in ("setup", "oom", "recovery"):
            container_id = owned_ids[phase]
            if launch_uncertain[phase] and container_id is None:
                # Recover only an exact already-visible owned identity. Absence
                # cannot clear launch uncertainty because creation may be late.
                try:
                    if _container_exists(names[phase]):
                        candidate = _docker_inspect(names[phase], ".Id")
                        if not _owned_container(names[phase], candidate, nonce):
                            raise HarnessError("late container ownership mismatch")
                        owned_ids[phase] = candidate
                        container_id = candidate
                except BaseException as recovery_error:
                    manifest["cleanup"][phase + "_launch_recovery_error_type"] = type(recovery_error).__name__
            if container_id is None:
                continue
            try:
                manifest["cleanup"][phase + "_container"] = _stop_and_remove_owned(
                    names[phase], container_id, nonce)
                owned_ids[phase] = None
                launch_uncertain[phase] = False
            except BaseException as cleanup_error:
                manifest["cleanup"][phase + "_container_error_type"] = type(cleanup_error).__name__
                if primary_error is None:
                    primary_error = cleanup_error
                    manifest["status"] = "FAIL"
        authority = _creation_authority(evidence, database, nonce)
        if any(launch_uncertain[phase] for phase in ("setup", "oom", "recovery")):
            manifest["cleanup"]["database_removed"] = False
            manifest["cleanup"]["database_status"] = "RETAINED_UNRESOLVED_WRITER"
        elif authority is None:
            manifest["cleanup"]["database_removed"] = False
            manifest["cleanup"]["database_status"] = "RETAINED_CREATION_OR_MARKER_UNCERTAIN"
        else:
            cleanup = _host_common_docker(args, name=cleanup_name, database=database, evidence=evidence,
                                          script=script, postgres_id=postgres_id, nonce=nonce)
            cleanup.extend(["cleanup", "--database", database, "--nonce", nonce,
                            "--evidence", "/evidence"])
            try:
                launch_uncertain["cleanup"] = True
                owned_ids["cleanup"] = _start_owned(cleanup, cleanup_name, nonce)
                cleanup_exit = _wait_owned(owned_ids["cleanup"], 45)
                manifest["cleanup"]["database_exit_code"] = cleanup_exit
                manifest["cleanup"]["cleanup_container"] = _stop_and_remove_owned(
                    cleanup_name, owned_ids["cleanup"], nonce)
                owned_ids["cleanup"] = None
                launch_uncertain["cleanup"] = False
                manifest["cleanup"]["database_removed"] = (
                    cleanup_exit == 0 and (evidence / "cleanup.json").is_file()
                )
                if not manifest["cleanup"]["database_removed"] and primary_error is None:
                    primary_error = HarnessError("exact owned diagnostic database cleanup failed")
                    manifest["status"] = "FAIL"
            except BaseException as cleanup_error:
                manifest["cleanup"]["database_error_type"] = type(cleanup_error).__name__
                if owned_ids["cleanup"] is not None:
                    try:
                        manifest["cleanup"]["cleanup_container"] = _stop_and_remove_owned(
                            cleanup_name, owned_ids["cleanup"], nonce)
                        owned_ids["cleanup"] = None
                    except BaseException as container_error:
                        manifest["cleanup"]["cleanup_container_error_type"] = type(container_error).__name__
                if launch_uncertain["cleanup"]:
                    manifest["cleanup"]["cleanup_launch_status"] = "UNRESOLVED"
                if primary_error is None:
                    primary_error = cleanup_error
                    manifest["status"] = "FAIL"
        try:
            manifest["source_after"] = _source_hashes(root)
            manifest["source_unchanged"] = manifest["source_after"] == local_before
            if not manifest["source_unchanged"] and primary_error is None:
                primary_error = HarnessError("tracked source changed during diagnostic")
                manifest["status"] = "FAIL"
        except BaseException as source_error:
            manifest["source_after_error_type"] = type(source_error).__name__
            if primary_error is None:
                primary_error = source_error
                manifest["status"] = "FAIL"
        manifest["ended_utc"] = _utc()
        _atomic_json(evidence / "manifest.json", manifest)
    if primary_error is not None:
        raise primary_error
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    host = subparsers.add_parser("host", help="reviewed parent-host orchestrator")
    host.add_argument("--image", required=True)
    host.add_argument("--image-id", required=True)
    host.add_argument("--postgres-container", required=True)
    host.add_argument("--env-file", required=True, type=Path)
    host.add_argument("--evidence-dir", required=True, type=Path)
    for mode in ("setup", "oom", "recover", "cleanup"):
        inner = subparsers.add_parser(mode, help=argparse.SUPPRESS)
        inner.add_argument("--database", required=True)
        inner.add_argument("--evidence", required=True)
        if mode in {"setup", "cleanup"}:
            inner.add_argument("--nonce", required=True)
        if mode in {"oom", "recover"}:
            inner.add_argument("--run-id", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    return {
        "host": _host_mode,
        "setup": _setup_mode,
        "oom": _oom_mode,
        "recover": _recover_mode,
        "cleanup": _cleanup_mode,
    }[args.mode](args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HarnessError as exc:
        # Never print connection URLs, environment values, Docker raw inspect,
        # or nested exception text.  Detailed bounded facts live in JSON files.
        print(f"HARNESS_ERROR:{type(exc).__name__}", file=sys.stderr)
        raise SystemExit(2)
