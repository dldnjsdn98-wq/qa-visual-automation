"""Deployment admission is strict, bounded, content-pinned, and fail closed."""
from __future__ import annotations

import hashlib
import json

from backend.app.workers import ocr_admission


PROFILE_ID = "qualified-profile-v1"
PROFILE_DIGEST = "a" * 64
TARGET = "windows-x86_64"
RELEASE = "release-2026.09.25"


def _payload(**changes):
    value = {
        "schema_version": 1,
        "worker_target": TARGET,
        "release_id": RELEASE,
        "profiles": [{"profile_id": PROFILE_ID, "profile_digest": PROFILE_DIGEST}],
    }
    value.update(changes)
    return value


def _write(tmp_path, raw, **env_changes):
    path = tmp_path / "ocr-admission.json"
    path.write_bytes(raw)
    env = {
        "QA_OCR_ADMISSION_PATH": str(path),
        "QA_OCR_ADMISSION_SHA256": hashlib.sha256(raw).hexdigest(),
        "QA_OCR_WORKER_TARGET": TARGET,
        "QA_OCR_RELEASE_ID": RELEASE,
    }
    env.update(env_changes)
    return env


def _json(value):
    return json.dumps(value, separators=(",", ":")).encode()


def test_missing_configuration_and_file_fail_closed(tmp_path):
    assert ocr_admission.load_admission_snapshot({}) is None
    env = {
        "QA_OCR_ADMISSION_PATH": str(tmp_path / "missing.json"),
        "QA_OCR_ADMISSION_SHA256": "0" * 64,
        "QA_OCR_WORKER_TARGET": TARGET,
        "QA_OCR_RELEASE_ID": RELEASE,
    }
    assert ocr_admission.load_admission_snapshot(env) is None
    env["QA_OCR_ADMISSION_PATH"] = "invalid\x00path"
    assert ocr_admission.load_admission_snapshot(env) is None


def test_exact_profile_and_digest_are_admitted(tmp_path, monkeypatch):
    env = _write(tmp_path, _json(_payload()))
    snapshot = ocr_admission.load_admission_snapshot(env)

    assert snapshot is not None
    assert snapshot.worker_target == TARGET
    assert snapshot.release_id == RELEASE
    assert snapshot.admitted(PROFILE_ID, PROFILE_DIGEST)
    assert not snapshot.admitted(PROFILE_ID, "b" * 64)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert ocr_admission.admitted(PROFILE_ID, PROFILE_DIGEST)


def test_content_pin_mismatch_fails_closed(tmp_path):
    env = _write(tmp_path, _json(_payload()))
    env["QA_OCR_ADMISSION_SHA256"] = "0" * 64

    assert ocr_admission.load_admission_snapshot(env) is None


def test_target_and_release_mismatch_fail_closed(tmp_path):
    raw = _json(_payload())

    assert ocr_admission.load_admission_snapshot(
        _write(tmp_path, raw, QA_OCR_WORKER_TARGET="linux-x86_64")
    ) is None
    assert ocr_admission.load_admission_snapshot(
        _write(tmp_path, raw, QA_OCR_RELEASE_ID="other-release")
    ) is None


def test_target_and_release_values_are_bounded_tokens(tmp_path):
    long_target = "t" * 129
    long_release = "r" * 129

    assert ocr_admission.load_admission_snapshot(_write(
        tmp_path,
        _json(_payload(worker_target=long_target)),
        QA_OCR_WORKER_TARGET=long_target,
    )) is None
    assert ocr_admission.load_admission_snapshot(_write(
        tmp_path,
        _json(_payload(release_id=long_release)),
        QA_OCR_RELEASE_ID=long_release,
    )) is None


def test_duplicate_json_keys_and_duplicate_profile_ids_fail_closed(tmp_path):
    duplicate_key = (
        b'{"schema_version":1,"schema_version":1,"worker_target":"windows-x86_64",'
        b'"release_id":"release-2026.09.25","profiles":[]}'
    )
    assert ocr_admission.load_admission_snapshot(_write(tmp_path, duplicate_key)) is None

    duplicate_id = _payload(profiles=[
        {"profile_id": PROFILE_ID, "profile_digest": PROFILE_DIGEST},
        {"profile_id": PROFILE_ID, "profile_digest": "b" * 64},
    ])
    assert ocr_admission.load_admission_snapshot(_write(tmp_path, _json(duplicate_id))) is None


def test_missing_unknown_fields_and_non_integer_version_fail_closed(tmp_path):
    missing = _payload()
    del missing["release_id"]
    unknown = _payload(unexpected=True)

    for payload in (missing, unknown, _payload(schema_version=True), _payload(schema_version="1")):
        assert ocr_admission.load_admission_snapshot(
            _write(tmp_path, _json(payload))
        ) is None


def test_invalid_profile_tokens_and_digests_fail_closed(tmp_path):
    cases = [
        [{"profile_id": "bad profile", "profile_digest": PROFILE_DIGEST}],
        [{"profile_id": "x" * 129, "profile_digest": PROFILE_DIGEST}],
        [{"profile_id": PROFILE_ID, "profile_digest": "A" * 64}],
        [{"profile_id": PROFILE_ID, "profile_digest": "a" * 63}],
        [{"profile_id": PROFILE_ID, "profile_digest": PROFILE_DIGEST, "extra": 1}],
    ]
    for profiles in cases:
        assert ocr_admission.load_admission_snapshot(
            _write(tmp_path, _json(_payload(profiles=profiles)))
        ) is None


def test_profile_count_and_actual_read_are_bounded(tmp_path):
    profiles = [
        {"profile_id": f"profile-{index}", "profile_digest": f"{index:064x}"}
        for index in range(257)
    ]
    assert ocr_admission.load_admission_snapshot(
        _write(tmp_path, _json(_payload(profiles=profiles)))
    ) is None

    oversized = b" " * (ocr_admission.MAX_ADMISSION_BYTES + 1)
    assert ocr_admission.load_admission_snapshot(_write(tmp_path, oversized)) is None


def test_malformed_non_utf8_and_non_finite_json_fail_closed(tmp_path):
    deeply_nested = (b"[" * 1100) + (b"]" * 1100)
    for raw in (b"{", b"\xff", b'{"schema_version":NaN}', deeply_nested):
        assert ocr_admission.load_admission_snapshot(_write(tmp_path, raw)) is None


def test_api_local_capability_environment_cannot_enable_admission(monkeypatch):
    monkeypatch.delenv("QA_OCR_ADMISSION_PATH", raising=False)
    monkeypatch.delenv("QA_OCR_ADMISSION_SHA256", raising=False)
    monkeypatch.delenv("QA_OCR_WORKER_TARGET", raising=False)
    monkeypatch.delenv("QA_OCR_RELEASE_ID", raising=False)
    monkeypatch.setenv("QA_OCR_RUNTIME_AVAILABLE", "true")
    monkeypatch.setenv("QA_OCR_CGROUP_AVAILABLE", "true")
    monkeypatch.setenv("QA_OCR_LOCAL_CAPABILITY", "AVAILABLE")

    assert not ocr_admission.admitted(PROFILE_ID, PROFILE_DIGEST)
