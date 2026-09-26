from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from .errors import AdapterError
from .validation import require_closed_mapping, require_int, require_sha256


ADAPTER_VERSION = 1


def _source_facts(value: object) -> Mapping[str, Any]:
    facts = require_closed_mapping(
        value,
        required=frozenset(
            {
                "source_sha256",
                "size",
                "width",
                "height",
                "mime_type",
                "locale_code",
                "ocr_language",
            }
        ),
        stage="OCR",
        code="ENGINE_OUTPUT_INVALID",
    )
    require_sha256(
        facts["source_sha256"],
        stage="OCR",
        code="INPUT_HASH_MISMATCH",
    )
    require_int(
        facts["size"],
        minimum=1,
        maximum=20 * 1024 * 1024,
        stage="OCR",
        code="ENGINE_OUTPUT_INVALID",
    )
    require_int(
        facts["width"],
        minimum=1,
        maximum=16_384,
        stage="OCR",
        code="ENGINE_OUTPUT_INVALID",
    )
    require_int(
        facts["height"],
        minimum=1,
        maximum=16_384,
        stage="OCR",
        code="ENGINE_OUTPUT_INVALID",
    )
    if not all(
        isinstance(facts[key], str) and facts[key]
        for key in ("mime_type", "locale_code", "ocr_language")
    ):
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    return facts


def ocr_execute(
    source_bytes: bytes,
    source_facts: Mapping[str, object],
    profile_manifest: Mapping[str, object],
) -> dict[str, object]:
    try:
        if not isinstance(source_bytes, bytes):
            raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
        facts = _source_facts(source_facts)
        if len(source_bytes) != facts["size"]:
            raise AdapterError("INPUT_HASH_MISMATCH", "OCR")
        source_sha256 = hashlib.sha256(source_bytes).hexdigest()
        if source_sha256 != facts["source_sha256"]:
            raise AdapterError("INPUT_HASH_MISMATCH", "OCR")
        if not isinstance(profile_manifest, Mapping):
            raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
        manifest_dict = dict(profile_manifest)
        try:
            import rfc8785
        except ImportError as error:
            raise AdapterError("ENGINE_UNAVAILABLE", "OCR") from error
        canonical_manifest = rfc8785.dumps(manifest_dict)
        profile_sha256 = hashlib.sha256(canonical_manifest).hexdigest()
        qualification = manifest_dict.get("qualification")
        if not isinstance(qualification, Mapping) or qualification.get("status") != "QUALIFIED":
            raise AdapterError("MODEL_UNAVAILABLE", "OCR")
        if manifest_dict.get("production_eligible") is not True:
            raise AdapterError("MODEL_UNAVAILABLE", "OCR")
        engine = manifest_dict.get("engine")
        if not isinstance(engine, Mapping) or engine.get("name") != "paddleocr":
            raise AdapterError("ENGINE_UNAVAILABLE", "OCR")
        from .paddle_engine import execute_paddle

        return execute_paddle(
            source_bytes=source_bytes,
            source_facts=facts,
            profile_manifest=manifest_dict,
            profile_sha256=profile_sha256,
        )
    except AdapterError:
        raise
    except ImportError as error:
        raise AdapterError("ENGINE_UNAVAILABLE", "OCR") from error
    except Exception as error:
        raise AdapterError("ENGINE_INTERNAL_ERROR", "OCR") from error
