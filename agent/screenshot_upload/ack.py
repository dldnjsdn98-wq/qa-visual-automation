"""Strict success acknowledgment validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from uuid import UUID

from .canonical import CanonicalizationError, canonical_equal
from .client import HttpResult
from .config import canonical_uuid
from .jsonio import StrictJSONError, loads_strict


class AckMismatch(ValueError):
    """A nominally successful response does not prove the intended upload."""


@dataclass(frozen=True)
class ValidatedAck:
    screenshot: dict[str, Any]
    status: int
    location: str
    idempotency_replayed: bool
    x_request_id: str
    received_at: datetime


def _field(value: object, name: str) -> Any:
    if isinstance(value, Mapping):
        return value[name]
    return getattr(value, name)


def _header(headers: Mapping[str, str], name: str) -> str:
    matches = [value for key, value in headers.items() if key.lower() == name.lower()]
    if len(matches) != 1 or not matches[0]:
        raise AckMismatch(f"missing or duplicate {name} header")
    return matches[0]


def _strict_json_object(raw: bytes) -> dict[str, Any]:
    try:
        value = loads_strict(raw, max_bytes=128 * 1024)
    except StrictJSONError as exc:
        raise AckMismatch("response body is not strict UTF-8 JSON") from exc
    if type(value) is not dict:
        raise AckMismatch("response body must be a JSON object")
    return value


def _uuid(value: Any, field: str, *, version: int | None = None) -> str:
    if type(value) is not str:
        raise AckMismatch(f"{field} must be a UUID string")
    try:
        parsed = UUID(value)
    except ValueError as exc:
        raise AckMismatch(f"{field} must be a UUID") from exc
    if version is not None and parsed.version != version:
        raise AckMismatch(f"{field} must be UUID version {version}")
    canonical = str(parsed)
    if value != canonical:
        raise AckMismatch(f"{field} must use canonical UUID text")
    return canonical


def _uploaded_at(value: Any) -> datetime:
    if type(value) is not str:
        raise AckMismatch("uploaded_at must be a string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AckMismatch("uploaded_at must be ISO 8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise AckMismatch("uploaded_at must identify UTC")
    return parsed.astimezone(timezone.utc)


def _expect_exact(body: Mapping[str, Any], field: str, expected: Any, expected_type: type) -> None:
    if field not in body or type(body[field]) is not expected_type or body[field] != expected:
        raise AckMismatch(f"{field} does not match the immutable manifest")


def validate_ack(result: HttpResult, item: object) -> ValidatedAck:
    replayed_text = _header(result.headers, "Idempotency-Replayed")
    if result.status_code == 201 and replayed_text == "false":
        replayed = False
    elif result.status_code == 200 and replayed_text == "true":
        replayed = True
    else:
        raise AckMismatch("status and Idempotency-Replayed are not an allowed success pair")

    location = _header(result.headers, "Location")
    request_id = _uuid(_header(result.headers, "X-Request-ID"), "X-Request-ID")
    body = _strict_json_object(result.body)
    request = _field(item, "request")

    expected_uuids = {
        "project_id": str(_field(item, "project_id")),
        "client_upload_id": str(_field(item, "client_upload_id")),
        "build_id": str(_field(request, "build_id")),
        "locale_id": str(_field(request, "locale_id")),
        "category_id": str(_field(request, "category_id")),
        "situation_id": str(_field(request, "situation_id")),
    }
    for field, expected in expected_uuids.items():
        try:
            expected_canonical = canonical_uuid(expected, field)
        except ValueError as exc:
            raise AckMismatch(f"invalid manifest {field}") from exc
        if field not in body or _uuid(body[field], field) != expected_canonical:
            raise AckMismatch(f"{field} does not match the immutable manifest")

    screenshot_id = _uuid(body.get("id"), "id")
    _uploaded_at(body.get("uploaded_at"))
    _expect_exact(body, "source", _field(request, "source"), str)
    _expect_exact(body, "original_filename", _field(item, "original_filename"), str)
    _expect_exact(body, "metadata_version", _field(request, "metadata_version"), int)
    _expect_exact(body, "file_hash", _field(item, "file_hash"), str)
    _expect_exact(body, "size_bytes", _field(item, "size_bytes"), int)
    _expect_exact(body, "media_type", _field(item, "media_type"), str)
    _expect_exact(body, "width", _field(item, "width"), int)
    _expect_exact(body, "height", _field(item, "height"), int)
    if "metadata" not in body or type(body["metadata"]) is not dict:
        raise AckMismatch("metadata must be an object")
    try:
        if not canonical_equal(body["metadata"], _field(request, "metadata")):
            raise AckMismatch("metadata does not match the immutable manifest")
    except CanonicalizationError as exc:
        raise AckMismatch("metadata is outside the canonical value domain") from exc

    project_id = expected_uuids["project_id"]
    detail = f"/api/v1/projects/{project_id}/screenshots/{screenshot_id}"
    if location != detail:
        raise AckMismatch("Location does not match the acknowledged screenshot")
    _expect_exact(body, "content_url", f"{detail}/content", str)
    return ValidatedAck(
        screenshot=body,
        status=result.status_code,
        location=location,
        idempotency_replayed=replayed,
        x_request_id=request_id,
        received_at=result.received_at.astimezone(timezone.utc),
    )


def to_state_ack(validated: ValidatedAck, factory: Callable[..., object] | None = None) -> object:
    """Construct work-unit A's AckRecord without importing it at module import time."""

    if factory is None:
        try:
            from .state import AckRecord as factory  # type: ignore[assignment]
        except ImportError as exc:
            raise RuntimeError("work-unit A state.AckRecord is unavailable") from exc
    return factory(
        screenshot=validated.screenshot,
        status=validated.status,
        location=validated.location,
        idempotency_replayed=validated.idempotency_replayed,
        x_request_id=validated.x_request_id,
        received_at=validated.received_at,
    )
