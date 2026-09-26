from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from typing import Any

from worker.ocr.errors import AdapterError
from worker.ocr.schemas import validate_schema_instance
from worker.ocr.validation import (
    require_closed_mapping,
    require_int,
    require_scalar_text,
    require_sequence,
    require_sha256,
)

from .assignment import CandidateEdge, assign_candidates
from .levenshtein import score_ratio
from .normalization import NORMALIZATION_VERSION, normalize_v1


ADAPTER_VERSION = 1
MATCHING_VERSION = "one-to-one-levenshtein-v1"
MAX_ITEMS = 1_000
MAX_REGIONS = 1_000
MAX_REAL_PAIRS = 65_536
MAX_NORMALIZED_SCALARS = 1_000_000
MAX_DISTANCE_WORK = 50_000_000


def _threshold(value: object) -> tuple[Decimal, int, int]:
    if isinstance(value, bool):
        raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY") from None
    if not decimal_value.is_finite() or not (Decimal(0) <= decimal_value <= Decimal(100)):
        raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
    exponent = decimal_value.as_tuple().exponent
    if exponent < -2:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
    scale = max(0, -exponent)
    denominator = 10**scale
    numerator = int(decimal_value * denominator)
    return decimal_value, numerator, denominator


def _at_least(
    score_numerator: int,
    score_denominator: int,
    threshold_numerator: int,
    threshold_denominator: int,
) -> bool:
    return (
        score_numerator * threshold_denominator
        >= threshold_numerator * score_denominator
    )


def _display_score(numerator: int, denominator: int) -> float:
    value = (Decimal(numerator) / Decimal(denominator)).quantize(
        Decimal("0.000001"),
        rounding=ROUND_HALF_EVEN,
    )
    return float(value)


def _parse_config(value: object) -> dict[str, Any]:
    validate_schema_instance("verification-config", value, stage="VERIFY")
    config = require_closed_mapping(
        value,
        required=frozenset(
            {
                "configuration_sha256",
                "pass_threshold",
                "review_threshold",
                "normalization_version",
                "matching_version",
            }
        ),
        stage="VERIFY",
        code="ENGINE_OUTPUT_INVALID",
    )
    configuration_sha256 = require_sha256(
        config["configuration_sha256"],
        stage="VERIFY",
        code="PROFILE_DIGEST_MISMATCH",
    )
    if config["normalization_version"] != NORMALIZATION_VERSION:
        raise AdapterError("NORMALIZATION_ERROR", "VERIFY")
    if config["matching_version"] != MATCHING_VERSION:
        raise AdapterError("PROFILE_DIGEST_MISMATCH", "VERIFY")
    pass_value, pass_numerator, pass_denominator = _threshold(config["pass_threshold"])
    review_value, review_numerator, review_denominator = _threshold(
        config["review_threshold"]
    )
    if review_value >= pass_value:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
    return {
        "configuration_sha256": configuration_sha256,
        "pass_threshold": pass_value,
        "pass_numerator": pass_numerator,
        "pass_denominator": pass_denominator,
        "review_threshold": review_value,
        "review_numerator": review_numerator,
        "review_denominator": review_denominator,
    }


