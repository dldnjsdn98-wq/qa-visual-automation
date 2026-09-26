"""Marker-last producer for immutable capture intents."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

from .durable_fs import ensure_directory, publish_file_no_replace, sync_directory, write_temp
from .image import inspect_image_bytes
from .jsonio import dumps_compact
from .manifest import MAX_MANIFEST_BYTES, ReadyItem, canonical_uuid, load_ready_item, sanitize_filename, validate_request
from .marker import ready_bytes
from .origin import BindingGuard


Barrier = Callable[[str], None]


def _noop_barrier(name: str) -> None:
    return None


class Producer:
    def __init__(self, spool_root: str | Path, binding_guard: BindingGuard):
        self.spool_root = Path(spool_root)
        self.binding_guard = binding_guard
        if self.spool_root != binding_guard.spool_root:
            raise ValueError("producer and binding guard must use the same spool root")

    def publish(
        self,
        image_bytes: bytes,
        *,
        project_id: str,
        original_filename: str,
        request: Mapping[str, Any],
        client_upload_id: str | None = None,
        barrier: Barrier | None = None,
    ) -> ReadyItem:
        """Publish one immutable intent and return its fully revalidated item."""
        self.binding_guard.check()
        client_id = canonical_uuid(client_upload_id or str(uuid4()), version4=True)
        project = canonical_uuid(project_id)
        filename = sanitize_filename(original_filename)
        facts = inspect_image_bytes(image_bytes)
        image_name = f"original.{facts.extension}"
        request_value = dict(request)
        for key in ("build_id", "locale_id", "category_id", "situation_id"):
            request_value[key] = canonical_uuid(request_value.get(key))
        request_value.setdefault("metadata_version", 1)
        request_value.setdefault("metadata", {})
        validate_request(request_value, width=facts.width, height=facts.height)
        manifest = {
            "manifest_version": 1,
            "upload_protocol_version": 1,
            "client_upload_id": client_id,
            "project_id": project,
            "image_file": image_name,
            "original_filename": filename,
            "file_hash": facts.file_hash,
            "size_bytes": facts.size_bytes,
            "media_type": facts.media_type,
            "width": facts.width,
            "height": facts.height,
            "request": request_value,
        }
        manifest_bytes = dumps_compact(manifest)
        if len(manifest_bytes) > MAX_MANIFEST_BYTES:
            raise ValueError("manifest exceeds 64 KiB")
        marker = ready_bytes(sha256(manifest_bytes).hexdigest())
        pending = self.spool_root / "pending"
        ensure_directory(pending)
        item_dir = pending / client_id
        callback = barrier or _noop_barrier

        self.binding_guard.check()
        item_dir.mkdir(exist_ok=False)
        sync_directory(pending)

        image_temp = item_dir / "original.tmp"
        image_final = item_dir / image_name
        write_temp(
            image_temp,
            image_bytes,
            guard=self.binding_guard.check,
            barrier=callback,
            barrier_name="producer.original.temp_fsynced",
        )
        publish_file_no_replace(
            image_temp,
            image_final,
            guard=self.binding_guard.check,
            barrier=callback,
            barrier_name="producer.original.renamed",
        )
        callback("producer.original.dir_synced")

        manifest_temp = item_dir / "manifest.json.tmp"
        manifest_final = item_dir / "manifest.json"
        write_temp(
            manifest_temp,
            manifest_bytes,
            guard=self.binding_guard.check,
            barrier=callback,
            barrier_name="producer.manifest.temp_fsynced",
        )
        publish_file_no_replace(
            manifest_temp,
            manifest_final,
            guard=self.binding_guard.check,
            barrier=callback,
            barrier_name="producer.manifest.renamed",
        )
        callback("producer.manifest.dir_synced")

        ready_temp = item_dir / "ready.json.tmp"
        ready_final = item_dir / "ready.json"
        write_temp(
            ready_temp,
            marker,
            guard=self.binding_guard.check,
            barrier=callback,
            barrier_name="producer.ready.temp_fsynced",
        )
        publish_file_no_replace(
            ready_temp,
            ready_final,
            guard=self.binding_guard.check,
            barrier=callback,
            barrier_name="producer.ready.renamed",
        )
        callback("producer.ready.dir_synced")
        return load_ready_item(item_dir)


def publish_capture(
    spool_root: str | Path,
    binding_guard: BindingGuard,
    image_bytes: bytes,
    **intent: Any,
) -> ReadyItem:
    return Producer(spool_root, binding_guard).publish(image_bytes, **intent)
