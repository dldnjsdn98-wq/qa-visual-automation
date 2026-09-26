"""Fail-closed deployment admission for qualified OCR worker releases."""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


MAX_ADMISSION_BYTES = 64 * 1024
MAX_PROFILES = 256
MAX_TOKEN_LENGTH = 128

_PROFILE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_DEPLOYMENT_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@+-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TOP_LEVEL_FIELDS = frozenset({"schema_version", "worker_target", "release_id", "profiles"})
_PROFILE_FIELDS = frozenset({"profile_id", "profile_digest"})


class _DuplicateKey(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AdmissionSnapshot:
    """A validated assertion for one exact worker target and release."""

    worker_target: str
    release_id: str
    profiles: Mapping[str, str]

    def admitted(self, profile_id: str, profile_digest: str) -> bool:
        return (
            _valid_profile_id(profile_id)
            and _valid_sha256(profile_digest)
            and self.profiles.get(profile_id) == profile_digest
        )


def _valid_string(value: object, pattern: re.Pattern[str]) -> bool:
    return (
        type(value) is str
        and 1 <= len(value) <= MAX_TOKEN_LENGTH
        and pattern.fullmatch(value) is not None
    )


def _valid_profile_id(value: object) -> bool:
    return _valid_string(value, _PROFILE_ID)


def _valid_deployment_token(value: object) -> bool:
    return _valid_string(value, _DEPLOYMENT_TOKEN)


def _valid_sha256(value: object) -> bool:
    return type(value) is str and _SHA256.fullmatch(value) is not None


def _object_without_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(key)
        result[key] = value
    return result


def _reject_json_constant(value: str):
    raise ValueError(f"unsupported JSON constant: {value}")


def _snapshot_from_payload(payload: object, worker_target: str, release_id: str):
    if type(payload) is not dict or frozenset(payload) != _TOP_LEVEL_FIELDS:
        return None
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        return None
    if payload["worker_target"] != worker_target or payload["release_id"] != release_id:
        return None
    if not _valid_deployment_token(payload["worker_target"]):
        return None
    if not _valid_deployment_token(payload["release_id"]):
        return None
    entries = payload["profiles"]
    if type(entries) is not list or len(entries) > MAX_PROFILES:
        return None

    profiles = {}
    for entry in entries:
        if type(entry) is not dict or frozenset(entry) != _PROFILE_FIELDS:
            return None
        profile_id = entry["profile_id"]
        profile_digest = entry["profile_digest"]
        if not _valid_profile_id(profile_id) or not _valid_sha256(profile_digest):
            return None
        if profile_id in profiles:
            return None
        profiles[profile_id] = profile_digest

    return AdmissionSnapshot(
        worker_target=worker_target,
        release_id=release_id,
        profiles=MappingProxyType(profiles),
    )


def load_admission_snapshot(
    env: Mapping[str, str] | None = None,
) -> AdmissionSnapshot | None:
    """Load one content-pinned assertion, returning ``None`` for normal invalid input."""

    source = os.environ if env is None else env
    try:
        path = source.get("QA_OCR_ADMISSION_PATH")
        expected_sha256 = source.get("QA_OCR_ADMISSION_SHA256")
        worker_target = source.get("QA_OCR_WORKER_TARGET")
        release_id = source.get("QA_OCR_RELEASE_ID")
    except (AttributeError, KeyError, TypeError):
        return None
    if type(path) is not str or not path:
        return None
    if not _valid_sha256(expected_sha256):
        return None
    if not _valid_deployment_token(worker_target) or not _valid_deployment_token(release_id):
        return None

    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_ADMISSION_BYTES + 1)
    except (OSError, ValueError):
        return None
    if not raw or len(raw) > MAX_ADMISSION_BYTES:
        return None
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        return None

    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_json_constant,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        _DuplicateKey,
        RecursionError,
        TypeError,
        ValueError,
    ):
        return None
    return _snapshot_from_payload(payload, worker_target, release_id)


def admitted(profile_id: str, profile_digest: str) -> bool:
    """Return whether the current deployment assertion admits this exact profile."""

    snapshot = load_admission_snapshot()
    return snapshot is not None and snapshot.admitted(profile_id, profile_digest)
