"""Integrated uploader runtime held under one OS spool lock."""

from __future__ import annotations

from dataclasses import dataclass

from .client import UploadClient
from .ack import AckMismatch
from .config import RuntimeConfig
from .lock import ProcessLock
from .origin import BindingGuard
from .recovery import LocalIntentChanged, validate_intent, validate_persisted_ack
from .requeue import requeue_failed
from .spool import Spool
from .state_store import StateStore, StateStoreError
from .worker import UploadWorker


@dataclass
class UploadRuntime:
    config: RuntimeConfig

    def _components(self):
        guard = BindingGuard(self.config.spool_root, self.config.backend_origin)
        guard.check()
        spool = Spool(self.config.spool_root, guard)
        store = StateStore(guard.check)
        return guard, spool, store

    def run(self) -> list[object]:
        with ProcessLock(self.config.spool_root):
            guard, spool, store = self._components()
            items = spool.discover()
            results: list[object] = []
            with UploadClient(self.config, guard) as client:
                worker = UploadWorker(
                    guard=guard,
                    state_store=store,
                    spool=spool,
                    client=client,
                    validate_intent=validate_intent,
                    validate_persisted_ack=validate_persisted_ack,
                )
                for item, location in items:
                    try:
                        results.append(worker.run_item(item, location=location))
                    except (AckMismatch, StateStoreError, LocalIntentChanged):
                        spool.quarantine_path(item.item_dir, location, "LOCAL_STATE_INVALID")
            return results

    def requeue(self, client_upload_id: str) -> object:
        with ProcessLock(self.config.spool_root):
            guard, spool, store = self._components()
            item = spool.find(client_upload_id, "failed")
            return requeue_failed(
                item,
                guard=guard,
                state_store=store,
                spool=spool,
                validate_intent=validate_intent,
            )


def build_runtime(config: RuntimeConfig) -> UploadRuntime:
    return UploadRuntime(config)
