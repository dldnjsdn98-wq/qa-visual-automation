from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import uuid4


AdapterStage = Literal["OCR", "VERIFY"]

SAFE_ADAPTER_ERROR_CODES = frozenset(
    {
        "SOURCE_DECODE_ERROR",
        "ENGINE_UNAVAILABLE",
        "MODEL_UNAVAILABLE",
        "ENGINE_TIMEOUT",
        "ENGINE_OUTPUT_INVALID",
        "RESULT_LIMIT_EXCEEDED",
        "INPUT_HASH_MISMATCH",
        "PROFILE_DIGEST_MISMATCH",
        "SNAPSHOT_INTEGRITY_ERROR",
        "NORMALIZATION_ERROR",
        "ENGINE_INTERNAL_ERROR",
    }
)


@dataclass(slots=True)
class AdapterError(Exception):
    code: str
    stage: AdapterStage
    diagnostic_id: str

    def __init__(
        self,
        code: str,
        stage: AdapterStage,
        diagnostic_id: str | None = None,
    ) -> None:
        if code not in SAFE_ADAPTER_ERROR_CODES:
            code = "ENGINE_INTERNAL_ERROR"
        if stage not in ("OCR", "VERIFY"):
            stage = "OCR"
            code = "ENGINE_INTERNAL_ERROR"
        self.code = code
        self.stage = stage
        self.diagnostic_id = diagnostic_id or str(uuid4())
        Exception.__init__(self, f"{self.stage}:{self.code}:{self.diagnostic_id}")

    def as_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "stage": self.stage,
            "diagnostic_id": self.diagnostic_id,
        }
