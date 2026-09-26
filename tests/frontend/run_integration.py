"""Run the real Frontend client against FastAPI + an isolated PostgreSQL DB.

Usage from project root: .venv/Scripts/python.exe tests/frontend/run_integration.py
Add --serve for manual browser QA on loopback port 8001 (Ctrl+C cleans up).
Add --verify-upload-web --isolated-postgres for the synthetic uploader -> Web proof.
Add --verify-ocr-web --isolated-postgres only after Backend03 and OCR05 report matching readiness.
Never migrates or clears the configured user database.
"""
from hashlib import sha256
from io import BytesIO
import json
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

import httpx
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
from sqlalchemy import create_engine, text, URL
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
import uvicorn
from backend.app.config import get_settings
from backend.app.main import app
from backend.app.api.dependencies import get_session, get_storage
from backend.app.storage.local import LocalStorage
from agent.screenshot_upload.origin import BindingGuard, initialize_binding
from agent.screenshot_upload.producer import Producer


EVIDENCE = ROOT / ".orchestration" / "reports" / "FRONTEND-UPLOAD-VERIFY-001-review-rework-04-evidence.json"
OCR_EVIDENCE = ROOT / ".orchestration" / "reports" / "FRONTEND-OCR-VERIFY-001-04-evidence.json"
HARNESS_PATH = Path(__file__).resolve()
CONTRACT_TEST_PATH = ROOT / "frontend" / "tests" / "integration" / "contract.test.ts"
SNAPSHOT_FILES = (
    "backend/app/api/v1/screenshots.py",
    "backend/app/services/screenshots.py",
    "backend/app/services/upload_receipts.py",
    "backend/app/storage/local.py",
    "agent/screenshot_upload/producer.py",
    "agent/screenshot_upload/client.py",
    "frontend/components/screenshots.tsx",
    "frontend/lib/api.ts",
    "tests/frontend/run_integration.py",
)
OCR_BACKEND_MANIFEST = ROOT / ".orchestration" / "reports" / "BACKEND-OCR-001-runtime-resume-source-manifest.txt"
OCR_WORKER_MANIFEST = ROOT / ".orchestration" / "reports" / "OCR-001-05-source-manifest.txt"
OCR_FIXTURE = ROOT / "tests" / "ocr" / "fixtures" / "runtime" / "ko.png"


def _backend_source_manifest() -> dict:
    files = subprocess.check_output(
        ["rg", "--files", "backend", "tests/backend"], cwd=ROOT, text=True
    ).splitlines()
    paths = sorted({path.replace("\\", "/") for path in [*files, "pyproject.toml"]})
    manifest = "".join(
        f"{path} {sha256((ROOT / path).read_bytes()).hexdigest()}\n" for path in paths
    ).encode("utf-8")
    return {"file_count": len(paths), "aggregate_sha256": sha256(manifest).hexdigest()}


def _uploader_source_manifest() -> dict:
    files = subprocess.check_output(
        ["rg", "--files", "agent/screenshot_upload", "tests/upload"], cwd=ROOT, text=True
    ).splitlines()
    paths = sorted({path.replace("\\", "/") for path in [*files, "pyproject.toml"]})
    manifest = "".join(
        f"{path} {sha256((ROOT / path).read_bytes()).hexdigest()}\n" for path in paths
    ).encode("utf-8")
    return {"file_count": len(paths), "aggregate_sha256": sha256(manifest).hexdigest()}


def _synthetic_png(label: str, color: tuple[int, int, int]) -> bytes:
    stream = BytesIO()
    image = Image.new("RGB", (320, 180), color)
    canvas = ImageDraw.Draw(image)
    canvas.rectangle((12, 12, 307, 167), outline=(255, 255, 255), width=4)
    canvas.text((28, 72), label, fill=(255, 255, 255))
    image.save(stream, format="PNG")
    return stream.getvalue()


