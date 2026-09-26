from __future__ import annotations

import hashlib

import pytest

from worker.ocr import AdapterError, load_fixture_profile_document, ocr_execute
from worker.verification import verify_execute


CONFIG = {
    "configuration_sha256": "b" * 64,
    "pass_threshold": 95,
    "review_threshold": 85,
    "normalization_version": "norm-v1",
    "matching_version": "one-to-one-levenshtein-v1",
}


def _snapshot(count: int, text: str = "A") -> dict[str, object]:
    return {
        "snapshot_version": 1,
        "sha256": "a" * 64,
        "items": [
            {
                "position": index,
                "string_key_id": f"key-{index}",
                "string_id": f"string-{index}",
                "entry_id": f"entry-{index}",
                "expected_text": text,
                "translation_status": "present",
            }
            for index in range(count)
        ],
    }


def _regions(count: int) -> list[dict[str, object]]:
    return [
        {
            "region_index": index,
            "text": "A",
            "confidence": 0.5,
            "confidence_semantics": "recognition",
            "detection_confidence": None,
            "detection_confidence_unavailable_reason": "NOT_EXPOSED_BY_PROFILE",
            "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]],
            "bbox": {"x": 0, "y": 0, "width": 1, "height": 1},
            "clipped": False,
            "engine_region_index": index,
        }
        for index in range(count)
    ]


def test_real_pair_limit_fails_before_distance_work() -> None:
    with pytest.raises(AdapterError) as raised:
        verify_execute(_snapshot(257), _regions(256), CONFIG)
    assert raised.value.code == "RESULT_LIMIT_EXCEEDED"
    assert raised.value.stage == "VERIFY"


def test_normalized_scalar_limit_fails_closed() -> None:
    with pytest.raises(AdapterError) as raised:
        verify_execute(_snapshot(101, "가" * 10_000), [], CONFIG)
    assert raised.value.code == "RESULT_LIMIT_EXCEEDED"


def test_nonfinite_region_confidence_is_invalid() -> None:
    regions = _regions(1)
    regions[0]["confidence"] = float("nan")
    with pytest.raises(AdapterError) as raised:
        verify_execute(_snapshot(1), regions, CONFIG)
    assert raised.value.code == "ENGINE_OUTPUT_INVALID"


def test_source_hash_mismatch_precedes_profile_dispatch() -> None:
    source = b"synthetic source"
    facts = {
        "source_sha256": "0" * 64,
        "size": len(source),
        "width": 1,
        "height": 1,
        "mime_type": "image/png",
        "locale_code": "en-US",
        "ocr_language": "en",
    }
    fixture = load_fixture_profile_document("fixture-contract-v1")
    with pytest.raises(AdapterError) as raised:
        ocr_execute(source, facts, fixture.manifest)
    assert raised.value.code == "INPUT_HASH_MISMATCH"


def test_test_only_profile_never_becomes_production_execution() -> None:
    source = b"synthetic source"
    facts = {
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "size": len(source),
        "width": 1,
        "height": 1,
        "mime_type": "image/png",
        "locale_code": "en-US",
        "ocr_language": "en",
    }
    fixture = load_fixture_profile_document("fixture-contract-v1")
    with pytest.raises(AdapterError) as raised:
        ocr_execute(source, facts, fixture.manifest)
    assert raised.value.code == "MODEL_UNAVAILABLE"
    assert fixture.production_eligible is False
