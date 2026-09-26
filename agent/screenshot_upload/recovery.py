"""Revalidation helpers used before sends and acknowledged recovery."""

from __future__ import annotations

from typing import Any

from .ack import AckMismatch, validate_ack
from .client import HttpResult
from .jsonio import dumps_compact
from .manifest import ReadyItem, load_ready_item
from .state import AckRecord


class LocalIntentChanged(RuntimeError):
    pass


def _intent_tuple(item: ReadyItem) -> tuple[Any, ...]:
    return (
        item.client_upload_id,
        item.project_id,
        item.original_filename,
        item.file_hash,
        item.size_bytes,
        item.media_type,
        item.width,
        item.height,
        dict(item.request),
        item.manifest_sha256,
    )


def validate_intent(item: ReadyItem) -> None:
    try:
        current = load_ready_item(item.item_dir)
    except Exception as exc:
        raise LocalIntentChanged("immutable upload intent no longer validates") from exc
    if _intent_tuple(current) != _intent_tuple(item):
        raise LocalIntentChanged("immutable upload intent changed")


def validate_persisted_ack(item: ReadyItem, ack: AckRecord | None) -> None:
    if ack is None:
        raise AckMismatch("acknowledged state has no acknowledgment")
    result = HttpResult(
        status_code=ack.status,
        headers={
            "Location": ack.location,
            "Idempotency-Replayed": "true" if ack.idempotency_replayed else "false",
            "X-Request-ID": ack.x_request_id,
        },
        body=dumps_compact(dict(ack.screenshot)),
        received_at=ack.received_at,
    )
    validate_ack(result, item)