def _contains_empty_string(value) -> bool:
    if value == "":
        return True
    if isinstance(value, dict):
        return any(_contains_empty_string(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_empty_string(child) for child in value)
    return False


def _created(client: httpx.Client, path: str, body: dict) -> dict:
    response = client.post(path, json=body)
    if response.status_code != 201:
        raise RuntimeError(f"POST {path} returned {response.status_code}: {response.text}")
    return response.json()


def _stop_process(process: subprocess.Popen | None) -> str:
    if process is None:
        return "not_started"
    was_running = process.poll() is None
    if was_running:
        process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    prefix = "terminated" if was_running else "already_exited"
    return f"{prefix}_exit_{process.returncode}"


def _wait_http(url: str, process: subprocess.Popen, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"process exited during startup with {process.returncode}")
        try:
            if httpx.get(url, timeout=0.5).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    raise RuntimeError(f"timed out waiting for {url}")


def _prepare_upload_verification(origin: str, spool_root: Path, storage_root: Path, engine) -> dict:
    agent_bytes = _synthetic_png("SYNTHETIC AGENT QA", (20, 82, 125))
    automation_bytes = _synthetic_png("SYNTHETIC AUTOMATION QA", (30, 112, 74))
    manual_bytes = _synthetic_png("SYNTHETIC MANUAL QA", (112, 45, 97))
    agent_metadata = {
        "run_id": str(uuid4()),
        "device": "Windows 합성 장치 😀",
        "resolution": {"width": 320, "height": 180},
        "scenario": "가입 / 初回起動 / démarrage",
        "checkpoint": "환영 화면 · ようこそ · bienvenue",
        "screen_state": "준비됨 e\u0301",
        "empty_string": "",
        "nested": {
            "한국어": {"문구": "안녕하세요", "상태": ["표시", True, None]},
            "日本語": {"文言": "ようこそ", "段階": 2},
            "العربية": {"النص": "مرحبا", "اتجاه": "rtl"},
            "emoji": ["😀", "🧪", {"보존": "완료"}],
        },
    }
    automation_metadata = {
        "run_id": str(uuid4()),
        "device": "Linux 자동화 장치 🧪",
        "resolution": {"width": 320, "height": 180},
        "scenario": "자동화 / 自動化 / أتمتة",
        "checkpoint": "빈 문자열 보존 / 空文字列",
        "screen_state": "",
        "empty_string": "",
        "nested": {
            "한국어": {"빈문자열": "", "값": "자동화"},
            "日本語": {"空文字列": "", "値": "自動"},
            "emoji": ["🤖", {"empty": ""}],
        },
    }
    with httpx.Client(base_url=origin, timeout=20) as client:
        project = _created(client, "/api/v1/projects", {"slug": "web-upload-" + uuid4().hex, "name": "실제 Web 업로드 검증 😀"})
        prefix = f"/api/v1/projects/{project['id']}"
        build = _created(client, prefix + "/builds", {"label": "verify-2026.09"})
        locale = _created(client, prefix + "/locales", {"code": "ko-KR", "name": "한국어 / 日本語"})
        category = _created(client, prefix + "/categories", {"slug": "onboarding", "name": "가입 흐름"})
        situation = _created(client, prefix + "/situations", {"category_id": category["id"], "slug": "welcome", "name": "환영 / ようこそ"})

    initialize_binding(spool_root, origin)
    guard = BindingGuard(spool_root, origin)
    agent_item = Producer(spool_root, guard).publish(
        agent_bytes,
        project_id=project["id"],
        original_filename="합성-agent-ようこそ-😀.png",
        request={
            "build_id": build["id"], "locale_id": locale["id"],
            "category_id": category["id"], "situation_id": situation["id"],
            "source": "agent", "metadata_version": 1, "metadata": agent_metadata,
        },
    )
    automation_item = Producer(spool_root, guard).publish(
        automation_bytes,
        project_id=project["id"],
        original_filename="합성-automation-自動化-🤖.png",
        request={
            "build_id": build["id"], "locale_id": locale["id"],
            "category_id": category["id"], "situation_id": situation["id"],
            "source": "automation", "metadata_version": 1, "metadata": automation_metadata,
        },
    )
    uploader = subprocess.run(
        [sys.executable, "-m", "agent.screenshot_upload", "run", "--spool", str(spool_root), "--backend-origin", origin],
        cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
    )
    if uploader.returncode != 0:
        raise RuntimeError(f"uploader CLI failed: {uploader.stdout}\n{uploader.stderr}")

    with httpx.Client(base_url=origin, timeout=20) as client:
        listing_response = client.get(prefix + "/screenshots")
        listing_response.raise_for_status()
        listing = listing_response.json()
        if listing["total"] != 2:
            raise RuntimeError(f"expected two queued uploads before manual smoke, found {listing['total']}")

        def uploaded(item, expected_source: str, expected_metadata: dict, expected_bytes: bytes) -> dict:
            listed = next(row for row in listing["items"] if row["client_upload_id"] == item.client_upload_id)
            detail_response = client.get(prefix + f"/screenshots/{listed['id']}")
            detail_response.raise_for_status()
            detail = detail_response.json()
            content_response = client.get(prefix + f"/screenshots/{listed['id']}/content")
            content_response.raise_for_status()
            expected_hash = sha256(expected_bytes).hexdigest()
            if detail["source"] != expected_source or detail["metadata_version"] != 1:
                raise RuntimeError(f"{expected_source} detail lost source/version")
            if detail["metadata"] != expected_metadata or not _contains_empty_string(expected_metadata):
                raise RuntimeError(f"{expected_source} detail lost empty-string/nested Unicode metadata")
            if detail["client_upload_id"] != item.client_upload_id or listed != detail:
                raise RuntimeError(f"{expected_source} identity/list/detail did not round-trip")
            if content_response.content != expected_bytes or detail["file_hash"] != expected_hash:
                raise RuntimeError(f"{expected_source} original bytes/hash did not round-trip")
            return {
                "producer_client_upload_id": item.client_upload_id,
                "producer_file_hash": item.file_hash,
                "producer_manifest_sha256": item.manifest_sha256,
                "detail": detail,
                "content_sha256": sha256(content_response.content).hexdigest(),
                "content_exact": content_response.content == expected_bytes,
            }

        agent_evidence = uploaded(agent_item, "agent", agent_metadata, agent_bytes)
        automation_evidence = uploaded(
            automation_item, "automation", automation_metadata, automation_bytes
        )

        manual_metadata = {
            "build_id": build["id"], "locale_id": locale["id"],
            "category_id": category["id"], "situation_id": situation["id"],
            "source": "manual", "metadata_version": 1,
            "metadata": {
                "note": "수동 원본 보존 · 手動 · e\u0301",
                "empty_string": "",
                "nested": {"kept": [True, None, "😀", ""]},
            },
        }
        manual_response = client.post(
            prefix + "/screenshots",
            files={"file": ("수동-원본-保持-😀.png", manual_bytes, "image/png")},
            data={"metadata": json.dumps(manual_metadata, ensure_ascii=False, separators=(",", ":"))},
        )
        if manual_response.status_code != 201:
            raise RuntimeError(f"manual multipart returned {manual_response.status_code}: {manual_response.text}")
        manual_created = manual_response.json()
        manual_detail_response = client.get(prefix + f"/screenshots/{manual_created['id']}")
        manual_detail_response.raise_for_status()
        manual = manual_detail_response.json()
        final_listing_response = client.get(prefix + "/screenshots")
        final_listing_response.raise_for_status()
        final_listing = final_listing_response.json()
        manual_listed = next(row for row in final_listing["items"] if row["id"] == manual["id"])
        manual_content = client.get(prefix + f"/screenshots/{manual['id']}/content")
        manual_content.raise_for_status()
        if (
            final_listing["total"] != 3
            or manual_created != manual
            or manual_listed != manual
            or manual["client_upload_id"] is not None
            or manual["source"] != "manual"
        ):
            raise RuntimeError("manual source/client_upload_id compatibility failed")
        if (
            manual["metadata"] != manual_metadata["metadata"]
            or not _contains_empty_string(manual["metadata"])
            or manual["file_hash"] != sha256(manual_bytes).hexdigest()
            or manual_content.content != manual_bytes
        ):
            raise RuntimeError("manual Unicode metadata/original bytes did not round-trip")

    stored = [path for path in storage_root.rglob("*") if path.is_file()]
    if len(stored) != 3:
        raise RuntimeError(f"expected three stored originals, found {len(stored)}")
    stored_hashes = sorted(sha256(path.read_bytes()).hexdigest() for path in stored)
    expected_hashes = sorted([
        sha256(agent_bytes).hexdigest(),
        sha256(automation_bytes).hexdigest(),
        sha256(manual_bytes).hexdigest(),
    ])
    if stored_hashes != expected_hashes:
        raise RuntimeError("stored object bytes differ from the three upload originals")
    with engine.connect() as connection:
        screenshot_count = connection.execute(
            text("SELECT count(*) FROM screenshots WHERE project_id=:project_id"),
            {"project_id": project["id"]},
        ).scalar_one()
        receipts = connection.execute(
            text(
                "SELECT client_upload_id, state, upload_protocol_version, screenshot_id, "
                "lease_expires_at, last_error_code FROM upload_receipts "
                "WHERE project_id=:project_id ORDER BY client_upload_id"
            ),
            {"project_id": project["id"]},
        ).mappings().all()
    if screenshot_count != 3:
        raise RuntimeError(f"expected three screenshot rows, found {screenshot_count}")
    expected_receipts = {
        agent_item.client_upload_id: agent_evidence["detail"]["id"],
        automation_item.client_upload_id: automation_evidence["detail"]["id"],
    }
    if len(receipts) != 2:
        raise RuntimeError(f"expected two completed receipts, found {len(receipts)}")
    for receipt in receipts:
        client_id = str(receipt["client_upload_id"])
        if (
            client_id not in expected_receipts
            or receipt["state"] != "COMPLETED"
            or receipt["upload_protocol_version"] != 1
            or str(receipt["screenshot_id"]) != expected_receipts[client_id]
            or receipt["lease_expires_at"] is not None
            or receipt["last_error_code"] is not None
        ):
            raise RuntimeError("queued upload receipt is not durably completed")
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "api_origin": origin,
        "harness_source_sha256": sha256(HARNESS_PATH.read_bytes()).hexdigest(),
        "contract_test_sha256": sha256(CONTRACT_TEST_PATH.read_bytes()).hexdigest(),
        "source_snapshot": {
            path: sha256((ROOT / path).read_bytes()).hexdigest() for path in SNAPSHOT_FILES
        },
        "backend_source_manifest": _backend_source_manifest(),
        "uploader_source_manifest": _uploader_source_manifest(),
        "backend_reference_image": os.environ.get("QA_VERIFY_BACKEND_REFERENCE_IMAGE", "unrecorded"),
        "backend_runtime": "host source snapshot recorded above",
        "postgres_image": os.environ.get("QA_VERIFY_POSTGRES_IMAGE", "unrecorded"),
        "project": project,
        "build": build,
        "locale": locale,
        "category": category,
        "situation": situation,
        "uploader_cli_returncode": uploader.returncode,
        "list_total_after_queued_uploads": listing["total"],
        "list_total_after_manual_upload": final_listing["total"],
        "agent": agent_evidence,
        "automation": automation_evidence,
        "manual": {
            "status": manual_response.status_code,
            "location": manual_response.headers.get("location"),
            "detail": manual,
            "content_sha256": sha256(manual_content.content).hexdigest(),
            "content_exact": manual_content.content == manual_bytes,
        },
        "storage_file_count": len(stored),
        "storage_hashes": stored_hashes,
        "database": {
            "screenshot_count": screenshot_count,
            "receipt_count": len(receipts),
            "receipts": [
                {
                    "client_upload_id": str(receipt["client_upload_id"]),
                    "state": receipt["state"],
                    "upload_protocol_version": receipt["upload_protocol_version"],
                    "screenshot_id": str(receipt["screenshot_id"]),
                    "lease_expires_at": receipt["lease_expires_at"],
                    "last_error_code": receipt["last_error_code"],
                }
                for receipt in receipts
            ],
        },
        "cleanup": {"web": "pending", "api": "pending", "database": "pending", "postgres_container": "pending"},
    }


