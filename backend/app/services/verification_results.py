"""Validate complete adapter output and append one immutable result set."""
from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal, ROUND_HALF_EVEN
from uuid import uuid4

import rfc8785
from sqlalchemy import select

from backend.app.errors import DomainError
from backend.app.models import (
    OCRRegion,
    OCRResult,
    VerificationExpectedItem,
    VerificationItem,
    VerificationResult,
)
from backend.app.services.ocr_types import AdapterOutputInvalid as JobInvariantError, FinalizedResults
from backend.app.validation.unicode import validate_unicode
from worker.ocr import AdapterError
from worker.ocr.schemas import (
    validate_ocr_adapter_output,
    validate_schema_instance,
    validate_verification_adapter_output,
)


MAX_RESULT_BYTES = 8 * 1024 * 1024
MAX_REGIONS = 1000
MAX_REGION_SCALARS = 10000
MAX_REGION_UTF8 = 1024 * 1024
QUALITY = {"PASS", "REVIEW", "FAIL", "UNVERIFIED"}
REASONS = {"MATCHED", "NO_MATCH", "MISSING_TRANSLATION", "EMPTY_EXPECTED", "NORMALIZED_EMPTY_EXPECTED"}
EVALUATION_REASONS = {"EVALUATED", "PARTIAL_UNVERIFIED", "NO_EVALUABLE_EXPECTATIONS", "NO_EXPECTATIONS"}


def _mapping(value, label):
    if not isinstance(value, dict):
        raise JobInvariantError(f"{label} must be an object")
    try:
        validate_unicode(value, label)
    except DomainError as exc:
        raise JobInvariantError(f"{label} contains invalid Unicode") from exc
    return value


def _canonical(value, label):
    try:
        data = rfc8785.dumps(value)
    except (rfc8785.CanonicalizationError, TypeError, ValueError):
        raise JobInvariantError(f"{label} is not canonical JSON") from None
    if len(data) > MAX_RESULT_BYTES:
        raise JobInvariantError("Adapter result exceeds the aggregate limit")
    return data, hashlib.sha256(data).hexdigest()


def _required(value, required, label, optional=()):
    missing = set(required) - set(value)
    unknown = set(value) - set(required) - set(optional)
    if missing or unknown:
        raise JobInvariantError(f"{label} has an invalid closed shape")


def _finite(value, low, high, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise JobInvariantError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result) or not low <= result <= high:
        raise JobInvariantError(f"{label} is outside its range")
    return result


def _geometry(region, width, height):
    polygon = region.get("polygon")
    bbox = region.get("bbox")
    if not isinstance(polygon, list) or not 3 <= len(polygon) <= 8 or not isinstance(bbox, dict):
        raise JobInvariantError("Invalid region geometry")
    points = []
    for point in polygon:
        if not isinstance(point, list) or len(point) != 2:
            raise JobInvariantError("Invalid polygon point")
        x = _finite(point[0], 0, width, "polygon x")
        y = _finite(point[1], 0, height, "polygon y")
        points.append([x, y])
    if set(bbox) != {"x", "y", "width", "height"}:
        raise JobInvariantError("Invalid bbox shape")
    x = _finite(bbox["x"], 0, width, "bbox x")
    y = _finite(bbox["y"], 0, height, "bbox y")
    w = _finite(bbox["width"], 0, width, "bbox width")
    h = _finite(bbox["height"], 0, height, "bbox height")
    if w <= 0 or h <= 0 or x + w > width or y + h > height:
        raise JobInvariantError("Bounding box is outside the original raster")
    return points, (x, y, w, h)


def _decimal_score(value):
    if value is None:
        return None
    number = Decimal(str(value))
    if not number.is_finite() or not Decimal("0") <= number <= Decimal("100"):
        raise JobInvariantError("Invalid match score")
    return number.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)


