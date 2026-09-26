from __future__ import annotations

import unicodedata

from worker.ocr.errors import AdapterError
from worker.ocr.validation import require_scalar_text


NORMALIZATION_VERSION = "norm-v1"
UNICODE_DATA_VERSION = "15.0.0"

WHITE_SPACE_CODEPOINTS = frozenset(
    [
        *range(0x0009, 0x000E),
        0x0020,
        0x0085,
        0x00A0,
        0x1680,
        *range(0x2000, 0x200B),
        0x2028,
        0x2029,
        0x202F,
        0x205F,
        0x3000,
    ]
)


def ensure_unicode_runtime() -> None:
    if unicodedata.unidata_version != UNICODE_DATA_VERSION:
        raise AdapterError("NORMALIZATION_ERROR", "VERIFY")


def normalize_v1(value: str) -> str:
    ensure_unicode_runtime()
    raw = require_scalar_text(
        value,
        maximum=10_000,
        stage="VERIFY",
        code="NORMALIZATION_ERROR",
    )
    canonical_newlines = raw.replace("\r\n", "\n").replace("\r", "\n")
    nfc = unicodedata.normalize("NFC", canonical_newlines)
    output: list[str] = []
    in_space = False
    for char in nfc:
        if ord(char) in WHITE_SPACE_CODEPOINTS:
            if not in_space:
                output.append(" ")
                in_space = True
        else:
            output.append(char)
            in_space = False
    return "".join(output).strip(" ")
