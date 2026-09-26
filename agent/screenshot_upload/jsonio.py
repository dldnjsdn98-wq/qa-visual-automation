"""Strict JSON primitives for the upload spool protocol."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import json
import math
from typing import Any


MAX_SAFE_INTEGER = 9_007_199_254_740_991


class StrictJSONError(ValueError):
    """Raised when JSON is not in the protocol's accepted input domain."""


def _parse_int(token: str) -> int:
    value = int(token)
    if abs(value) > MAX_SAFE_INTEGER:
        raise StrictJSONError("integer is outside the binary64 safe integer range")
    return value


def _parse_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise StrictJSONError("number is not finite binary64")
    try:
        decimal_value = Decimal(token)
    except InvalidOperation as exc:  # pragma: no cover - json validates syntax first
        raise StrictJSONError("invalid number") from exc
    if value == 0.0 and decimal_value != 0:
        raise StrictJSONError("nonzero number underflows binary64")
    if value.is_integer() and abs(value) > MAX_SAFE_INTEGER:
        raise StrictJSONError("integral number is outside the binary64 safe range")
    return value


def _reject_constant(token: str) -> None:
    raise StrictJSONError(f"unsupported numeric token: {token}")


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise StrictJSONError(f"duplicate object key: {key!r}")
        result[key] = value
    return result


def validate_unicode(value: Any) -> None:
    if isinstance(value, str):
        if "\x00" in value:
            raise StrictJSONError("U+0000 is not allowed")
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise StrictJSONError("surrogate scalar is not allowed")
    elif isinstance(value, dict):
        for key, child in value.items():
            validate_unicode(key)
            validate_unicode(child)
    elif isinstance(value, list):
        for child in value:
            validate_unicode(child)


def loads_strict(raw: bytes | str, *, max_bytes: int | None = None) -> Any:
    if isinstance(raw, bytes):
        if max_bytes is not None and len(raw) > max_bytes:
            raise StrictJSONError("JSON document exceeds size limit")
        if raw.startswith(b"\xef\xbb\xbf"):
            raise StrictJSONError("UTF-8 BOM is not allowed")
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise StrictJSONError("invalid UTF-8") from exc
    else:
        text = raw
        if max_bytes is not None and len(text.encode("utf-8")) > max_bytes:
            raise StrictJSONError("JSON document exceeds size limit")
        if text.startswith("\ufeff"):
            raise StrictJSONError("UTF-8 BOM is not allowed")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object,
            parse_int=_parse_int,
            parse_float=_parse_float,
            parse_constant=_reject_constant,
        )
    except StrictJSONError:
        raise
    except (ValueError, RecursionError) as exc:
        raise StrictJSONError("invalid JSON") from exc
    validate_unicode(value)
    return value


def dumps_compact(value: Any) -> bytes:
    validate_unicode(value)
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise StrictJSONError("value is not JSON serializable") from exc
    # Decode through the strict parser so producer output cannot escape the
    # accepted numeric and Unicode domain.
    loads_strict(encoded)
    return encoded