def _sha256(value, label):
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise JobInvariantError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _matrix(value, label):
    if not isinstance(value, list) or len(value) != 3 or any(not isinstance(row, list) or len(row) != 3 for row in value):
        raise JobInvariantError(f"{label} must be a 3x3 matrix")
    return [[_finite(cell, -float("inf"), float("inf"), label) for cell in row] for row in value]


def _positive_int(value, label, *, allow_zero=False):
    minimum = 0 if allow_zero else 1
    if type(value) is not int or value < minimum:
        raise JobInvariantError(f"{label} must be an integer greater than or equal to {minimum}")
    return value


def _text(value, label, *, nonempty=False):
    if not isinstance(value, str) or (nonempty and not value):
        raise JobInvariantError(f"{label} must be text")
    return value


def _array(value, label, *, maximum=None, minimum=0):
    if not isinstance(value, list) or len(value) < minimum or (maximum is not None and len(value) > maximum):
        raise JobInvariantError(f"{label} must be an array")
    return value


def _name_values(value, label):
    result = _array(value, label)
    for item in result:
        item = _mapping(item, f"{label} item")
        _required(item, {"name", "value"}, f"{label} item")
        _text(item["name"], f"{label} name", nonempty=True)
        scalar = item["value"]
        if isinstance(scalar, (dict, list)) or not isinstance(scalar, (str, int, float, bool, type(None))):
            raise JobInvariantError(f"{label} value must be scalar")
        if isinstance(scalar, float) and not math.isfinite(scalar):
            raise JobInvariantError(f"{label} value must be finite")
    return result


def _runtime_manifest(value):
    runtime = _mapping(value, "runtime manifest")
    _required(runtime, {
        "profile_id", "engine_name", "engine_version", "packages", "native_packages", "artifacts",
        "locale_code", "ocr_language", "detected_language", "detected_language_reason",
        "os", "architecture", "python_version", "unicode_version", "rapidfuzz_version",
        "device", "thread_count", "numeric_mode", "engine_options",
        "determinism_limitations", "runtime_manifest_sha256",
    }, "runtime manifest")
    for key in (
        "profile_id", "engine_name", "engine_version", "locale_code", "ocr_language",
        "os", "architecture", "python_version",
    ):
        _text(runtime[key], f"runtime {key}", nonempty=True)
    if runtime["detected_language"] is not None or runtime["detected_language_reason"] != "NOT_PROVIDED":
        raise JobInvariantError("Invalid detected-language runtime facts")
    if runtime["unicode_version"] != "15.0.0" or runtime["rapidfuzz_version"] != "3.14.6":
        raise JobInvariantError("Invalid runtime text versions")
    if runtime["device"] != "cpu" or runtime["numeric_mode"] != "fp32":
        raise JobInvariantError("Invalid runtime execution policy")
    _positive_int(runtime["thread_count"], "runtime thread count")
    for package in _array(runtime["packages"], "runtime packages"):
        package = _mapping(package, "runtime package")
        _required(package, {"name", "version", "filename", "byte_size", "sha256"}, "runtime package")
        for key in ("name", "version", "filename"):
            _text(package[key], f"runtime package {key}", nonempty=True)
        _positive_int(package["byte_size"], "runtime package byte size")
        _sha256(package["sha256"], "runtime package digest")
    for package in _array(runtime["native_packages"], "runtime native packages"):
        package = _mapping(package, "runtime native package")
        _required(
            package,
            {"name", "version", "architecture", "copyright_sha256"},
            "runtime native package",
        )
        for key in ("name", "version", "architecture"):
            _text(package[key], f"runtime native package {key}", nonempty=True)
        _sha256(package["copyright_sha256"], "runtime native package copyright digest")
    for artifact in _array(runtime["artifacts"], "runtime artifacts"):
        artifact = _mapping(artifact, "runtime artifact")
        _required(artifact, {
            "name", "revision", "kind", "byte_size", "sha256", "license_identifier",
        }, "runtime artifact")
        for key in ("name", "revision", "kind", "license_identifier"):
            _text(artifact[key], f"runtime artifact {key}", nonempty=True)
        _positive_int(artifact["byte_size"], "runtime artifact byte size")
        _sha256(artifact["sha256"], "runtime artifact digest")
    _name_values(runtime["engine_options"], "runtime engine options")
    for limitation in _array(runtime["determinism_limitations"], "runtime determinism limitations"):
        _text(limitation, "runtime determinism limitation")
    declared_digest = _sha256(runtime["runtime_manifest_sha256"], "runtime manifest digest")
    digest_input = dict(runtime)
    del digest_input["runtime_manifest_sha256"]
    try:
        actual_digest = hashlib.sha256(rfc8785.dumps(digest_input)).hexdigest()
    except (rfc8785.CanonicalizationError, TypeError, ValueError):
        raise JobInvariantError("Runtime manifest cannot be canonicalized") from None
    if declared_digest != actual_digest:
        raise JobInvariantError("Runtime manifest digest does not match its content")
    return runtime