def _run_ocr_job(client: httpx.Client, run_path: str, runner) -> tuple[dict, list[dict]]:
    observations: list[dict] = []
    outcome: list[object] = []

    def execute():
        try:
            outcome.append(runner.run_once())
        except BaseException as exc:  # Preserve unexpected runner failure in evidence.
            outcome.append(exc)

    thread = threading.Thread(target=execute, name="frontend-ocr-live-runner", daemon=True)
    thread.start()
    deadline = time.monotonic() + 320
    last = None
    while time.monotonic() < deadline:
        response = client.get(run_path)
        response.raise_for_status()
        run = response.json()
        marker = (run["status"], run["stage"], run["attempt_count"])
        if marker != last:
            observations.append({
                "status": run["status"], "stage": run["stage"],
                "attempt_count": run["attempt_count"],
                "verification_status": run["verification_status"],
                "retry_after": response.headers.get("Retry-After"),
                "error": run["error"],
            })
            last = marker
        if run["status"] in {"SUCCEEDED", "FAILED"}:
            thread.join(timeout=10)
            if thread.is_alive():
                raise RuntimeError("OCR runner thread remained alive after terminal API state")
            if outcome and isinstance(outcome[0], BaseException):
                raise RuntimeError("OCR runner raised unexpectedly") from outcome[0]
            return run, observations
        time.sleep(0.1)
    raise RuntimeError(f"timed out waiting for OCR run {run_path}")