def _parse_expected_snapshot(value: object) -> tuple[str, list[dict[str, Any]]]:
    validate_schema_instance("expected-snapshot", value, stage="VERIFY")
    snapshot = require_closed_mapping(
        value,
        required=frozenset({"snapshot_version", "sha256", "items"}),
        optional=frozenset(
            {
                "captured_at",
                "source_mode",
                "locale_code",
                "ocr_language",
                "screenshot",
                "item_count",
                "missing_count",
            }
        ),
        stage="VERIFY",
        code="SNAPSHOT_INTEGRITY_ERROR",
    )
    if snapshot["snapshot_version"] != 1:
        raise AdapterError("SNAPSHOT_INTEGRITY_ERROR", "VERIFY")
    snapshot_sha256 = require_sha256(
        snapshot["sha256"],
        stage="VERIFY",
        code="SNAPSHOT_INTEGRITY_ERROR",
    )
    raw_items = require_sequence(
        snapshot["items"],
        stage="VERIFY",
        code="SNAPSHOT_INTEGRITY_ERROR",
    )
    if len(raw_items) > MAX_ITEMS:
        raise AdapterError("RESULT_LIMIT_EXCEEDED", "VERIFY")
    items: list[dict[str, Any]] = []
    positions: set[int] = set()
    string_key_ids: set[str] = set()
    string_ids: set[str] = set()
    for raw_item in raw_items:
        item = require_closed_mapping(
            raw_item,
            required=frozenset(
                {
                    "position",
                    "string_key_id",
                    "string_id",
                    "entry_id",
                    "expected_text",
                    "translation_status",
                }
            ),
            stage="VERIFY",
            code="SNAPSHOT_INTEGRITY_ERROR",
        )
        position = require_int(
            item["position"],
            minimum=0,
            maximum=999,
            stage="VERIFY",
            code="SNAPSHOT_INTEGRITY_ERROR",
        )
        if position in positions:
            raise AdapterError("SNAPSHOT_INTEGRITY_ERROR", "VERIFY")
        positions.add(position)
        status = item["translation_status"]
        if status not in ("present", "missing"):
            raise AdapterError("SNAPSHOT_INTEGRITY_ERROR", "VERIFY")
        expected = item["expected_text"]
        entry_id = item["entry_id"]
        if status == "missing":
            if expected is not None or entry_id is not None:
                raise AdapterError("SNAPSHOT_INTEGRITY_ERROR", "VERIFY")
        else:
            expected = require_scalar_text(
                expected,
                maximum=10_000,
                stage="VERIFY",
                code="SNAPSHOT_INTEGRITY_ERROR",
            )
        for identifier in ("string_key_id", "string_id"):
            if not isinstance(item[identifier], str) or not item[identifier]:
                raise AdapterError("SNAPSHOT_INTEGRITY_ERROR", "VERIFY")
        if entry_id is not None and (not isinstance(entry_id, str) or not entry_id):
            raise AdapterError("SNAPSHOT_INTEGRITY_ERROR", "VERIFY")
        if status == "present" and entry_id is None:
            raise AdapterError("SNAPSHOT_INTEGRITY_ERROR", "VERIFY")
        if item["string_key_id"] in string_key_ids or item["string_id"] in string_ids:
            raise AdapterError("SNAPSHOT_INTEGRITY_ERROR", "VERIFY")
        string_key_ids.add(item["string_key_id"])
        string_ids.add(item["string_id"])
        items.append(
            {
                "position": position,
                "string_key_id": item["string_key_id"],
                "string_id": item["string_id"],
                "entry_id": entry_id,
                "expected_text": expected,
                "translation_status": status,
            }
        )
    items.sort(key=lambda item: item["position"])
    if "item_count" in snapshot and snapshot["item_count"] != len(items):
        raise AdapterError("SNAPSHOT_INTEGRITY_ERROR", "VERIFY")
    if "missing_count" in snapshot and snapshot["missing_count"] != sum(
        item["translation_status"] == "missing" for item in items
    ):
        raise AdapterError("SNAPSHOT_INTEGRITY_ERROR", "VERIFY")
    return snapshot_sha256, items


def _parse_regions(value: object) -> list[dict[str, Any]]:
    validate_schema_instance("canonical-regions", value, stage="VERIFY")
    raw_regions = require_sequence(
        value,
        stage="VERIFY",
        code="ENGINE_OUTPUT_INVALID",
    )
    if len(raw_regions) > MAX_REGIONS:
        raise AdapterError("RESULT_LIMIT_EXCEEDED", "VERIFY")
    regions: list[dict[str, Any]] = []
    for expected_index, raw_region in enumerate(raw_regions):
        region = require_closed_mapping(
            raw_region,
            required=frozenset(
                {
                    "region_index",
                    "text",
                    "confidence",
                    "confidence_semantics",
                    "detection_confidence",
                    "detection_confidence_unavailable_reason",
                    "polygon",
                    "bbox",
                    "clipped",
                    "engine_region_index",
                }
            ),
            stage="VERIFY",
            code="ENGINE_OUTPUT_INVALID",
        )
        region_index = require_int(
            region["region_index"],
            minimum=0,
            maximum=999,
            stage="VERIFY",
            code="ENGINE_OUTPUT_INVALID",
        )
        if region_index != expected_index:
            raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
        text = require_scalar_text(
            region["text"],
            maximum=10_000,
            stage="VERIFY",
            code="ENGINE_OUTPUT_INVALID",
        )
        regions.append({"region_index": region_index, "text": text, **region})
    return regions