def _audit_polygon(value, label):
    points = _array(value, label, minimum=4, maximum=4)
    for point in points:
        if not isinstance(point, list) or len(point) != 2:
            raise JobInvariantError(f"{label} contains an invalid point")
        _finite(point[0], -float("inf"), float("inf"), label)
        _finite(point[1], -float("inf"), float("inf"), label)


def _raw_audit(value):
    audit = _mapping(value, "raw OCR audit")
    _required(audit, {"schema_version", "regions", "raw_output_sha256"}, "raw OCR audit")
    if audit["schema_version"] != 1:
        raise JobInvariantError("Invalid raw OCR audit version")
    _sha256(audit["raw_output_sha256"], "raw output digest")
    for region in _array(audit["regions"], "raw audit regions", maximum=MAX_REGIONS):
        region = _mapping(region, "raw audit region")
        _required(region, {
            "engine_region_index", "engine_polygon", "transformed_preclip_polygon",
            "raw_text", "recognition_confidence", "detection_confidence",
        }, "raw audit region")
        _positive_int(region["engine_region_index"], "raw audit engine region index", allow_zero=True)
        raw_text = _text(region["raw_text"], "raw audit text")
        if len(raw_text) > MAX_REGION_SCALARS:
            raise JobInvariantError("Invalid raw audit text")
        _audit_polygon(region["engine_polygon"], "raw engine polygon")
        _audit_polygon(region["transformed_preclip_polygon"], "raw transformed polygon")
        _finite(region["recognition_confidence"], 0, 1, "raw recognition confidence")
        if region["detection_confidence"] is not None:
            _finite(region["detection_confidence"], 0, 1, "raw detection confidence")
    return audit


def _timings(value):
    timings = _mapping(value, "OCR timings")
    _required(timings, {"decode", "inference", "projection", "total"}, "OCR timings")
    for key in timings:
        _finite(timings[key], 0, float("inf"), f"OCR timing {key}")
    return timings


def _validate_preprocessing(value, pixel_sha256):
    preprocessing = _mapping(value, "preprocessing")
    _required(preprocessing, {
        "exif_policy", "exif_orientation", "pixel_sha256", "steps",
        "original_to_inference_matrix3x3",
    }, "preprocessing")
    if preprocessing["exif_policy"] != "ignored-v1":
        raise JobInvariantError("Invalid EXIF policy")
    orientation = preprocessing["exif_orientation"]
    if orientation is not None and (type(orientation) is not int or not 1 <= orientation <= 8):
        raise JobInvariantError("Invalid EXIF orientation")
    if _sha256(preprocessing["pixel_sha256"], "preprocessing pixel digest") != pixel_sha256:
        raise JobInvariantError("Preprocessing pixel digest changed")
    _matrix(preprocessing["original_to_inference_matrix3x3"], "original-to-inference matrix")
    steps = preprocessing["steps"]
    if not isinstance(steps, list) or not steps:
        raise JobInvariantError("Preprocessing steps must be an array")
    for step in steps:
        step = _mapping(step, "preprocessing step")
        _required(step, {
            "kind", "input_width", "input_height", "output_width", "output_height", "matrix3x3",
        }, "preprocessing step")
        if not isinstance(step["kind"], str) or not step["kind"]:
            raise JobInvariantError("Preprocessing step kind is invalid")
        for key in ("input_width", "input_height", "output_width", "output_height"):
            _positive_int(step[key], f"preprocessing {key}")
        _matrix(step["matrix3x3"], "preprocessing matrix")
    return preprocessing


