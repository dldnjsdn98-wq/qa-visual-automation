"""Synthetic child process that discards one real Backend response then exits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent.screenshot_upload.client import UploadClient, UploadTransportError
from agent.screenshot_upload.config import RuntimeConfig
from agent.screenshot_upload.faults import ExitAtFault
from agent.screenshot_upload.lock import ProcessLock
from agent.screenshot_upload.origin import BindingGuard
from agent.screenshot_upload.recovery import validate_intent, validate_persisted_ack
from agent.screenshot_upload.spool import Spool
from agent.screenshot_upload.state_store import StateStore
from agent.screenshot_upload.worker import UploadWorker


class DiscardCompletedResponse:
    def __init__(self, client: UploadClient, observed_response: Path):
        self.client = client
        self.observed_response = observed_response

    def send(self, item):
        result = self.client.send(item)
        self.observed_response.write_text(
            json.dumps(
                {
                    "status": result.status_code,
                    "headers": dict(result.headers),
                    "body": json.loads(result.body.decode("utf-8")),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        raise UploadTransportError("synthetic response loss after Backend completion")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spool", required=True)
    parser.add_argument("--backend-origin", required=True)
    parser.add_argument("--observed-response", required=True, type=Path)
    args = parser.parse_args()
    config = RuntimeConfig.create(args.spool, args.backend_origin)
    with ProcessLock(config.spool_root):
        guard = BindingGuard(config.spool_root, config.backend_origin)
        spool = Spool(config.spool_root, guard)
        store = StateStore(guard.check)
        items = spool.discover()
        if len(items) != 1 or items[0][1] != "pending":
            raise RuntimeError("expected one pending synthetic item")
        with UploadClient(config, guard) as client:
            worker = UploadWorker(
                guard=guard,
                state_store=store,
                spool=spool,
                client=DiscardCompletedResponse(client, args.observed_response),
                validate_intent=validate_intent,
                validate_persisted_ack=validate_persisted_ack,
                faults=ExitAtFault("worker.retry_wait.durable", exit_code=97),
            )
            worker.run_item(items[0][0], location="pending")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