def _prepare_ocr_verification(origin: str, storage_root: Path, factory) -> dict:
    from backend.app.workers.ocr import OCRRunner

    source = OCR_FIXTURE.read_bytes()
    source_hash = sha256(source).hexdigest()
    runner = OCRRunner(session_factory=factory, storage=LocalStorage(storage_root))
    with httpx.Client(base_url=origin, timeout=30) as client:
        def created(path: str, body: dict) -> dict:
            response = client.post(path, json=body)
            if response.status_code != 201:
                raise RuntimeError(f"POST {path} returned {response.status_code}: {response.text}")
            return response.json()

        project = created("/api/v1/projects", {"slug": "ocr-live-" + uuid4().hex, "name": "OCR live synthetic"})
        prefix = f"/api/v1/projects/{project['id']}"
        build = created(prefix + "/builds", {"label": "ocr-live-2026.09"})
        locale = created(prefix + "/locales", {"code": "ko-KR", "name": "한국어"})
        category = created(prefix + "/categories", {"slug": "ocr-live", "name": "OCR Live"})
        situation = created(prefix + "/situations", {"category_id": category["id"], "slug": "scored", "name": "Scored"})
        no_expectations = created(prefix + "/situations", {"category_id": category["id"], "slug": "no-expectations", "name": "No expectations"})
        keys = {name: created(prefix + "/string-keys", {"string_id": name}) for name in ("recognized", "empty", "missing")}
        recognized = created(prefix + "/strings", {"build_id": build["id"], "locale_id": locale["id"], "string_id": "recognized", "text": "안녕하세요 설정 123"})
        created(prefix + "/strings", {"build_id": build["id"], "locale_id": locale["id"], "string_id": "empty", "text": ""})
        mapping = client.put(
            prefix + f"/situations/{situation['id']}/expected-string-keys",
            params={"build_id": build["id"]}, json={"string_ids": ["recognized", "empty", "missing"]},
        )
        mapping.raise_for_status()

        def upload(target_situation: str, filename: str) -> dict:
            metadata = {
                "build_id": build["id"], "locale_id": locale["id"],
                "category_id": category["id"], "situation_id": target_situation,
                "source": "manual", "metadata_version": 1,
                "metadata": {"fixture": "qualified-ko", "empty": "", "unicode": "한글 😀"},
            }
            response = client.post(
                prefix + "/screenshots", files={"file": (filename, source, "image/png")},
                data={"metadata": json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))},
            )
            if response.status_code != 201:
                raise RuntimeError(f"OCR fixture upload returned {response.status_code}: {response.text}")
            return response.json()

        screenshot = upload(situation["id"], "qualified-ko.png")
        no_expected_screenshot = upload(no_expectations["id"], "qualified-ko-no-expectations.png")
        profiles_response = client.get(prefix + "/ocr-profiles")
        profiles_response.raise_for_status()
        profiles = profiles_response.json()["items"]
        available = [item for item in profiles if item["availability"] == "AVAILABLE"]
        profile = next(item for item in available if "korean-medium-windows" in item["profile_id"])
        if profile["profile_digest"] != "00300d2aebd8097cba3879f8f35cae888c3e7a6b0abd3f426b654e5d7201c679":
            raise RuntimeError("qualified Windows Korean profile digest drift")

        runs_path = prefix + f"/screenshots/{screenshot['id']}/verification-runs"

        def request_run(path: str, client_run_id: str) -> tuple[dict, dict]:
            body = {"protocol_version": 1, "client_run_id": client_run_id, "profile_id": profile["profile_id"]}
            response = client.post(path, json=body)
            if response.status_code not in {200, 202}:
                raise RuntimeError(f"run request returned {response.status_code}: {response.text}")
            return response.json(), {
                "status": response.status_code, "location": response.headers.get("Location"),
                "retry_after": response.headers.get("Retry-After"),
                "idempotency_replayed": response.headers.get("Idempotency-Replayed"),
                "request": body,
            }

        first_client_id = str(uuid4())
        first, first_create = request_run(runs_path, first_client_id)
        replay, replay_create = request_run(runs_path, first_client_id)
        if first_create["status"] != 202 or replay_create["status"] != 200 or replay["id"] != first["id"]:
            raise RuntimeError("same-client idempotency replay contract failed")
        before = client.get(runs_path).json()
        if before["total"] != 1:
            raise RuntimeError("same-client replay created a duplicate run")
        first_path = runs_path + "/" + first["id"]
        first_final, first_observations = _run_ocr_job(client, first_path, runner)
        first_expected_response = client.get(first_path + "/expected", params={"limit": 50, "offset": 0})
        first_expected_response.raise_for_status()
        first_expected_bytes = first_expected_response.content
        first_expected = first_expected_response.json()
        first_ocr = client.get(first_path + "/ocr").json()
        first_regions = client.get(first_path + "/ocr/regions", params={"limit": 50, "offset": 0}).json()
        first_verification = client.get(first_path + "/verification").json()
        first_items = client.get(first_path + "/verification/items", params={"limit": 50, "offset": 0}).json()
        if first_final["status"] != "SUCCEEDED" or first_final["verification_status"] != "UNVERIFIED":
            diagnostic = {
                "run": first_final,
                "observations": first_observations,
                "expected": first_expected,
                "ocr": first_ocr,
                "regions": first_regions,
                "verification": first_verification,
                "items": first_items,
            }
            diagnostic_path = OCR_EVIDENCE.with_name(OCR_EVIDENCE.stem + "-diagnostic.json")
            diagnostic_path.write_text(
                json.dumps(diagnostic, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            raise RuntimeError(
                "partial-unverified qualified OCR run had the wrong aggregate; "
                f"diagnostic={diagnostic_path.relative_to(ROOT)} "
                f"summary={json.dumps(diagnostic, ensure_ascii=False, separators=(',', ':'))}"
            )
        reasons = {item["string_id"]: (item["verification_status"], item["reason"], item["match_score"]) for item in first_items["items"]}
        if reasons["recognized"][0] != "PASS" or reasons["empty"][:2] != ("UNVERIFIED", "EMPTY_EXPECTED") or reasons["missing"][:2] != ("UNVERIFIED", "MISSING_TRANSLATION"):
            raise RuntimeError(f"expected PASS/empty/missing distinctions were lost: {reasons}")
        if (
            first_verification["evaluation_reason"] != "PARTIAL_UNVERIFIED"
            or not first_verification["incomplete"]
            or first_verification["evaluated_count"] != 1
            or first_verification["pass_count"] != 1
            or first_verification["unverified_count"] != 2
        ):
            raise RuntimeError("nonempty aggregate did not preserve partial-unverified semantics")

        mutation = client.patch(prefix + f"/strings/{recognized['id']}", json={"text": "변경된 기대 문자열"})
        mutation.raise_for_status()
        second, second_create = request_run(runs_path, str(uuid4()))
        second_path = runs_path + "/" + second["id"]
        second_final, second_observations = _run_ocr_job(client, second_path, runner)
        second_expected_response = client.get(second_path + "/expected", params={"limit": 50, "offset": 0})
        second_expected_response.raise_for_status()
        if first_expected_bytes != client.get(first_path + "/expected", params={"limit": 50, "offset": 0}).content:
            raise RuntimeError("old expected snapshot changed after catalog mutation")
        if first_expected_bytes == second_expected_response.content:
            raise RuntimeError("new rerun did not capture changed expected catalog")
        if second_final["status"] != "SUCCEEDED" or second_final["verification_status"] != "FAIL":
            raise RuntimeError("changed expected rerun did not produce processing success with quality FAIL")

        failed, failed_create = request_run(runs_path, str(uuid4()))
        object_path = storage_root / "objects" / project["id"] / f"{screenshot['id']}.png"
        original = object_path.read_bytes()
        object_path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
        try:
            failed_path = runs_path + "/" + failed["id"]
            failed_final, failed_observations = _run_ocr_job(client, failed_path, runner)
        finally:
            object_path.write_bytes(original)
        if failed_final["status"] != "FAILED" or failed_final["verification_status"] is not None or failed_final["error"]["code"] != "INPUT_HASH_MISMATCH":
            raise RuntimeError("persisted processing failure was conflated with quality")

        no_expected_runs = prefix + f"/screenshots/{no_expected_screenshot['id']}/verification-runs"
        no_expected, no_expected_create = request_run(no_expected_runs, str(uuid4()))
        no_expected_path = no_expected_runs + "/" + no_expected["id"]
        no_expected_final, no_expected_observations = _run_ocr_job(client, no_expected_path, runner)
        no_expected_verification = client.get(no_expected_path + "/verification").json()
        if no_expected_final["verification_status"] != "UNVERIFIED" or no_expected_verification["evaluation_reason"] != "NO_EXPECTATIONS":
            raise RuntimeError("no-expectations run semantics failed")

        history = client.get(runs_path, params={"selection": "all", "limit": 50, "offset": 0}).json()
        latest_completed = client.get(runs_path, params={"selection": "succeeded", "limit": 1, "offset": 0}).json()
        if history["items"][0]["id"] != failed["id"] or latest_completed["items"][0]["id"] != second["id"]:
            raise RuntimeError("latest requested and latest completed selection diverged incorrectly")
        content = client.get(prefix + f"/screenshots/{screenshot['id']}/content")
        content.raise_for_status()
        detail = client.get(prefix + f"/screenshots/{screenshot['id']}").json()
        if content.content != source or detail["file_hash"] != source_hash or detail["metadata"]["empty"] != "":
            raise RuntimeError("Phase2 source bytes/hash/metadata compatibility failed")

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": "actual-qualified-ocr-web",
        "api_origin": origin,
        "harness_source_sha256_at_start": sha256(HARNESS_PATH.read_bytes()).hexdigest(),
        "contract_test_sha256": sha256(CONTRACT_TEST_PATH.read_bytes()).hexdigest(),
        "backend_manifest_sha256": sha256(OCR_BACKEND_MANIFEST.read_bytes()).hexdigest(),
        "worker_manifest_sha256": sha256(OCR_WORKER_MANIFEST.read_bytes()).hexdigest(),
        "fixture": {"path": str(OCR_FIXTURE.relative_to(ROOT)), "sha256": source_hash, "size": len(source)},
        "runtime": {
            "python": sys.version, "platform": sys.platform,
            "model_root": os.environ.get("QA_OCR_MODEL_ROOT"),
            "paddle_cache": os.environ.get("PADDLE_PDX_CACHE_HOME"),
            "profile": profile, "available_profiles": available,
        },
        "catalog": {"project": project, "build": build, "locale": locale, "category": category, "situation": situation, "no_expectations_situation": no_expectations},
        "screenshot": screenshot,
        "first_run": {"create": first_create, "replay": replay_create, "run": first_final, "observations": first_observations, "expected": first_expected, "ocr": first_ocr, "regions": first_regions, "verification": first_verification, "items": first_items},
        "rerun_after_catalog_mutation": {"create": second_create, "run": second_final, "observations": second_observations, "expected": second_expected_response.json(), "old_snapshot_byte_exact": True},
        "persisted_processing_failure": {"create": failed_create, "run": failed_final, "observations": failed_observations, "source_restored": sha256(object_path.read_bytes()).hexdigest() == source_hash},
        "no_expectations_run": {"create": no_expected_create, "run": no_expected_final, "observations": no_expected_observations, "verification": no_expected_verification},
        "history": history, "latest_completed": latest_completed,
        "source_round_trip": {"content_sha256": sha256(content.content).hexdigest(), "detail_file_hash": detail["file_hash"], "bytes_exact": content.content == source, "metadata": detail["metadata"]},
        "product_acceptance": "NOT_RUN pending PM and independent Reviewer08 decision",
        "cleanup": {"web": "pending", "api": "pending", "database": "pending", "postgres_container": "pending"},
    }


def _run_web(origin: str, evidence: dict, evidence_path: Path = EVIDENCE) -> subprocess.Popen:
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    node = shutil.which("node.exe" if os.name == "nt" else "node")
    if not npm or not node:
        raise RuntimeError("npm and node must be available on PATH")
    probe = socket.socket()
    try:
        probe.bind(("127.0.0.1", 3001))
    except OSError as exc:
        raise RuntimeError("loopback port 3001 is required by the Backend CORS contract and is already in use") from exc
    finally:
        probe.close()
    web_root = Path(os.environ.get("QA_VERIFY_FRONTEND_ROOT", ROOT / "frontend")).resolve()
    prebuilt = os.environ.get("QA_VERIFY_FRONTEND_PREBUILT") == "1"
    environment = dict(os.environ, NEXT_PUBLIC_API_BASE_URL=origin)
    if prebuilt:
        if not (web_root / ".next" / "BUILD_ID").is_file():
            raise RuntimeError(f"prebuilt production Web is missing BUILD_ID: {web_root}")
        build_returncode = 0
    else:
        build = subprocess.run([npm, "run", "build"], cwd=web_root, env=environment, check=False)
        build_returncode = build.returncode
        if build_returncode != 0:
            raise RuntimeError(f"production Web build failed with {build_returncode}")
    logs = evidence_path.with_suffix(".web.log")
    handle = logs.open("w", encoding="utf-8")
    process = subprocess.Popen(
        [node, "node_modules/next/dist/bin/next", "start", "--hostname", "127.0.0.1", "--port", "3001"],
        cwd=web_root, env=environment, stdout=handle, stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    process._verification_log_handle = handle  # type: ignore[attr-defined]
    try:
        _wait_http("http://127.0.0.1:3001", process)
    except BaseException:
        _stop_process(process)
        handle.close()
        raise
    if "agent" in evidence:
        project = evidence["project"]["id"]
        screenshot_id = evidence["agent"]["detail"]["id"]
    else:
        project = evidence["catalog"]["project"]["id"]
        screenshot_id = evidence["screenshot"]["id"]
    evidence["web"] = {
        "origin": "http://127.0.0.1:3001",
        "list_url": f"http://127.0.0.1:3001/#/screenshots?project={project}",
        "detail_url": f"http://127.0.0.1:3001/#/detail?project={project}&id={screenshot_id}",
        "production_build_returncode": build_returncode,
        "production_build_root": str(web_root),
        "prebuilt": prebuilt,
        "log": str(logs.relative_to(ROOT)),
    }
    if "agent" in evidence:
        evidence["web"]["detail_urls"] = {
            source: f"http://127.0.0.1:3001/#/detail?project={project}&id={evidence[source]['detail']['id']}"
            for source in ("agent", "automation", "manual")
        }
    elif "first_run" in evidence:
        evidence["web"].update({
            "detail_url": f"http://127.0.0.1:3001/#/detail?project={project}&id={screenshot_id}&run={evidence['first_run']['run']['id']}",
            "rerun_url": f"http://127.0.0.1:3001/#/detail?project={project}&id={screenshot_id}&run={evidence['rerun_after_catalog_mutation']['run']['id']}",
            "failed_run_url": f"http://127.0.0.1:3001/#/detail?project={project}&id={screenshot_id}&run={evidence['persisted_processing_failure']['run']['id']}",
        })
    return process


def main(test_url=None):
    serve = "--serve" in sys.argv
    verify_upload_web = "--verify-upload-web" in sys.argv
    verify_ocr_web = "--verify-ocr-web" in sys.argv
    if verify_upload_web and verify_ocr_web:
        raise RuntimeError("choose one Web verification mode")
    evidence_path = OCR_EVIDENCE if verify_ocr_web else EVIDENCE
    stop_file = evidence_path.with_suffix(".stop")
    name = "qa_frontend_test_" + uuid4().hex
    url = test_url or get_settings().database_url
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5})
    with admin.connect() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE "{name}" ENCODING \'UTF8\' TEMPLATE template0')
    engine = create_engine(url.set(database=name), isolation_level="REPEATABLE READ", connect_args={"client_encoding": "utf8", "connect_timeout": 5})
    server = None
    worker = None
    web = None
    evidence = None
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
            configured_port = os.environ.get("QA_VERIFY_API_PORT")
            api_port = int(configured_port) if configured_port else (8001 if serve else 0)
            listener.bind(("127.0.0.1", api_port))
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
                if verify_upload_web or verify_ocr_web:
                    evidence_path.parent.mkdir(parents=True, exist_ok=True)
                    stop_file.unlink(missing_ok=True)
                    if verify_ocr_web:
                        evidence = _prepare_ocr_verification(
                            f"http://127.0.0.1:{port}", storage.root, factory
                        )
                    else:
                        evidence = _prepare_upload_verification(
                            f"http://127.0.0.1:{port}", Path(directory) / "captures", storage.root, engine
                        )
                    web = _run_web(f"http://127.0.0.1:{port}", evidence, evidence_path)
                    evidence["harness_source_sha256_before_browser"] = sha256(HARNESS_PATH.read_bytes()).hexdigest()
                    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    print("VERIFICATION_READY " + json.dumps(evidence["web"], ensure_ascii=False), flush=True)
                    while web.poll() is None and worker.is_alive() and not stop_file.exists():
                        time.sleep(0.25)
                    if stop_file.exists():
                        return 0
                    if web.poll() is not None:
                        raise RuntimeError(f"production Web exited with {web.returncode}")
                    return 0
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
                web_status = _stop_process(web)
                if web is not None:
                    web._verification_log_handle.close()  # type: ignore[attr-defined]
                server.should_exit = True
                worker.join(timeout=10)
                if evidence is not None:
                    evidence["cleanup"].update(web=web_status, api="stopped")
                    evidence["harness_source_sha256_after"] = sha256(HARNESS_PATH.read_bytes()).hexdigest()
                    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
        if evidence is not None:
            evidence["cleanup"]["database"] = "dropped"
            evidence["harness_source_sha256_after"] = sha256(HARNESS_PATH.read_bytes()).hexdigest()
            evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
            os.environ["QA_VERIFY_POSTGRES_IMAGE"] = subprocess.check_output(
                ["docker", "image", "inspect", "postgres:17-alpine", "--format", "{{.Id}}"], text=True
            ).strip()
            reference = subprocess.run(
                ["docker", "image", "inspect", "qa-backend-upload-rework:local", "--format", "{{.Id}}"],
                capture_output=True, text=True, check=False,
            )
            if reference.returncode == 0:
                os.environ["QA_VERIFY_BACKEND_REFERENCE_IMAGE"] = reference.stdout.strip()
            port = int(subprocess.check_output(["docker", "port", container, "5432/tcp"], text=True).strip().rsplit(":", 1)[1])
            test_url = URL.create("postgresql+psycopg", username="postgres", password=password, host="127.0.0.1", port=port, database="postgres")
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
                logs = subprocess.run(["docker", "logs", container], capture_output=True, text=True, check=False)
                raise RuntimeError(f"isolated PostgreSQL did not become reachable: {logs.stdout}{logs.stderr}")
        sys.exit(main(test_url))
    except KeyboardInterrupt:
        pass
    finally:
        if container:
            subprocess.run(["docker", "rm", "-f", container], stdout=subprocess.DEVNULL, check=False)
            evidence_path = OCR_EVIDENCE if "--verify-ocr-web" in sys.argv else EVIDENCE
            if evidence_path.exists() and ("--verify-upload-web" in sys.argv or "--verify-ocr-web" in sys.argv):
                evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
                evidence["cleanup"]["postgres_container"] = "removed"
                evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (OCR_EVIDENCE if "--verify-ocr-web" in sys.argv else EVIDENCE).with_suffix(".stop").unlink(missing_ok=True)