def _normalizer():
    try:
        from worker.verification.normalization import normalize_v1
    except (ImportError, ModuleNotFoundError) as exc:
        raise JobInvariantError("Verification normalizer is unavailable") from exc
    return normalize_v1


def _normalize(normalize_v1, value, label):
    if not isinstance(value, str):
        raise JobInvariantError(f"{label} must be text")
    try:
        return normalize_v1(value)
    except Exception as exc:
        raise JobInvariantError(f"{label} cannot be normalized") from exc


def _profile_manifest(run):
    try:
        canonical = bytes(run["profile_canonical"])
        if hashlib.sha256(canonical).hexdigest() != run["profile_digest"]:
            raise ValueError
        manifest = json.loads(canonical)
        if not isinstance(manifest, dict) or rfc8785.dumps(manifest) != canonical:
            raise ValueError
        validate_schema_instance("profile-manifest", manifest, stage="OCR")
    except (
        AdapterError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        rfc8785.CanonicalizationError,
    ):
        raise JobInvariantError("Frozen profile manifest is invalid") from None
    return manifest


def _profile_runtime(run):
    manifest = _profile_manifest(run)
    runtime = manifest.get("runtime") if isinstance(manifest.get("runtime"), dict) else {}
    engine = manifest.get("engine") if isinstance(manifest.get("engine"), dict) else {}
    return (
        manifest.get("engine_name", runtime.get("engine_name", engine.get("name"))),
        manifest.get("engine_version", runtime.get("engine_version", engine.get("version"))),
    )


def _python_major_minor(value):
    if not isinstance(value, str):
        return None
    parts = value.split(".")
    if len(parts) < 2 or not all(part.isdigit() for part in parts[:2]):
        return None
    return tuple(int(part) for part in parts[:2])


def _derived_summary(items, region_count, assigned_count):
    counts = {name: sum(item["verification_status"] == name for item in items) for name in QUALITY}
    evaluated = counts["PASS"] + counts["REVIEW"] + counts["FAIL"]
    if counts["FAIL"]:
        status = "FAIL"
    elif counts["REVIEW"]:
        status = "REVIEW"
    elif counts["UNVERIFIED"] or evaluated == 0:
        status = "UNVERIFIED"
    else:
        status = "PASS"
    if not items:
        reason = "NO_EXPECTATIONS"
    elif evaluated == 0:
        reason = "NO_EVALUABLE_EXPECTATIONS"
    elif counts["UNVERIFIED"]:
        reason = "PARTIAL_UNVERIFIED"
    else:
        reason = "EVALUATED"
    return {
        "verification_status": status,
        "evaluation_reason": reason,
        "incomplete": counts["UNVERIFIED"] > 0,
        "total_count": len(items),
        "evaluated_count": evaluated,
        "unverified_count": counts["UNVERIFIED"],
        "pass_count": counts["PASS"],
        "review_count": counts["REVIEW"],
        "fail_count": counts["FAIL"],
        "unmatched_region_count": region_count - assigned_count,
    }


