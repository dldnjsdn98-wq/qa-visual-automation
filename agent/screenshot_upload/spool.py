"""Directory-scan queue authority and no-overwrite item moves."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from .durable_fs import (
    ensure_directory,
    ensure_regular_file,
    rename_directory_no_replace,
    replace_file,
    write_temp,
)
from .manifest import ManifestError, ReadyItem, canonical_uuid, load_ready_item


class SpoolError(RuntimeError):
    pass


class Spool:
    LOCATIONS = ("pending", "uploaded", "failed")

    def __init__(self, root: str | Path, guard: object):
        self.root = Path(root)
        self.guard = guard
        ensure_directory(self.root)
        for name in self.LOCATIONS:
            ensure_directory(self.root / name)

    def _guard(self) -> object:
        return self.guard.check()

    def _inventory(self) -> dict[str, list[tuple[str, Path]]]:
        self._guard()
        by_id: dict[str, list[tuple[str, Path]]] = {}
        for location in self.LOCATIONS:
            queue = self.root / location
            ensure_directory(queue)
            for entry in sorted(queue.iterdir(), key=lambda value: value.name):
                if entry.name == ".gitkeep":
                    stat_result = ensure_regular_file(entry)
                    assert stat_result is not None
                    if stat_result.st_size != 0:
                        raise SpoolError(f"{location}/.gitkeep must be empty")
                    continue
                ensure_directory(entry)
                try:
                    item_id = canonical_uuid(entry.name, version4=True)
                except ManifestError as exc:
                    raise SpoolError(f"unexpected queue directory: {entry.name}") from exc
                by_id.setdefault(item_id, []).append((location, entry))
        duplicates = {item_id: entries for item_id, entries in by_id.items() if len(entries) != 1}
        if duplicates:
            raise SpoolError("duplicate queue identity exists across spool locations")
        return by_id

    @staticmethod
    def _has_ownership_evidence(path: Path) -> bool:
        return any((path / name).exists() or (path / name).is_symlink() for name in ("state.json", "initialized.json"))

    def quarantine_path(self, path: Path, location: str, code: str) -> None:
        self._guard()
        safe_code = "".join(character for character in code if character.isupper() or character.isdigit() or character == "_")[:64]
        if not safe_code:
            safe_code = "QUEUE_INVALID"
        diagnostic = path / f"diagnostic-{safe_code}.txt"
        temp = path / f"diagnostic-{safe_code}.tmp"
        if location == "failed" and diagnostic.exists() and not diagnostic.is_symlink():
            ensure_regular_file(diagnostic)
            return
        write_temp(temp, (safe_code + "\n").encode("ascii"), guard=self._guard)
        replace_file(temp, diagnostic, guard=self._guard)
        if location != "failed":
            destination = self.root / "failed" / path.name
            rename_directory_no_replace(path, destination, guard=self._guard)

    def discover(self) -> list[tuple[ReadyItem, str]]:
        inventory = self._inventory()
        found: list[tuple[ReadyItem, str]] = []
        for item_id in sorted(inventory):
            location, path = inventory[item_id][0]
            ready = path / "ready.json"
            if not ready.exists() and not ready.is_symlink():
                if location == "pending" and not self._has_ownership_evidence(path):
                    continue
                self.quarantine_path(path, location, "QUEUE_INCOMPLETE")
                continue
            try:
                item = load_ready_item(path)
            except Exception:
                self.quarantine_path(path, location, "LOCAL_INTENT_CHANGED")
                continue
            found.append((item, location))
        return found

    def find(self, client_upload_id: str, location: str) -> ReadyItem:
        item_id = canonical_uuid(client_upload_id, version4=True)
        inventory = self._inventory()
        entries = inventory.get(item_id)
        if entries is None or entries[0][0] != location:
            raise SpoolError(f"queue item is not in {location}")
        return load_ready_item(entries[0][1])

    def move(self, item: ReadyItem, destination: str) -> ReadyItem:
        if destination not in self.LOCATIONS:
            raise SpoolError("invalid queue destination")
        source = Path(item.item_dir)
        if source.parent.parent != self.root or source.parent.name not in self.LOCATIONS:
            raise SpoolError("item path is outside the spool queue")
        target = self.root / destination / source.name
        if source == target:
            return item
        rename_directory_no_replace(source, target, guard=self._guard)
        return replace(item, item_dir=target, image_path=target / item.image_path.name)
