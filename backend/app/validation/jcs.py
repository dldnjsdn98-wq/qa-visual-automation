from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal, InvalidOperation
from typing import Any

import rfc8785

from backend.app.errors import DomainError
from .unicode import decode_json, validate_unicode


SAFE_INTEGER = 9_007_199_254_740_991


def _invalid(reason: str) -> DomainError:
    return DomainError(field="metadata", reason=reason)


def _reject_constant(_: str) -> None:
    raise _invalid("nonfinite numbers are not allowed")


def _parse_int(token: str) -> int:
    value = int(token)
    if abs(value) > SAFE_INTEGER:
        raise _invalid("integral number exceeds the safe binary64 range")
    return value


def _parse_float(token: str) -> float:
    try:
        exact = Decimal(token)
        value = float(token)
    except (InvalidOperation, OverflowError, ValueError):
        raise _invalid("number is outside the binary64 domain") from None
    if not math.isfinite(value):
        raise _invalid("number is outside the binary64 domain")
    if value == 0.0 and exact != 0:
        raise _invalid("nonzero number underflows binary64")
    if value.is_integer() and abs(value) > SAFE_INTEGER:
        raise _invalid("integral number exceeds the safe binary64 range")
    return value


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _invalid("duplicate object keys are not allowed")
        result[key] = value
    return result


def decode_agent_json(raw: bytes | str) -> Any:
    try:
        decoded = raw.decode("utf-8", "strict") if isinstance(raw, bytes) else raw
    except UnicodeDecodeError:
        raise _invalid("invalid UTF-8") from None
    try:
        value = json.loads(
            decoded,
            object_pairs_hook=_object_without_duplicates,
            parse_int=_parse_int,
            parse_float=_parse_float,
            parse_constant=_reject_constant,
        )
    except DomainError:
        raise
    except (ValueError, RecursionError):
        raise _invalid("invalid JSON") from None
    try:
        return validate_unicode(value, "metadata")
    except RecursionError:
        raise _invalid("nesting limit exceeded") from None


def decode_upload_json(raw: bytes) -> Any:
    """Preserve Phase 1 parsing for manual input; enforce strict token rules for agents."""
    ordinary = decode_json(raw, "metadata")
    if isinstance(ordinary, dict) and ordinary.get("source") in ("agent", "automation"):
        return decode_agent_json(raw)
    return ordinary


def canonicalize_fingerprint(payload: dict[str, Any]) -> tuple[bytes, str]:
    try:
        canonical = rfc8785.dumps(payload)
    except rfc8785.CanonicalizationError:
        raise _invalid("value cannot be represented by fingerprint version 1") from None
    return canonical, hashlib.sha256(canonical).hexdigest()
