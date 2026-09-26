"""Opt-in real OCR runner integration against isolated PostgreSQL."""

from __future__ import annotations

import json
import hashlib
import os
import platform
import stat
import time
from pathlib import Path
from types import MappingProxyType
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from backend.app.models import OCRRegion, OCRResult, VerificationJob, VerificationResult, VerificationRun
from backend.app.workers.ocr import ATTEMPT_SECONDS, RSS_LIMIT_BYTES, OCRRunner


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(
    os.environ.get("QA_OCR_REAL_RUNTIME_TEST") != "1" or platform.system() != "Linux",
    reason="requires the qualified external OCR model root",
)
def test_real_runner_atomically_commits_ocr_and_verification_results(
    client, catalog, record_property, monkeypatch
):
    assert platform.system() == "Linux"
    _qualification_admission(monkeypatch, record_property, "linux")
    _real_runner_case(client, catalog, record_property, "linux", None)


@pytest.mark.skipif(
    os.environ.get("QA_OCR_REAL_RUNTIME_TEST") != "1" or platform.system() != "Windows",
    reason="Windows real OCR requires explicit opt-in, qualified read-only models and native containment",
)
def test_windows_real_runner_qualified_unified_profile(client, catalog, record_property, monkeypatch):
    # Paths are supplied by parent using existing Owner05 provenance; no search,
    # copy, model installation or package mutation is performed here.
    model_path = os.environ.get("QA_OCR_MODEL_ROOT")
    if not model_path:
        pytest.skip("NOT_RUN: approved Windows model root not supplied")
    try:
        if not stat.S_ISDIR(os.stat(model_path).st_mode):
            pytest.skip("NOT_RUN: approved Windows model root is not a directory")
    except OSError as exc:
        pytest.skip(f"NOT_RUN: approved Windows model root inaccessible ({type(exc).__name__})")
    _qualification_admission(monkeypatch, record_property, "windows")
    _real_runner_case(
        client, catalog, record_property, "windows",
        "39917d5bf35cd7b538ecd38db6f5c26604cda8370faae0069aa1acc1d2bde916",
    )


def _qualification_admission(monkeypatch, record_property, target_os):
    """Isolated evidence-generation bypass, NOT a production readiness assertion.

    Only this test process sees the pinned snapshot. Both API snapshot loading
    and runner admitted() consult the identical provider; no deployment config,
    profile, model or admission file is created or changed.
    """
    from backend.app.services import verification_runs
    from backend.app.workers import ocr_admission

    identities = {
        "windows": (
            "paddleocr-unified-medium-windows-amd64-cpython312-v1",
            "39917d5bf35cd7b538ecd38db6f5c26604cda8370faae0069aa1acc1d2bde916",
        ),
        "linux": (
            "paddleocr-unified-medium-linux-x86_64-debian13-glibc2.41-cpython312-v1",
            "89d587ee744e52a53593eae177366efe9b72079d6c0eacecad91c0ec916221ed",
        ),
    }
    profile_id, digest = identities[target_os]
    snapshot = ocr_admission.AdmissionSnapshot(
        worker_target="isolated-qualification", release_id="test-only",
        profiles=MappingProxyType({profile_id: digest}),
    )
    def provider():
        return snapshot
    monkeypatch.setattr(ocr_admission, "load_admission_snapshot", provider)
    monkeypatch.setattr(verification_runs, "load_admission_snapshot", provider)
    assert ocr_admission.admitted(profile_id, digest)
    record_property("admission_mode", "isolated qualification bypass; NOT production readiness")
    record_property("qualification_profile_id", profile_id)


