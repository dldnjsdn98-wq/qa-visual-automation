"""RFC 8785 canonical JSON helpers for uploader protocol version 1."""

from __future__ import annotations

from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
import math
from collections.abc import Mapping
from typing import Any


MAX_SAFE_INTEGER = 9_007_199_254_740_991


class CanonicalizationError(ValueError):
    """A value is outside the upload protocol's canonical JSON domain."""


class CanonicalizationUnavailable(RuntimeError):
    """The reviewed RFC 8785 implementation is unavailable."""


def _validate_string(value: str, path: str) -> None:
    for character in value:
        codepoint = ord(character)
        if codepoint == 0 or 0xD800 <= codepoint <= 0xDFFF:
            raise CanonicalizationError(f"{path} contains an invalid Unicode scalar")


def validate_value(value: Any, path: str = "$") -> None:
    """Validate values before passing them to rfc8785.

    Parsing duplicate keys and numeric-token underflow is the manifest parser's
    responsibility.  This function prevents Python-only values and values outside
    the protocol's finite binary64/safe-integral domain from reaching JCS.
    """

    if value is None or type(value) is bool:
        return
    if type(value) is str:
        _validate_string(value, path)
        return
    if type(value) is int:
        if not -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER:
            raise CanonicalizationError(f"{path} is outside the safe integer domain")
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise CanonicalizationError(f"{path} must be finite")
        if value.is_integer() and not -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER:
            raise CanonicalizationError(f"{path} is outside the safe integer domain")
        return
    if type(value) in (list, tuple):
        for index, member in enumerate(value):
            validate_value(member, f"{path}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, member in value.items():
            if type(key) is not str:
                raise CanonicalizationError(f"{path} contains a non-string object key")
            _validate_string(key, f"{path}.<key>")
            validate_value(member, f"{path}.{key}")
        return
    raise CanonicalizationError(f"{path} contains unsupported type {type(value).__name__}")


def _json_value(value: Any) -> Any:
    """Thaw A's immutable Mapping/tuple representation for the JCS package."""

    if isinstance(value, Mapping):
        return {key: _json_value(member) for key, member in value.items()}
    if type(value) in (list, tuple):
        return [_json_value(member) for member in value]
    return value


def _rfc8785_module():
    try:
        installed = version("rfc8785")
        module = import_module("rfc8785")
    except (PackageNotFoundError, ModuleNotFoundError) as exc:
        raise CanonicalizationUnavailable(
            "rfc8785 0.1.4 is required for upload canonicalization"
        ) from exc
    if installed != "0.1.4":
        raise CanonicalizationUnavailable(
            f"rfc8785 0.1.4 is required; found {installed}"
        )
    if not callable(getattr(module, "dumps", None)):
        raise CanonicalizationUnavailable("rfc8785.dumps is unavailable")
    return module


def canonical_bytes(value: Any) -> bytes:
    """Return exact RFC 8785 UTF-8 bytes with no BOM or trailing newline."""

    validate_value(value)
    module = _rfc8785_module()
    try:
        rendered = module.dumps(_json_value(value))
    except Exception as exc:  # rfc8785 exposes package-specific value errors
        raise CanonicalizationError("value cannot be serialized as RFC 8785 JSON") from exc
    if type(rendered) is not bytes:
        raise CanonicalizationUnavailable("rfc8785.dumps did not return bytes")
    if rendered.startswith(b"\xef\xbb\xbf") or rendered.endswith(b"\n"):
        raise CanonicalizationUnavailable("rfc8785.dumps returned noncanonical framing")
    return rendered


def canonical_equal(left: Any, right: Any) -> bool:
    """Compare JSON values by their exact RFC 8785 representation."""

    return canonical_bytes(left) == canonical_bytes(right)
