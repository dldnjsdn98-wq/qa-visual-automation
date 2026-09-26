"""Uploader runtime configuration and narrow Backend-origin validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from .origin import canonicalize_origin


class ConfigError(ValueError):
    pass


def canonical_backend_origin(origin: str) -> str:
    """Expose the binding canonicalizer with the configuration exception type."""

    try:
        return canonicalize_origin(origin)
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc


def canonical_uuid(value: object, field: str) -> str:
    if type(value) is not str:
        raise ConfigError(f"{field} must be a UUID string")
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ConfigError(f"{field} must be a UUID") from exc
    canonical = str(parsed)
    if value != canonical:
        raise ConfigError(f"{field} must be canonical lowercase UUID text")
    return canonical


@dataclass(frozen=True)
class RuntimeConfig:
    spool_root: Path
    backend_origin: str
    connect_timeout: float = 5.0
    read_timeout: float = 30.0
    write_timeout: float = 30.0
    pool_timeout: float = 30.0
    attempt_deadline: float = 120.0
    response_limit: int = 128 * 1024
    max_attempts: int = 8

    def __post_init__(self) -> None:
        canonical = canonical_backend_origin(self.backend_origin)
        if canonical != self.backend_origin:
            raise ConfigError("backend_origin must already be canonical")
        if self.connect_timeout != 5.0 or any(
            value != 30.0 for value in (self.read_timeout, self.write_timeout, self.pool_timeout)
        ):
            raise ConfigError("protocol v1 HTTP timeouts are fixed")
        if self.attempt_deadline != 120.0 or self.response_limit != 128 * 1024:
            raise ConfigError("protocol v1 attempt and response limits are fixed")
        if self.max_attempts != 8:
            raise ConfigError("protocol v1 permits exactly 8 attempts per epoch")

    @classmethod
    def create(cls, spool_root: str | Path, backend_origin: str) -> "RuntimeConfig":
        root = Path(spool_root).expanduser().absolute()
        return cls(spool_root=root, backend_origin=canonical_backend_origin(backend_origin))