def _real_runner_case(client, catalog, record_property, target_os, expected_digest):
    assert ATTEMPT_SECONDS == 300
    assert RSS_LIMIT_BYTES == 2 * 1024 * 1024 * 1024
    model_root = Path(os.environ["QA_OCR_MODEL_ROOT"])
    assert model_root.is_dir()

    source = (ROOT / "tests/ocr/fixtures/runtime/ja.png").read_bytes()
    upload = client.post(
        catalog["p"] + "/screenshots",
        files={
            "file": ("ja.png", source, "image/png"),
            "metadata": (
                None,
                json.dumps({
                    "build_id": catalog["build"]["id"],
                    "locale_id": catalog["locale"]["id"],
                    "category_id": catalog["category"]["id"],
                    "situation_id": catalog["situation"]["id"],
                    "source": "manual",
                }),
                "application/json",
            ),
        },
    )
    assert upload.status_code == 201, upload.text
    screenshot = upload.json()

    profiles = client.get(catalog["p"] + "/ocr-profiles")
    assert profiles.status_code == 200, profiles.text
    profile = next(
        item
        for item in profiles.json()["items"]
        if item["availability"] == "AVAILABLE"
        and f"unified-medium-{target_os}" in item["profile_id"]
    )
    if expected_digest is not None:
        assert profile["profile_digest"] == expected_digest
    runs_path = screenshot["content_url"].removesuffix("/content") + "/verification-runs"
    created = client.post(
        runs_path,
        json={
            "protocol_version": 1,
            "client_run_id": str(uuid4()),
            "profile_id": profile["profile_id"],
        },
    )
    assert created.status_code == 202, created.text
    run_id = UUID(created.json()["id"])

    runner = OCRRunner(session_factory=client.factory, storage=client.storage)
    started = time.monotonic()
    assert runner.run_once() is True
    elapsed = time.monotonic() - started
    record_property("isolated_database_name", client.factory.kw["bind"].url.database)
    record_property("profile_digest", profile["profile_digest"])
    record_property("observed_runner_elapsed_seconds", elapsed)
    if target_os == "windows" and getattr(runner, "containment_unavailable", False):
        pytest.skip("NOT_RUN: Windows continuous containment unavailable; OCR did not qualify")
    assert runner.quarantined is False
    assert runner.last_process is not None
    assert runner.child_stopped is True
    assert runner.last_process.poll() is not None
    assert runner.last_receiver is not None
    assert runner.last_receiver.is_alive() is False

    with client.factory() as session:
        run = session.get(VerificationRun, run_id)
        job = session.get(VerificationJob, run_id)
        ocr = session.scalar(select(OCRResult).where(OCRResult.run_id == run_id))
        verification = session.scalar(
            select(VerificationResult).where(VerificationResult.run_id == run_id)
        )
        regions = session.scalars(
            select(OCRRegion).where(OCRRegion.run_id == run_id).order_by(OCRRegion.region_index)
        ).all()

        assert run.status == job.state == "SUCCEEDED"
        assert run.stage == job.stage == "COMPLETE"
        assert run.ocr_result_id == ocr.id
        assert run.verification_result_id == verification.id
        assert verification.ocr_result_id == ocr.id
        assert ocr.profile_digest == profile["profile_digest"]
        assert ocr.runtime_manifest["profile_id"] == profile["profile_id"]
        assert len(ocr.runtime_manifest["native_packages"]) == 3
        assert ocr.region_count == len(regions) > 0
        assert verification.verification_status == "UNVERIFIED"
        assert verification.evaluation_reason == "NO_EXPECTATIONS"

    run_path = runs_path + "/" + str(run_id)
    assert client.get(run_path).json()["status"] == "SUCCEEDED"
    assert client.get(run_path + "/ocr").status_code == 200
    assert client.get(run_path + "/verification").status_code == 200

    database_name = client.factory.kw["bind"].url.database
    worker_path = ROOT / "backend/app/workers/ocr.py"
    source_path = ROOT / "backend/app/workers/ocr_source.py"
    record_property("isolated_database_name", database_name)
    record_property("profile_digest", profile["profile_digest"])
    record_property("attempt_child_pid", runner.last_process.pid)
    record_property("attempt_child_exitcode", runner.last_process.poll())
    record_property("attempt_child_alive_after_cleanup", not runner.child_stopped)
    record_property("containment_elapsed_seconds", runner.containment_elapsed)
    record_property("receiver_alive_after_cleanup", runner.last_receiver.is_alive())
    record_property("runner_quarantined", runner.quarantined)
    record_property(
        "supervisor_identity",
        "backend.app.workers.ocr.OCRRunner._execute/launch_contained",
    )
    record_property(
        "source_supervision_identity",
        "backend.app.workers.ocr_source.read_source",
    )
    record_property("ocr_worker_sha256", hashlib.sha256(worker_path.read_bytes()).hexdigest())
    record_property("ocr_source_sha256", hashlib.sha256(source_path.read_bytes()).hexdigest())