def write_adapter_results(session, run, output):
    bundle = _mapping(output, "adapter output")
    _required(bundle, {"ocr", "verification"}, "adapter output")
    ocr = _mapping(bundle["ocr"], "OCR adapter output")
    verification = _mapping(bundle["verification"], "verification adapter output")
    _canonical(bundle, "adapter output")

    try:
        validate_ocr_adapter_output(ocr)
        validate_verification_adapter_output(verification)
    except AdapterError as exc:
        raise JobInvariantError("Adapter output does not match the registered versioned schema") from exc

    _required(ocr, {
        "adapter_version", "source_sha256", "profile_sha256", "pixel_sha256",
        "runtime_manifest", "preprocessing", "regions", "raw_audit", "timings_ms",
    }, "OCR adapter output")
    if type(ocr["adapter_version"]) is not int or ocr["adapter_version"] != 1 or ocr["source_sha256"] != run["screenshot_file_hash"]:
        raise JobInvariantError("OCR output does not identify the source")
    if ocr["profile_sha256"] != run["profile_digest"]:
        raise JobInvariantError("OCR output does not identify the profile")
    regions = ocr["regions"]
    if not isinstance(regions, list) or len(regions) > MAX_REGIONS:
        raise JobInvariantError("Invalid OCR region count")
    runtime = _runtime_manifest(ocr["runtime_manifest"])
    preprocessing = _validate_preprocessing(ocr["preprocessing"], _sha256(ocr["pixel_sha256"], "pixel digest"))
    raw_audit = _raw_audit(ocr["raw_audit"])
    timings = _timings(ocr["timings_ms"])
    _, raw_hash = _canonical(raw_audit, "raw OCR audit")
    _, output_hash = _canonical(ocr, "OCR adapter output")
    if sum(len(str(region.get("text", "")).encode("utf-8")) for region in regions) > MAX_REGION_UTF8:
        raise JobInvariantError("OCR text exceeds the aggregate limit")

    pixel_sha256 = _sha256(ocr["pixel_sha256"], "pixel digest")
    expected_engine_name, expected_engine_version = _profile_runtime(run)
    profile_manifest = _profile_manifest(run)
    profile_engine = profile_manifest.get("engine")
    profile_policy = profile_manifest.get("runtime_policy")
    expected_artifacts = [
        {key: artifact[key] for key in ("name", "revision", "kind", "byte_size", "sha256", "license_identifier")}
        for artifact in profile_manifest.get("artifacts", [])
    ] if isinstance(profile_manifest.get("artifacts"), list) else None
    if (runtime["profile_id"] != run["profile_id"]
            or runtime["engine_name"] != expected_engine_name
            or runtime["engine_version"] != expected_engine_version
            or runtime["locale_code"] != run["locale_code"]
            or runtime["ocr_language"] != run["ocr_language"]
            or not isinstance(profile_engine, dict)
            or runtime["packages"] != profile_engine.get("packages")
            or runtime["native_packages"] != profile_engine.get("native_packages")
            or expected_artifacts is None
            or runtime["artifacts"] != expected_artifacts
            or runtime["engine_options"] != profile_manifest.get("engine_options")
            or runtime["unicode_version"] != profile_manifest.get("unicode_version")
            or runtime["rapidfuzz_version"] != profile_manifest.get("rapidfuzz_version")
            or not isinstance(profile_policy, dict)
            or runtime["device"] != profile_policy.get("device")
            or runtime["thread_count"] != profile_policy.get("thread_count")
            or runtime["numeric_mode"] != profile_policy.get("numeric_mode")
            or _python_major_minor(runtime["python_version"])
            != _python_major_minor(profile_policy.get("python"))):
        raise JobInvariantError("OCR runtime does not match the frozen profile")
    normalize_v1 = _normalizer()
    result_id = uuid4()
    ocr_row = OCRResult(
        id=result_id, project_id=run["project_id"], run_id=run["id"],
        screenshot_id=run["screenshot_id"], coordinate_space="original-raster-v1",
        width=run["screenshot_width"], height=run["screenshot_height"],
        region_count=len(regions),
        no_text=not any(_normalize(normalize_v1, region.get("text"), "OCR region text") for region in regions),
        profile_id=run["profile_id"], profile_digest=run["profile_digest"],
        engine_name=runtime.get("engine_name", "unknown"),
        engine_version=runtime.get("engine_version", "unknown"),
        ocr_language=run["ocr_language"], source_sha256=ocr["source_sha256"],
        pixel_sha256=pixel_sha256, runtime_manifest=runtime,
        preprocessing=preprocessing, raw_audit=raw_audit,
        raw_audit_sha256=raw_hash, timings_ms=timings,
        output_sha256=output_hash,
    )
    session.add(ocr_row)
    session.flush()

    seen_regions = set()
    for expected_index, region in enumerate(regions):
        _required(region, {
            "region_index", "engine_region_index", "text", "confidence",
            "confidence_semantics",
            "detection_confidence", "detection_confidence_unavailable_reason",
            "polygon", "bbox", "clipped",
        }, "OCR region")
        index = region["region_index"]
        if type(index) is not int or index != expected_index or index in seen_regions:
            raise JobInvariantError("OCR regions are not in canonical contiguous order")
        seen_regions.add(index)
        raw_text = region["text"]
        if not isinstance(raw_text, str) or len(raw_text) > MAX_REGION_SCALARS:
            raise JobInvariantError("Invalid OCR region text")
        confidence = _finite(region["confidence"], 0, 1, "recognition confidence")
        if region["confidence_semantics"] != "recognition":
            raise JobInvariantError("Invalid recognition confidence semantics")
        detection = region["detection_confidence"]
        unavailable = region["detection_confidence_unavailable_reason"]
        if detection is None:
            if unavailable != "NOT_EXPOSED_BY_PROFILE":
                raise JobInvariantError("Missing detection confidence reason")
        else:
            detection = _finite(detection, 0, 1, "detection confidence")
            if unavailable is not None:
                raise JobInvariantError("Detection confidence reason must be null")
        polygon, bbox = _geometry(region, run["screenshot_width"], run["screenshot_height"])
        engine_index = region["engine_region_index"]
        if type(engine_index) is not int or engine_index < 0:
            raise JobInvariantError("Invalid engine region index")
        if type(region["clipped"]) is not bool:
            raise JobInvariantError("Invalid clipped flag")
        session.add(OCRRegion(
            project_id=run["project_id"], run_id=run["id"], result_id=result_id,
            region_index=index, engine_region_index=engine_index, raw_text=raw_text,
            confidence=confidence, confidence_semantics="recognition",
            detection_confidence=detection,
            detection_confidence_unavailable_reason=unavailable,
            polygon=polygon, bbox_x=bbox[0], bbox_y=bbox[1], bbox_width=bbox[2], bbox_height=bbox[3],
            source_width=run["screenshot_width"], source_height=run["screenshot_height"],
            clipped=region["clipped"],
        ))
    session.flush()

    _required(verification, {
        "adapter_version", "snapshot_sha256", "configuration_sha256",
        "matching_version", "normalization_version", "items", "summary",
    }, "verification adapter output")
    if (type(verification["adapter_version"]) is not int or verification["adapter_version"] != 1
            or verification["snapshot_sha256"] != run["snapshot_sha256"]
            or verification["configuration_sha256"] != run["configuration_sha256"]
            or verification["matching_version"] != run["matching_version"]
            or verification["normalization_version"] != run["normalization_version"]):
        raise JobInvariantError("Verification output does not identify frozen inputs")
    items = verification["items"]
    summary = _mapping(verification["summary"], "verification summary")
    if not isinstance(items, list):
        raise JobInvariantError("Verification items must be an array")
    expected_rows = session.scalars(select(VerificationExpectedItem).where(
        VerificationExpectedItem.project_id == run["project_id"],
        VerificationExpectedItem.run_id == run["id"],
    ).order_by(VerificationExpectedItem.position)).all()
    if len(items) != len(expected_rows):
        raise JobInvariantError("Verification output must cover every expected item")
    _required(summary, {
        "verification_status", "evaluation_reason", "incomplete", "total_count",
        "evaluated_count", "unverified_count", "pass_count", "review_count",
        "fail_count", "unmatched_region_count", "pass_threshold", "review_threshold",
    }, "verification summary")
    if summary["verification_status"] not in QUALITY or summary["evaluation_reason"] not in EVALUATION_REASONS:
        raise JobInvariantError("Invalid aggregate quality")
    try:
        pass_threshold = Decimal(str(summary["pass_threshold"]))
        review_threshold = Decimal(str(summary["review_threshold"]))
    except Exception:
        raise JobInvariantError("Invalid verification thresholds") from None
    if not pass_threshold.is_finite() or not review_threshold.is_finite() or pass_threshold != run["pass_threshold"] or review_threshold != run["review_threshold"]:
        raise JobInvariantError("Verification thresholds changed")
    verification_id = uuid4()
    result_row = VerificationResult(
        id=verification_id, project_id=run["project_id"], run_id=run["id"],
        screenshot_id=run["screenshot_id"], ocr_result_id=result_id,
        snapshot_sha256=run["snapshot_sha256"], configuration_sha256=run["configuration_sha256"],
        matching_version=run["matching_version"], normalization_version=run["normalization_version"],
        **summary,
    )
    session.add(result_row)
    session.flush()

    assigned = set()
    validated_items = []
    region_text = {region["region_index"]: region["text"] for region in regions}
    for expected, item in zip(expected_rows, items, strict=True):
        item = _mapping(item, "verification item")
        _required(item, {
            "expected_position", "string_key_id", "string_id", "entry_id", "expected_text",
            "normalized_expected", "translation_status", "region_index", "observed_text",
            "normalized_observed", "match_method", "match_score", "score_numerator",
            "score_denominator", "verification_status", "reason",
        }, "verification item")
        if (item["expected_position"] != expected.position
                or str(item["string_key_id"]) != str(expected.string_key_id)
                or item["string_id"] != expected.string_id
                or (str(item["entry_id"]) if item["entry_id"] else None) != (str(expected.entry_id) if expected.entry_id else None)
                or item["expected_text"] != expected.expected_text
                or item["translation_status"] != expected.translation_status):
            raise JobInvariantError("Verification item changed the expected snapshot")
        if item["verification_status"] not in QUALITY or item["reason"] not in REASONS:
            raise JobInvariantError("Invalid verification item status")
        region_index = item["region_index"]
        if region_index is not None:
            if type(region_index) is not int or region_index not in seen_regions or region_index in assigned:
                raise JobInvariantError("Verification assignment is not one-to-one")
            assigned.add(region_index)
            if item["observed_text"] != region_text[region_index] or item["normalized_observed"] != _normalize(normalize_v1, region_text[region_index], "OCR region text"):
                raise JobInvariantError("Verification item changed the assigned OCR region")
        expected_normalized = None if expected.expected_text is None else _normalize(normalize_v1, expected.expected_text, "expected text")
        if item["normalized_expected"] != expected_normalized:
            raise JobInvariantError("Verification item changed normalized expected text")
        validated_items.append(item)
        session.add(VerificationItem(
            project_id=run["project_id"], run_id=run["id"],
            verification_result_id=verification_id, ocr_result_id=result_id,
            expected_position=expected.position, string_key_id=expected.string_key_id,
            string_id=expected.string_id, entry_id=expected.entry_id,
            expected_text=expected.expected_text, normalized_expected=item["normalized_expected"],
            translation_status=expected.translation_status, region_index=region_index,
            observed_text=item["observed_text"], normalized_observed=item["normalized_observed"],
            match_method=item["match_method"], match_score=_decimal_score(item["match_score"]),
            score_numerator=item["score_numerator"], score_denominator=item["score_denominator"],
            verification_status=item["verification_status"], reason=item["reason"],
        ))
    session.flush()
    derived = _derived_summary(validated_items, len(regions), len(assigned))
    if any(summary[key] != value for key, value in derived.items()):
        raise JobInvariantError("Verification summary does not match its items")
    return FinalizedResults(
        ocr_result_id=result_id,
        verification_result_id=verification_id,
        verification_status=summary["verification_status"],
        snapshot_sha256=run["snapshot_sha256"],
        configuration_sha256=run["configuration_sha256"],
        profile_digest=run["profile_digest"],
    )
