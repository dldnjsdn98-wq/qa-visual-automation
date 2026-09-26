import hashlib
import os
import re
import stat
from pathlib import Path
from uuid import uuid4
from backend.app.errors import DomainError
from backend.app.validation.images import inspect_image
from .base import (
    ObjectExists,
    ObjectMismatch,
    ObjectNotFound,
    StagedObject,
    StoredObject,
    StorageError,
)

ROOT = Path(__file__).resolve().parents[3]
UUID_PATTERN = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
OBJECT_PATTERN = rf"objects/{UUID_PATTERN}/{UUID_PATTERN}\.(?:png|jpg)"


class LocalStorage:
    def __init__(self, root):
        self.root = Path(os.path.abspath(ROOT / root))
        self._check_components(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _check_components(path):
        for candidate in [*reversed(path.parents), path]:
            if candidate.exists() or candidate.is_symlink():
                info = candidate.lstat()
                if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                    raise StorageError("Storage links/reparse points are not permitted")

    def _path(self, key, stage=False):
        pattern = rf"staging/{UUID_PATTERN}" if stage else OBJECT_PATTERN
        if not re.fullmatch(pattern, key):
            raise StorageError("Invalid storage key")
        path = self.root / key
        self._check_components(path)
        if not path.resolve().is_relative_to(self.root.resolve()):
            raise StorageError("Storage escape")
        return path

    @staticmethod
    def _sync_dir(path):
        if os.name != "nt":
            descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)

    def stage(self, stream, limit=20_971_520):
        token = str(uuid4())
        path = self._path(f"staging/{token}", stage=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        digest, size = hashlib.sha256(), 0
        try:
            with path.open("xb") as output:
                while chunk := stream.read(65536):
                    size += len(chunk)
                    if size > limit:
                        raise DomainError(413, "UPLOAD_TOO_LARGE", "File exceeds 20 MiB")
                    output.write(chunk)
                    digest.update(chunk)
                if not size:
                    raise DomainError(422, "INVALID_IMAGE", "File is empty")
                output.flush()
                os.fsync(output.fileno())
            return StagedObject(token, size, digest.hexdigest())
        except BaseException:
            path.unlink(missing_ok=True)
            raise

    def inspect(self, staged, media_type):
        with self._path(f"staging/{staged.token}", stage=True).open("rb") as stream:
            return inspect_image(stream, media_type)

    def publish(self, staged, key):
        source = self._path(f"staging/{staged.token}", stage=True)
        target = self._path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._check_components(target.parent)
        try:
            # Hard-link publication is atomic and cannot overwrite on NTFS/POSIX.
            os.link(source, target)
        except FileExistsError:
            raise ObjectExists("Object already exists") from None
        self._sync_dir(target.parent)
        self._sync_dir(target.parent.parent)
        source.unlink()
        self._sync_dir(source.parent)
        return self.stat(key)

    def open_read(self, key):
        try:
            stream = self._path(key).open("rb")
            return stream, os.fstat(stream.fileno()).st_size
        except FileNotFoundError:
            raise ObjectNotFound("Object not found") from None

    def verify_exact(self, key, *, sha256, byte_count):
        """Verify immutable facts from one open handle without replacing the object."""
        try:
            with self._path(key).open("rb") as stream:
                before = os.fstat(stream.fileno())
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
                after = os.fstat(stream.fileno())
        except FileNotFoundError:
            raise ObjectNotFound("Object not found") from None

        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        )
        if identity_before != identity_after:
            raise StorageError("Object changed during verification")
        if after.st_size != byte_count or digest != sha256:
            raise ObjectMismatch("Object hash or size does not match")
        return StoredObject(key, after.st_size, after.st_mtime)

    def stat(self, key):
        try:
            info = self._path(key).stat()
            return StoredObject(key, info.st_size, info.st_mtime)
        except FileNotFoundError:
            raise ObjectNotFound("Object not found") from None

    def delete(self, key):
        path = self._path(key)
        path.unlink(missing_ok=True)
        if path.parent.exists():
            self._sync_dir(path.parent)

    def discard_stage(self, token):
        self._path(f"staging/{token}", stage=True).unlink(missing_ok=True)

    def _list(self, staging, offset, limit):
        directory = self.root / ("staging" if staging else "objects")
        self._check_components(directory)
        items = []
        if directory.exists():
            for parent, directories, files in os.walk(directory, followlinks=False):
                for name in directories:
                    self._check_components(Path(parent) / name)
                for name in files:
                    path = Path(parent) / name
                    key = path.relative_to(self.root).as_posix()
                    self._path(key, stage=staging)
                    info = path.stat()
                    items.append(StoredObject(key, info.st_size, info.st_mtime))
        return sorted(items, key=lambda item: item.key)[offset:offset + limit]

    def list_objects(self, offset=0, limit=100):
        return self._list(False, offset, limit)

    def list_staging(self, offset=0, limit=100):
        return self._list(True, offset, limit)
