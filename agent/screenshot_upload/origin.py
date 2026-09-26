"""Immutable spool-to-Backend origin binding."""

from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import re
from pathlib import Path
from typing import Callable

from .durable_fs import (
    FilesystemProtocolError,
    ensure_directory,
    ensure_local_filesystem,
    ensure_regular_file,
    publish_file_no_replace,
    sync_directory,
    write_temp,
)
from .jsonio import StrictJSONError, loads_strict
from .lock import ProcessLock


_DNS_LABEL = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
_PORT = re.compile(r"^[0-9]+$")
_BINDING_KEYS = {"binding_version", "backend_origin"}


class BindingError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Binding:
    backend_origin: str


def _canonical_port(raw: str | None, scheme: str) -> str:
    if raw is None:
        return ""
    if not _PORT.fullmatch(raw) or (len(raw) > 1 and raw.startswith("0")):
        raise ValueError("invalid port")
    port = int(raw)
    if not 1 <= port <= 65535:
        raise ValueError("invalid port")
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        return ""
    return f":{port}"


def _canonical_dns(host: str) -> str:
    if len(host) > 253 or host.endswith("."):
        raise ValueError("invalid DNS host")
    labels = host.split(".")
    if not labels or any(not _DNS_LABEL.fullmatch(label) for label in labels):
        raise ValueError("invalid DNS host")
    if any(label.lower().startswith("xn--") for label in labels):
        raise ValueError("IDNA labels are not supported")
    final = labels[-1]
    if not re.search(r"[A-Za-z]", final) or (
        final.lower().startswith("0x")
        and (len(final) == 2 or all(character in "0123456789abcdefABCDEF" for character in final[2:]))
    ):
        raise ValueError("numeric and hexadecimal host aliases are not supported")
    return host.lower()


def _canonical_ipv4(host: str) -> str:
    parts = host.split(".")
    if len(parts) != 4:
        raise ValueError("IPv4 must contain four components")
    values: list[str] = []
    for part in parts:
        if not part.isascii() or not part.isdecimal() or (len(part) > 1 and part.startswith("0")):
            raise ValueError("invalid IPv4 component")
        value = int(part)
        if value > 255:
            raise ValueError("invalid IPv4 component")
        values.append(str(value))
    return ".".join(values)


