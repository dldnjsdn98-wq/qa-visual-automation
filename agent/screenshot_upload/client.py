"""Bounded two-part HTTP uploader transport."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
from typing import Any, Callable, Mapping, Protocol

from .canonical import canonical_bytes
from .config import RuntimeConfig, canonical_uuid


class BindingGuardProtocol(Protocol):
    def check(self) -> None: ...


class UploadTransportError(RuntimeError):
    """A request failed before a complete bounded response was received."""


class ResponseTooLarge(UploadTransportError):
    pass


class AttemptDeadlineExceeded(UploadTransportError):
    pass


@dataclass(frozen=True)
class HttpResult:
    status_code: int
    headers: Mapping[str, str]
    body: bytes
    received_at: datetime


def _field(value: object, name: str) -> Any:
    if isinstance(value, Mapping):
        return value[name]
    return getattr(value, name)


def metadata_payload(item: object) -> dict[str, Any]:
    request = _field(item, "request")
    return {
        "upload_protocol_version": 1,
        "client_upload_id": canonical_uuid(str(_field(item, "client_upload_id")), "client_upload_id"),
        "build_id": canonical_uuid(str(_field(request, "build_id")), "build_id"),
        "locale_id": canonical_uuid(str(_field(request, "locale_id")), "locale_id"),
        "category_id": canonical_uuid(str(_field(request, "category_id")), "category_id"),
        "situation_id": canonical_uuid(str(_field(request, "situation_id")), "situation_id"),
        "source": _field(request, "source"),
        "metadata_version": _field(request, "metadata_version"),
        "metadata": _field(request, "metadata"),
        "expected_file_hash": _field(item, "file_hash"),
    }


def upload_url(bound_origin: str, project_id: object) -> str:
    project = canonical_uuid(str(project_id), "project_id")
    return f"{bound_origin}/api/v1/projects/{project}/screenshots"


class UploadClient:
    """httpx adapter with fixed protocol limits and no redirect following."""

    def __init__(
        self,
        config: RuntimeConfig,
        guard: BindingGuardProtocol,
        *,
        transport: object | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        try:
            import httpx
        except ModuleNotFoundError as exc:
            raise RuntimeError("httpx >=0.28,<1 is required by the screenshot uploader") from exc
        self._httpx = httpx
        self._config = config
        self._guard = guard
        binding = guard.check()
        bound_origin = getattr(guard, "backend_origin", getattr(binding, "backend_origin", None))
        if bound_origin != config.backend_origin:
            raise RuntimeError("runtime origin does not match the immutable spool binding")
        self._bound_origin = bound_origin
        self._monotonic = monotonic
        self._wall_clock = wall_clock
        timeout = httpx.Timeout(
            connect=config.connect_timeout,
            read=config.read_timeout,
            write=config.write_timeout,
            pool=config.pool_timeout,
        )
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            transport=transport,
            trust_env=False,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "UploadClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def send(self, item: object) -> HttpResult:
        self._guard.check()
        path = Path(_field(item, "image_path"))
        metadata = canonical_bytes(metadata_payload(item))
        url = upload_url(self._bound_origin, _field(item, "project_id"))
        filename = _field(item, "original_filename")
        media_type = _field(item, "media_type")
        started = self._monotonic()
        try:
            with path.open("rb") as image:
                files = [
                    ("file", (filename, image, media_type)),
                    ("metadata", (None, metadata, "application/json")),
                ]
                with self._client.stream("POST", url, files=files) as response:
                    content_length = response.headers.get("Content-Length")
                    if content_length is not None:
                        try:
                            if int(content_length) > self._config.response_limit:
                                raise ResponseTooLarge("response exceeds 128 KiB")
                        except ValueError:
                            pass
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        if self._monotonic() - started > self._config.attempt_deadline:
                            raise AttemptDeadlineExceeded("upload attempt exceeded 120 seconds")
                        if len(body) + len(chunk) > self._config.response_limit:
                            raise ResponseTooLarge("response exceeds 128 KiB")
                        body.extend(chunk)
                    if self._monotonic() - started > self._config.attempt_deadline:
                        raise AttemptDeadlineExceeded("upload attempt exceeded 120 seconds")
                    return HttpResult(
                        status_code=response.status_code,
                        headers=dict(response.headers.items()),
                        body=bytes(body),
                        received_at=self._wall_clock().astimezone(timezone.utc),
                    )
        except (ResponseTooLarge, AttemptDeadlineExceeded):
            raise
        except self._httpx.HTTPError as exc:
            raise UploadTransportError("upload transport failed") from exc


def safe_error_code(result: HttpResult) -> str | None:
    """Extract only a bounded, syntactically safe API error code."""

    try:
        payload = json.loads(result.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if type(payload) is not dict:
        return None
    error = payload.get("error")
    if type(error) is dict:
        code = error.get("code")
    else:
        code = payload.get("code")
    if type(code) is str and re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", code):
        return code
    return None
