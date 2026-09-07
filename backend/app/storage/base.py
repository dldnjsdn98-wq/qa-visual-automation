from dataclasses import dataclass
from typing import Protocol, BinaryIO


class StorageError(OSError):
    pass


class ObjectNotFound(StorageError):
    pass


class ObjectExists(StorageError):
    pass


@dataclass(frozen=True)
class StagedObject:
    token: str
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class StoredObject:
    key: str
    byte_count: int
    modified_at: float


class Storage(Protocol):
    def stage(self, stream: BinaryIO, limit: int) -> StagedObject: ...
    def inspect(self, staged: StagedObject, media_type: str): ...
    def publish(self, staged: StagedObject, key: str) -> StoredObject: ...
    def open_read(self, key: str) -> tuple[BinaryIO, int]: ...
    def stat(self, key: str) -> StoredObject: ...
    def delete(self, key: str) -> None: ...
    def discard_stage(self, token: str) -> None: ...
    def list_objects(self, offset: int = 0, limit: int = 100) -> list[StoredObject]: ...
    def list_staging(self, offset: int = 0, limit: int = 100) -> list[StoredObject]: ...
