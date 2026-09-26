"""OS-owned exclusive spool lock."""

from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO

from .durable_fs import ensure_directory, ensure_regular_file


class LockUnavailable(RuntimeError):
    pass


class ProcessLock:
    """Hold the spool lock for the lifetime of an explicit context manager."""

    def __init__(self, spool_root: str | Path):
        self.spool_root = Path(spool_root)
        self.path = self.spool_root / ".upload-agent.lock"
        self._stream: BinaryIO | None = None

    def __enter__(self) -> "ProcessLock":
        ensure_directory(self.spool_root)
        ensure_regular_file(self.path, allow_missing=True)
        stream = self.path.open("a+b")
        try:
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b"\0")
                stream.flush()
                os.fsync(stream.fileno())
            stream.seek(0)
            if os.name == "nt":
                import msvcrt

                try:
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError as exc:
                    raise LockUnavailable("upload spool is already locked") from exc
            else:
                import fcntl

                try:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as exc:
                    raise LockUnavailable("upload spool is already locked") from exc
        except BaseException:
            stream.close()
            raise
        self._stream = stream
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        stream = self._stream
        self._stream = None
        if stream is None:
            return
        try:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        finally:
            stream.close()