def verify_execute(
    expected_snapshot: object,
    canonical_regions: object,
    verification_config: object,
) -> dict[str, object]:
    try:
        snapshot_sha256, expected_items = _parse_expected_snapshot(expected_snapshot)
        regions = _parse_regions(canonical_regions)
        config = _parse_config(verification_config)

        normalized_regions: list[str] = [normalize_v1(region["text"]) for region in regions]
        eligible_regions = [
            index for index, normalized in enumerate(normalized_regions) if normalized
        ]
        normalized_scalar_count = sum(map(len, normalized_regions))
        evaluable: list[tuple[int, str, str]] = []
        output_items: list[dict[str, Any] | None] = [None] * len(expected_items)
        for item_index, item in enumerate(expected_items):
            expected_text = item["expected_text"]
            base = {
                "expected_position": item["position"],
                "string_key_id": item["string_key_id"],
                "string_id": item["string_id"],
                "entry_id": item["entry_id"],
                "expected_text": expected_text,
                "translation_status": item["translation_status"],
            }
            if item["translation_status"] == "missing":
                output_items[item_index] = {
                    **base,
                    "normalized_expected": None,
                    "region_index": None,
                    "observed_text": None,
                    "normalized_observed": None,
                    "match_method": None,
                    "match_score": None,
                    "score_numerator": None,
                    "score_denominator": None,
                    "verification_status": "UNVERIFIED",
                    "reason": "MISSING_TRANSLATION",
                }
                continue
            if expected_text == "":
                output_items[item_index] = {
                    **base,
                    "normalized_expected": "",
                    "region_index": None,
                    "observed_text": None,
                    "normalized_observed": None,
                    "match_method": None,
                    "match_score": None,
                    "score_numerator": None,
                    "score_denominator": None,
                    "verification_status": "UNVERIFIED",
                    "reason": "EMPTY_EXPECTED",
                }
                continue
            normalized = normalize_v1(expected_text)
            normalized_scalar_count += len(normalized)
            if not normalized:
                output_items[item_index] = {
                    **base,
                    "normalized_expected": "",
                    "region_index": None,
                    "observed_text": None,
                    "normalized_observed": None,
                    "match_method": None,
                    "match_score": None,
                    "score_numerator": None,
                    "score_denominator": None,
                    "verification_status": "UNVERIFIED",
                    "reason": "NORMALIZED_EMPTY_EXPECTED",
                }
                continue
            evaluable.append((item_index, expected_text, normalized))

        if normalized_scalar_count > MAX_NORMALIZED_SCALARS:
            raise AdapterError("RESULT_LIMIT_EXCEEDED", "VERIFY")
        pair_count = len(evaluable) * len(eligible_regions)
        if pair_count > MAX_REAL_PAIRS:
            raise AdapterError("RESULT_LIMIT_EXCEEDED", "VERIFY")

        candidates: list[CandidateEdge] = []
        distance_work = 0
        for evaluable_index, (_, expected_text, normalized_expected) in enumerate(evaluable):
            for region_index in eligible_regions:
                region_text = regions[region_index]["text"]
                normalized_observed = normalized_regions[region_index]
                if expected_text == region_text:
                    method = "EXACT"
                    numerator, denominator = 100, 1
                elif normalized_expected == normalized_observed:
                    method = "NORMALIZED"
                    numerator, denominator = 100, 1
                else:
                    distance_work += len(normalized_expected) * len(normalized_observed)
                    if distance_work > MAX_DISTANCE_WORK:
                        raise AdapterError("RESULT_LIMIT_EXCEEDED", "VERIFY")
                    method = "FUZZY"
                    numerator, denominator = score_ratio(
                        normalized_expected,
                        normalized_observed,
                    )
                if numerator <= 0:
                    continue
                if _at_least(
                    numerator,
                    denominator,
                    config["review_numerator"],
                    config["review_denominator"],
                ):
                    candidates.append(
                        CandidateEdge(
                            evaluable_index,
                            region_index,
                            method,
                            numerator,
                            denominator,
                        )
                    )

        assigned = assign_candidates(len(evaluable), len(regions), candidates)
        assigned_regions: set[int] = set()
        for evaluable_index, (item_index, expected_text, normalized_expected) in enumerate(
            evaluable
        ):
            item = expected_items[item_index]
            edge = assigned.get(evaluable_index)
            base = {
                "expected_position": item["position"],
                "string_key_id": item["string_key_id"],
                "string_id": item["string_id"],
                "entry_id": item["entry_id"],
                "expected_text": expected_text,
                "normalized_expected": normalized_expected,
                "translation_status": item["translation_status"],
            }
            if edge is None:
                output_items[item_index] = {
                    **base,
                    "region_index": None,
                    "observed_text": None,
                    "normalized_observed": None,
                    "match_method": "NONE",
                    "match_score": 0.0,
                    "score_numerator": 0,
                    "score_denominator": 1,
                    "verification_status": "FAIL",
                    "reason": "NO_MATCH",
                }
                continue
            assigned_regions.add(edge.region_index)
            region = regions[edge.region_index]
            if edge.method in ("EXACT", "NORMALIZED"):
                status = "PASS"
            elif _at_least(
                edge.score_numerator,
                edge.score_denominator,
                config["pass_numerator"],
                config["pass_denominator"],
            ):
                status = "PASS"
            else:
                status = "REVIEW"
            output_items[item_index] = {
                **base,
                "region_index": edge.region_index,
                "observed_text": region["text"],
                "normalized_observed": normalized_regions[edge.region_index],
                "match_method": edge.method,
                "match_score": _display_score(
                    edge.score_numerator,
                    edge.score_denominator,
                ),
                "score_numerator": edge.score_numerator,
                "score_denominator": edge.score_denominator,
                "verification_status": status,
                "reason": "MATCHED",
            }

        completed_items = [item for item in output_items if item is not None]
        if len(completed_items) != len(expected_items):
            raise AdapterError("ENGINE_OUTPUT_INVALID", "VERIFY")
        counts = {
            name: sum(
                item["verification_status"] == name for item in completed_items
            )
            for name in ("PASS", "REVIEW", "FAIL", "UNVERIFIED")
        }
        evaluated_count = counts["PASS"] + counts["REVIEW"] + counts["FAIL"]
        if counts["FAIL"]:
            aggregate = "FAIL"
        elif counts["REVIEW"]:
            aggregate = "REVIEW"
        elif counts["UNVERIFIED"] or evaluated_count == 0:
            aggregate = "UNVERIFIED"
        else:
            aggregate = "PASS"
        if not expected_items:
            evaluation_reason = "NO_EXPECTATIONS"
        elif evaluated_count == 0:
            evaluation_reason = "NO_EVALUABLE_EXPECTATIONS"
        elif counts["UNVERIFIED"]:
            evaluation_reason = "PARTIAL_UNVERIFIED"
        else:
            evaluation_reason = "EVALUATED"

        return {
            "adapter_version": ADAPTER_VERSION,
            "snapshot_sha256": snapshot_sha256,
            "configuration_sha256": config["configuration_sha256"],
            "matching_version": MATCHING_VERSION,
            "normalization_version": NORMALIZATION_VERSION,
            "items": completed_items,
            "summary": {
                "verification_status": aggregate,
                "evaluation_reason": evaluation_reason,
                "incomplete": counts["UNVERIFIED"] > 0,
                "total_count": len(completed_items),
                "evaluated_count": evaluated_count,
                "unverified_count": counts["UNVERIFIED"],
                "pass_count": counts["PASS"],
                "review_count": counts["REVIEW"],
                "fail_count": counts["FAIL"],
                "unmatched_region_count": len(regions) - len(assigned_regions),
                "pass_threshold": float(config["pass_threshold"]),
                "review_threshold": float(config["review_threshold"]),
            },
        }
    except AdapterError:
        raise
    except Exception as error:
        raise AdapterError("ENGINE_INTERNAL_ERROR", "VERIFY") from error
