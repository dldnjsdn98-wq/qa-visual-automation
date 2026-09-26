from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


class FakeClock:
    def __init__(self, now: datetime | None = None):
        self.now = now or datetime(2026, 9, 25, tzinfo=timezone.utc)
        self.monotonic_value = 0.0

    def wall(self) -> datetime:
        return self.now

    def monotonic(self) -> float:
        return self.monotonic_value

    def sleep(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)
        self.monotonic_value += seconds


class FixedRng:
    def __init__(self, fraction: float):
        self.fraction = fraction

    def uniform(self, low: float, high: float) -> float:
        return low + (high - low) * self.fraction


class Guard:
    def __init__(self, origin: str = "http://127.0.0.1:8001", fail_at: int | None = None):
        self.backend_origin = origin
        self.fail_at = fail_at
        self.checks = 0

    def check(self):
        self.checks += 1
        if self.checks == self.fail_at:
            raise RuntimeError("binding changed")
        return type("Binding", (), {"backend_origin": self.backend_origin})()


@dataclass(frozen=True)
class Request:
    build_id: str
    locale_id: str
    category_id: str
    situation_id: str
    source: str = "agent"
    metadata_version: int = 1
    metadata: Any = None


@dataclass(frozen=True)
class Item:
    item_dir: Any
    image_path: Any
    client_upload_id: str
    project_id: str
    original_filename: str
    file_hash: str
    size_bytes: int
    media_type: str
    width: int
    height: int
    request: Request
    manifest_sha256: str = "b" * 64


PROJECT = "11111111-1111-4111-8111-111111111111"
CLIENT = "66666666-6666-4666-8666-666666666666"
BUILD = "22222222-2222-4222-8222-222222222222"
LOCALE = "33333333-3333-4333-8333-333333333333"
CATEGORY = "44444444-4444-4444-8444-444444444444"
SITUATION = "55555555-5555-4555-8555-555555555555"
SCREENSHOT = "99999999-9999-4999-8999-999999999999"
REQUEST_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def make_item(path, *, metadata=None) -> Item:
    return Item(
        item_dir=path.parent,
        image_path=path,
        client_upload_id=CLIENT,
        project_id=PROJECT,
        original_filename="synthetic.png",
        file_hash="a" * 64,
        size_bytes=9,
        media_type="image/png",
        width=1,
        height=1,
        request=Request(BUILD, LOCALE, CATEGORY, SITUATION, metadata={} if metadata is None else metadata),
    )


def success_body(metadata=None) -> dict[str, Any]:
    return {
        "id": SCREENSHOT,
        "project_id": PROJECT,
        "client_upload_id": CLIENT,
        "build_id": BUILD,
        "locale_id": LOCALE,
        "category_id": CATEGORY,
        "situation_id": SITUATION,
        "source": "agent",
        "original_filename": "synthetic.png",
        "uploaded_at": "2026-09-25T00:00:00Z",
        "file_hash": "a" * 64,
        "media_type": "image/png",
        "size_bytes": 9,
        "width": 1,
        "height": 1,
        "metadata_version": 1,
        "metadata": {} if metadata is None else metadata,
        "content_url": f"/api/v1/projects/{PROJECT}/screenshots/{SCREENSHOT}/content",
    }
