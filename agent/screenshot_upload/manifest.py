"""Immutable upload intent schema and ready-item validation."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
import types
import unicodedata
from typing import Any, Mapping
from uuid import UUID

from .durable_fs import ensure_directory, ensure_regular_file, resolved_within
from .image import inspect_image_file
from .jsonio import dumps_compact, loads_strict
from .marker import load_ready_marker


MAX_MANIFEST_BYTES = 65_536
MAX_METADATA_BYTES = 16_384
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MANIFEST_KEYS = {
    "manifest_version",
    "upload_protocol_version",
    "client_upload_id",
    "project_id",
    "image_file",
    "original_filename",
    "file_hash",
    "size_bytes",
    "media_type",
    "width",
    "height",
    "request",
}
_REQUEST_KEYS = {
    "build_id",
    "locale_id",
    "category_id",
    "situation_id",
    "source",
    "metadata_version",
    "metadata",
}


class ManifestError(ValueError):
    pass


def canonical_uuid(value: Any, *, version4: bool = False) -> str:
    if not isinstance(value, str):
        raise ManifestError("UUID must be a string")
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ManifestError("invalid UUID") from exc
    canonical = str(parsed)
    if canonical != value or (version4 and parsed.version != 4):
        raise ManifestError("UUID must be canonical" + (" version 4" if version4 else ""))
    return canonical


def sanitize_filename(value: str) -> str:
    if not isinstance(value, str):
        raise ManifestError("filename must be a string")
    if "\x00" in value or any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ManifestError("filename contains forbidden Unicode")
    basename = value.replace("\\", "/").rsplit("/", 1)[-1]
    basename = "".join(character for character in basename if unicodedata.category(character) != "Cc").strip()
    if not 1 <= len(basename) <= 255:
        raise ManifestError("sanitized filename must contain 1..255 scalars")
    return basename


def _validate_metadata(value: Any, *, depth: int = 1, counter: list[int] | None = None) -> None:
    if counter is None:
        counter = [0]
    if depth > 5:
        raise ManifestError("metadata nesting exceeds 5")
    if isinstance(value, dict):
        counter[0] += len(value)
        if counter[0] > 100:
            raise ManifestError("metadata contains more than 100 object keys")
        for child in value.values():
            if isinstance(child, (dict, list)):
                _validate_metadata(child, depth=depth + 1, counter=counter)
    elif isinstance(value, list):
        for child in value:
            if isinstance(child, (dict, list)):
                _validate_metadata(child, depth=depth + 1, counter=counter)


def validate_request(value: Any, *, width: int, height: int) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _REQUEST_KEYS:
        raise ManifestError("request schema is not closed")
    for key in ("build_id", "locale_id", "category_id", "situation_id"):
        canonical_uuid(value[key])
    if value["source"] not in {"agent", "automation"}:
        raise ManifestError("source is invalid")
    if type(value["metadata_version"]) is not int or value["metadata_version"] != 1:
        raise ManifestError("metadata_version must be integer 1")
    metadata = value["metadata"]
    if not isinstance(metadata, dict):
        raise ManifestError("metadata must be an object")
    _validate_metadata(metadata)
    if len(dumps_compact(metadata)) > MAX_METADATA_BYTES:
        raise ManifestError("metadata exceeds 16 KiB")
    for key, limit in (("device", 200), ("scenario", 128), ("checkpoint", 128), ("screen_state", 128)):
        if key in metadata and (type(metadata[key]) is not str or len(metadata[key]) > limit):
            raise ManifestError(f"metadata.{key} is invalid")
    if "run_id" in metadata:
        if type(metadata["run_id"]) is not str:
            raise ManifestError("metadata.run_id must be a UUID string")
        try:
            UUID(metadata["run_id"])
        except ValueError as exc:
            raise ManifestError("metadata.run_id must be a UUID string") from exc
    if "resolution" in metadata:
        resolution = metadata["resolution"]
        if (
            type(resolution) is not dict
            or set(resolution) != {"width", "height"}
            or any(type(member) is not int or not 1 <= member <= 16_384 for member in resolution.values())
            or resolution != {"width": width, "height": height}
        ):
            raise ManifestError("metadata.resolution must match decoded dimensions")
    return value


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return types.MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(child) for child in value)
    return value


@dataclass(frozen=True)
class ReadyItem:
    item_dir: Path
    client_upload_id: str
    project_id: str
    image_path: Path
    original_filename: str
    file_hash: str
    size_bytes: int
    media_type: str
    width: int
    height: int
    request: Mapping[str, Any]
    manifest_sha256: str


def _validate_inventory(item_dir: Path, image_name: str) -> None:
    allowed = {
        image_name,
        "manifest.json",
        "ready.json",
        "state.json",
        "initialized.json",
        "original.tmp",
        "manifest.json.tmp",
        "ready.json.tmp",
        "state.json.tmp",
        "initialized.json.tmp",
    }
    for entry in item_dir.iterdir():
        if entry.name not in allowed and not entry.name.startswith("diagnostic-"):
            raise ManifestError(f"unexpected item file: {entry.name}")
        ensure_regular_file(entry)


def load_ready_item(item_dir: str | Path) -> ReadyItem:
    directory = Path(item_dir)
    ensure_directory(directory)
    resolved_within(directory, directory.parent)
    directory_id = canonical_uuid(directory.name, version4=True)
    manifest_path = directory / "manifest.json"
    result = ensure_regular_file(manifest_path)
    assert result is not None
    if result.st_size > MAX_MANIFEST_BYTES:
        raise ManifestError("manifest exceeds 64 KiB")
    raw = manifest_path.read_bytes()
    if len(raw) != result.st_size:
        raise ManifestError("manifest changed while being read")
    value = loads_strict(raw, max_bytes=MAX_MANIFEST_BYTES)
    if not isinstance(value, dict) or set(value) != _MANIFEST_KEYS:
        raise ManifestError("manifest schema is not closed")
    for key in ("manifest_version", "upload_protocol_version"):
        if type(value[key]) is not int or value[key] != 1:
            raise ManifestError(f"{key} must be integer 1")
    client_id = canonical_uuid(value["client_upload_id"], version4=True)
    if client_id != directory_id:
        raise ManifestError("directory UUID does not match manifest")
    project_id = canonical_uuid(value["project_id"])
    image_name = value["image_file"]
    if image_name not in {"original.png", "original.jpg"}:
        raise ManifestError("image_file is invalid")
    original_filename = value["original_filename"]
    if not isinstance(original_filename, str) or sanitize_filename(original_filename) != original_filename:
        raise ManifestError("original_filename is not an already-sanitized basename")
    file_hash = value["file_hash"]
    if not isinstance(file_hash, str) or not _SHA256.fullmatch(file_hash):
        raise ManifestError("file_hash is invalid")
    media_type = value["media_type"]
    expected_pair = {"original.png": "image/png", "original.jpg": "image/jpeg"}
    if media_type != expected_pair[image_name]:
        raise ManifestError("image extension and media type disagree")
    for key in ("size_bytes", "width", "height"):
        if type(value[key]) is not int or value[key] <= 0:
            raise ManifestError(f"{key} must be a positive integer")
    request = validate_request(value["request"], width=value["width"], height=value["height"])

    digest = sha256(raw).hexdigest()
    marker = load_ready_marker(directory / "ready.json")
    if marker.manifest_sha256 != digest:
        raise ManifestError("ready marker does not match exact manifest bytes")
    _validate_inventory(directory, image_name)
    image_path = directory / image_name
    facts = inspect_image_file(image_path, media_type)
    if (
        facts.file_hash != file_hash
        or facts.size_bytes != value["size_bytes"]
        or facts.width != value["width"]
        or facts.height != value["height"]
    ):
        raise ManifestError("immutable image facts do not match manifest")
    return ReadyItem(
        item_dir=directory,
        client_upload_id=client_id,
        project_id=project_id,
        image_path=image_path,
        original_filename=original_filename,
        file_hash=file_hash,
        size_bytes=value["size_bytes"],
        media_type=media_type,
        width=value["width"],
        height=value["height"],
        request=_freeze(request),
        manifest_sha256=digest,
    )