def canonicalize_origin(raw: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise ValueError("origin must be a nonempty string")
    if not raw.isascii() or any(ord(character) <= 0x20 or ord(character) == 0x7F for character in raw):
        raise ValueError("origin must contain visible ASCII without whitespace")
    if any(character in raw for character in "\\%@?#"):
        raise ValueError("origin contains a forbidden URL component")
    match = re.fullmatch(r"(?i:(http|https))://(.+?)(/?)", raw)
    if match is None:
        raise ValueError("origin must use http or https with no path")
    scheme = match.group(1).lower()
    authority = match.group(2)
    if authority.startswith("["):
        closing = authority.find("]")
        if closing < 0:
            raise ValueError("invalid bracketed IPv6 host")
        host_text = authority[1:closing]
        suffix = authority[closing + 1 :]
        if not host_text or "." in host_text or "%" in host_text:
            raise ValueError("invalid IPv6 host")
        if suffix and not suffix.startswith(":"):
            raise ValueError("invalid IPv6 authority")
        port = suffix[1:] if suffix else None
        if suffix == ":":
            raise ValueError("empty port")
        try:
            address = ipaddress.IPv6Address(host_text)
        except ipaddress.AddressValueError as exc:
            raise ValueError("invalid IPv6 host") from exc
        host = f"[{address.compressed.lower()}]"
    else:
        if authority.count(":") > 1:
            raise ValueError("IPv6 hosts must be bracketed")
        if ":" in authority:
            host_text, port = authority.rsplit(":", 1)
            if not port:
                raise ValueError("empty port")
        else:
            host_text, port = authority, None
        if not host_text:
            raise ValueError("empty host")
        if all(character in "0123456789." for character in host_text):
            host = _canonical_ipv4(host_text)
        else:
            host = _canonical_dns(host_text)
    return f"{scheme}://{host}{_canonical_port(port, scheme)}"


def _binding_bytes(origin: str) -> bytes:
    return f'{{"binding_version":1,"backend_origin":"{origin}"}}'.encode("utf-8")


def _read_binding(path: Path) -> Binding:
    try:
        result = ensure_regular_file(path)
        assert result is not None
        if result.st_size > 1024:
            raise BindingError("BINDING_INVALID", "binding.json exceeds 1 KiB")
        raw = path.read_bytes()
        value = loads_strict(raw, max_bytes=1024)
        if not isinstance(value, dict) or set(value) != _BINDING_KEYS:
            raise BindingError("BINDING_INVALID", "binding.json has an invalid schema")
        if type(value["binding_version"]) is not int or value["binding_version"] != 1:
            raise BindingError("BINDING_INVALID", "unsupported binding version")
        stored = value["backend_origin"]
        if not isinstance(stored, str) or canonicalize_origin(stored) != stored:
            raise BindingError("BINDING_INVALID", "stored origin is not canonical")
        if raw != _binding_bytes(stored):
            raise BindingError("BINDING_INVALID", "binding.json bytes are not canonical")
        return Binding(stored)
    except BindingError:
        raise
    except (OSError, FilesystemProtocolError, StrictJSONError, ValueError) as exc:
        raise BindingError("BINDING_INVALID", "binding.json is missing, unreadable, or invalid") from exc


def _validate_optional_temp(root: Path) -> None:
    temp = root / "binding.json.tmp"
    if temp.exists() or temp.is_symlink():
        try:
            ensure_regular_file(temp)
        except FilesystemProtocolError as exc:
            raise BindingError("BINDING_INVALID", "binding temp is not an ordinary file") from exc


def validate_binding(
    spool_root: str | Path,
    configured_origin: str,
    *,
    inspect_inventory: bool = True,
) -> Binding:
    root = Path(spool_root)
    try:
        canonical = canonicalize_origin(configured_origin)
    except ValueError as exc:
        raise BindingError("BINDING_INVALID", "configured origin is invalid") from exc
    try:
        ensure_directory(root)
        ensure_local_filesystem(root)
    except FilesystemProtocolError as exc:
        raise BindingError("BINDING_MISSING", "spool root is missing or unsafe") from exc
    final = root / "binding.json"
    if not final.exists() and not final.is_symlink():
        raise BindingError("BINDING_MISSING", "binding.json is absent")
    binding = _read_binding(final)
    _validate_optional_temp(root)
    if inspect_inventory:
        _inspect_bound_inventory(root)
    if binding.backend_origin != canonical:
        raise BindingError("BINDING_MISMATCH", "configured origin differs from immutable spool binding")
    return binding


def _empty_gitkeep(path: Path) -> None:
    result = ensure_regular_file(path)
    assert result is not None
    if result.st_size != 0:
        raise BindingError("BINDING_MISSING", ".gitkeep must be empty")


def _inspect_pristine(root: Path, *, allow_exact_temp: bool) -> bool:
    allowed_root = {".upload-agent.lock", ".gitkeep", "pending", "uploaded", "failed"}
    if allow_exact_temp:
        allowed_root.add("binding.json.tmp")
    for entry in root.iterdir():
        if entry.name not in allowed_root:
            raise BindingError("BINDING_MISSING", f"nonpristine spool entry: {entry.name}")
        if entry.name in {"pending", "uploaded", "failed"}:
            ensure_directory(entry)
            for child in entry.iterdir():
                if child.name != ".gitkeep":
                    raise BindingError("BINDING_MISSING", f"nonpristine queue entry: {child.name}")
                _empty_gitkeep(child)
        elif entry.name == ".gitkeep":
            _empty_gitkeep(entry)
        else:
            ensure_regular_file(entry)
    return (root / "binding.json.tmp").exists()


def _inspect_bound_inventory(root: Path) -> None:
    allowed = {
        ".upload-agent.lock", ".gitkeep", "binding.json", "binding.json.tmp",
        "pending", "uploaded", "failed",
    }
    try:
        for entry in root.iterdir():
            if entry.name not in allowed:
                raise BindingError("BINDING_INVALID", f"unexpected bound spool entry: {entry.name}")
            if entry.name in {"pending", "uploaded", "failed"}:
                ensure_directory(entry)
                for child in entry.iterdir():
                    if child.name == ".gitkeep":
                        _empty_gitkeep(child)
                    else:
                        ensure_directory(child)
            elif entry.name == ".gitkeep":
                _empty_gitkeep(entry)
            else:
                ensure_regular_file(entry)
        for name in ("pending", "uploaded", "failed"):
            ensure_directory(root / name)
    except BindingError:
        raise
    except (OSError, FilesystemProtocolError) as exc:
        raise BindingError("BINDING_INVALID", "bound spool inventory is unsafe") from exc


def initialize_binding(
    spool_root: str | Path,
    configured_origin: str,
    *,
    barrier: Callable[[str], None] | None = None,
) -> Binding:
    root = Path(spool_root)
    try:
        canonical = canonicalize_origin(configured_origin)
    except ValueError as exc:
        raise BindingError("BINDING_INVALID", "configured origin is invalid") from exc
    if not root.exists():
        root.mkdir(parents=True, exist_ok=False)
    ensure_directory(root)
    ensure_local_filesystem(root)
    with ProcessLock(root):
        final = root / "binding.json"
        temp = root / "binding.json.tmp"
        if final.exists() or final.is_symlink():
            binding = _read_binding(final)
            _validate_optional_temp(root)
            _inspect_bound_inventory(root)
            if binding.backend_origin != canonical:
                raise BindingError("BINDING_MISMATCH", "spool is already bound to another origin")
            return binding

        has_temp = _inspect_pristine(root, allow_exact_temp=True)
        if has_temp:
            ensure_regular_file(temp)
            temp.unlink()
            sync_directory(root)

        for name in ("pending", "uploaded", "failed"):
            directory = root / name
            if not directory.exists():
                directory.mkdir()
                sync_directory(root)
            ensure_directory(directory)

        expected = _binding_bytes(canonical)
        write_temp(temp, expected, barrier=barrier, barrier_name="binding.temp_fsynced")
        try:
            publish_file_no_replace(temp, final, barrier=barrier, barrier_name="binding.published")
        except FileExistsError:
            # Another conforming publisher may have won on a filesystem whose
            # locking scope is broader than this process.
            if temp.exists():
                temp.unlink()
            binding = _read_binding(final)
            if binding.backend_origin != canonical:
                raise BindingError("BINDING_MISMATCH", "concurrent init chose another origin")
            return binding
        binding = _read_binding(final)
        if final.read_bytes() != expected or binding.backend_origin != canonical:
            raise BindingError("BINDING_INVALID", "binding publication readback failed")
        return binding


class BindingGuard:
    """Immutable startup binding, revalidated before each protocol mutation."""

    __slots__ = ("_spool_root", "_binding")

    def __init__(self, spool_root: str | Path, configured_origin: str):
        self._spool_root = Path(spool_root)
        self._binding = validate_binding(self._spool_root, configured_origin)

    @property
    def backend_origin(self) -> str:
        return self._binding.backend_origin

    @property
    def spool_root(self) -> Path:
        return self._spool_root

    def check(self) -> Binding:
        current = validate_binding(
            self._spool_root,
            self._binding.backend_origin,
            inspect_inventory=False,
        )
        if current != self._binding:
            raise BindingError("BINDING_MISMATCH", "binding changed after startup")
        return self._binding
