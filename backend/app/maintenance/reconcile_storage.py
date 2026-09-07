"""Exclusive storage maintenance. Stop upload writers before invoking this command."""
import argparse
import hashlib
import json
import time
from sqlalchemy import select, text
from backend.app.db import SessionFactory
from backend.app.models import Screenshot
from backend.app.api.dependencies import get_storage
from backend.app.storage.base import ObjectNotFound


def reconcile(factory, storage, *, writers_stopped, apply=False, now=None):
    if not writers_stopped:
        raise ValueError("Stop upload writers and drain/terminate in-flight requests first")
    now = time.time() if now is None else now
    report = {"apply": apply, "orphans": [], "staging": [], "missing": [], "mismatches": [], "deleted": []}
    with factory() as session:
        if session.scalar(text("SELECT pg_is_in_recovery()")):
            raise ValueError("Maintenance requires primary database")
        rows = list(session.scalars(select(Screenshot)))
        references = {row.storage_key for row in rows}
        # Complete DB and storage inventory before any deletion; fail closed.
        def inventory(method):
            items, offset = [], 0
            while page := method(offset, 100):
                items.extend(page)
                offset += len(page)
            return items
        objects = inventory(storage.list_objects)
        stages = inventory(storage.list_staging)
        for row in rows:
            try:
                stream, size = storage.open_read(row.storage_key)
                with stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                if size != row.size_bytes or digest != row.file_hash:
                    report["mismatches"].append(row.storage_key)
            except ObjectNotFound:
                report["missing"].append(row.storage_key)
        report["orphans"] = [item.key for item in objects if item.key not in references and item.modified_at < now - 86400]
        report["staging"] = [item.key for item in stages if item.modified_at < now - 86400]
    if apply:
        for key in report["orphans"] + report["staging"]:
            # New primary snapshot immediately before each exact-key deletion.
            with factory() as session:
                if session.scalar(text("SELECT pg_is_in_recovery()")):
                    raise ValueError("Primary unavailable")
                if session.scalar(select(Screenshot.id).where(Screenshot.storage_key == key)) is not None:
                    continue
                if key.startswith("staging/"):
                    storage.discard_stage(key.split("/")[1])
                else:
                    storage.delete(key)
                report["deleted"].append(key)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--writers-stopped", action="store_true", required=True)
    parser.add_argument("--apply", action="store_true", help="Default is dry run")
    args = parser.parse_args()
    print(json.dumps(reconcile(SessionFactory, get_storage(), writers_stopped=args.writers_stopped, apply=args.apply), indent=2))


if __name__ == "__main__":
    main()
