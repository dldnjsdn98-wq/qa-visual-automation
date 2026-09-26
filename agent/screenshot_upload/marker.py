"""Ready and initialization marker schemas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from uuid import UUID

from .durable_fs import ensure_regular_file
from .jsonio import dumps_compact, loads_strict


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class MarkerError(ValueError):
    pass


@dataclass(frozen=True)
class ReadyMarker:
    manifest_version: int
    manifest_sha256: str


@dataclass(frozen=True)
class InitializedMarker:
    queue_state_version: int
    client_upload_id: str
    manifest_sha256: str


def ready_bytes(manifest_sha256: str) -> bytes:
    if not _SHA256.fullmatch(manifest_sha256):
        raise MarkerError("invalid manifest digest")
    return dumps_compact({"manifest_version": 1, "manifest_sha256": manifest_sha256})


def initialized_bytes(client_upload_id: str, manifest_sha256: str) -> bytes:
    if not _SHA256.fullmatch(manifest_sha256):
        raise MarkerError("invalid manifest digest")
    return dumps_compact(
        {
            "queue_state_version": 1,
            "client_upload_id": client_upload_id,
            "manifest_sha256": manifest_sha256,
        }
    )


def load_ready_marker(path: str | Path) -> ReadyMarker:
    marker_path = Path(path)
    result = ensure_regular_file(marker_path)
    assert result is not None
    if result.st_size > 1024:
        raise MarkerError("ready marker exceeds 1 KiB")
    raw = marker_path.read_bytes()
    value = loads_strict(raw, max_bytes=1024)
    if not isinstance(value, dict) or set(value) != {"manifest_version", "manifest_sha256"}:
        raise MarkerError("invalid ready marker schema")
    if type(value["manifest_version"]) is not int or value["manifest_version"] != 1:
        raise MarkerError("unsupported manifest version")
    digest = value["manifest_sha256"]
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        raise MarkerError("invalid manifest digest")
    if raw != ready_bytes(digest):
        raise MarkerError("ready marker bytes are not canonical")
    return ReadyMarker(1, digest)


def load_initialized_marker(path: str | Path) -> InitializedMarker:
    marker_path = Path(path)
    result = ensure_regular_file(marker_path)
    assert result is not None
    if result.st_size > 1024:
        raise MarkerError("initialized marker exceeds 1 KiB")
    raw = marker_path.read_bytes()
    value = loads_strict(raw, max_bytes=1024)
    expected = {"queue_state_version", "client_upload_id", "manifest_sha256"}
    if not isinstance(value, dict) or set(value) != expected:
        raise MarkerError("invalid initialized marker schema")
    if type(value["queue_state_version"]) is not int or value["queue_state_version"] != 1:
        raise MarkerError("unsupported queue state version")
    client_id = value["client_upload_id"]
    digest = value["manifest_sha256"]
    if not isinstance(client_id, str) or not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        raise MarkerError("invalid initialized marker identity")
    try:
        if str(UUID(client_id)) != client_id:
            raise MarkerError("initialized marker UUID is not canonical")
    except ValueError as exc:
        raise MarkerError("initialized marker UUID is invalid") from exc
    if raw != initialized_bytes(client_id, digest):
        raise MarkerError("initialized marker bytes are not canonical")
    return InitializedMarker(1, client_id, digest)
