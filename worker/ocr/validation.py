from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from typing import Any

from .errors import AdapterError


LOWER_HEX = frozenset("0123456789abcdef")


def require_closed_mapping(
    value: object,
    *,
    required: frozenset[str],
    optional: frozenset[str] = frozenset(),
    stage: str = "OCR",
    code: str = "ENGINE_OUTPUT_INVALID",
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AdapterError(code, stage)  # type: ignore[arg-type]
    keys = set(value)
    if not required.issubset(keys) or keys - required - optional:
        raise AdapterError(code, stage)  # type: ignore[arg-type]
    if not all(isinstance(key, str) for key in keys):
        raise AdapterError(code, stage)  # type: ignore[arg-type]
    return value


def require_sequence(value: object, *, stage: str, code: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise AdapterError(code, stage)  # type: ignore[arg-type]
    return value


def require_int(
    value: object,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
    stage: str,
    code: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AdapterError(code, stage)  # type: ignore[arg-type]
    if minimum is not None and value < minimum:
        raise AdapterError(code, stage)  # type: ignore[arg-type]
    if maximum is not None and value > maximum:
        raise AdapterError(code, stage)  # type: ignore[arg-type]
    return value


def require_finite_number(
    value: object,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    stage: str,
    code: str,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AdapterError(code, stage)  # type: ignore[arg-type]
    result = float(value)
    if not math.isfinite(result):
        raise AdapterError(code, stage)  # type: ignore[arg-type]
    if minimum is not None and result < minimum:
        raise AdapterError(code, stage)  # type: ignore[arg-type]
    if maximum is not None and result > maximum:
        raise AdapterError(code, stage)  # type: ignore[arg-type]
    return result


def require_scalar_text(
    value: object,
    *,
    maximum: int,
    stage: str,
    code: str,
) -> str:
    if not isinstance(value, str) or len(value) > maximum or "\x00" in value:
        raise AdapterError(code, stage)  # type: ignore[arg-type]
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise AdapterError(code, stage)  # type: ignore[arg-type]
    return value


def require_sha256(value: object, *, stage: str, code: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(char not in LOWER_HEX for char in value)
    ):
        raise AdapterError(code, stage)  # type: ignore[arg-type]
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
