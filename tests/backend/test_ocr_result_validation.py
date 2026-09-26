"""Closed result validation before Backend publishes immutable OCR results."""

import hashlib
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
import rfc8785

from backend.app.services.ocr_types import JobInvariantError
from backend.app.services.verification_results import write_adapter_results
from worker.ocr import load_fixture_profile_document


class _Scalars:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class _Session:
    def __init__(self, expected=()):
        self.expected = list(expected)
        self.added = []

    def add(self, row):
        self.added.append(row)

    def flush(self):
        pass

    def scalars(self, _statement):
        return _Scalars(self.expected)


def _run():
    document = load_fixture_profile_document("fixture-contract-v1")
    profile = document.manifest
    profile_bytes = document.canonical_bytes
    return {
        "id": uuid4(),
        "project_id": uuid4(),
        "screenshot_id": uuid4(),
        "screenshot_file_hash": "a" * 64,
        "screenshot_width": 12,
        "screenshot_height": 8,
        "profile_id": document.profile_id,
        "profile_digest": hashlib.sha256(profile_bytes).hexdigest(),
        "profile_canonical": profile_bytes,
        "locale_code": "en-US",
        "ocr_language": "en",
        "snapshot_sha256": "b" * 64,
        "configuration_sha256": "c" * 64,
        "matching_version": "one-to-one-levenshtein-v1",
        "normalization_version": "norm-v1",
        "pass_threshold": Decimal("95"),
        "review_threshold": Decimal("85"),
    }


def _refresh_runtime_digest(output):
    runtime = output["ocr"]["runtime_manifest"]
    digest_input = {key: value for key, value in runtime.items() if key != "runtime_manifest_sha256"}
    runtime["runtime_manifest_sha256"] = hashlib.sha256(rfc8785.dumps(digest_input)).hexdigest()


def _output(run):
    pixel = "d" * 64
    output = {
        "ocr": {
            "adapter_version": 1,
            "source_sha256": run["screenshot_file_hash"],
            "profile_sha256": run["profile_digest"],
            "pixel_sha256": pixel,
            "runtime_manifest": {
                "profile_id": run["profile_id"],
                "engine_name": "synthetic-fixture",
                "engine_version": "1",
                "packages": [],
                "native_packages": [],
                "artifacts": [],
                "locale_code": run["locale_code"],
                "ocr_language": run["ocr_language"],
                "detected_language": None,
                "detected_language_reason": "NOT_PROVIDED",
                "os": "test-os",
                "architecture": "test-architecture",
                "python_version": "3.12.14",
                "unicode_version": "15.0.0",
                "rapidfuzz_version": "3.14.6",
                "device": "cpu",
                "thread_count": 1,
                "numeric_mode": "fp32",
                "engine_options": [],
                "determinism_limitations": [],
                "runtime_manifest_sha256": "0" * 64,
            },
            "preprocessing": {
                "exif_policy": "ignored-v1",
                "exif_orientation": None,
                "pixel_sha256": pixel,
                "steps": [{
                    "kind": "identity",
                    "input_width": 12,
                    "input_height": 8,
                    "output_width": 12,
                    "output_height": 8,
                    "matrix3x3": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                }],
                "original_to_inference_matrix3x3": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            },
            "regions": [],
            "raw_audit": {
                "schema_version": 1,
                "regions": [],
                "raw_output_sha256": "f" * 64,
            },
            "timings_ms": {"decode": 0, "inference": 0, "projection": 0, "total": 0},
        },
        "verification": {
            "adapter_version": 1,
            "snapshot_sha256": run["snapshot_sha256"],
            "configuration_sha256": run["configuration_sha256"],
            "matching_version": run["matching_version"],
            "normalization_version": run["normalization_version"],
            "items": [],
            "summary": {
                "verification_status": "UNVERIFIED",
                "evaluation_reason": "NO_EXPECTATIONS",
                "incomplete": False,
                "total_count": 0,
                "evaluated_count": 0,
                "unverified_count": 0,
                "pass_count": 0,
                "review_count": 0,
                "fail_count": 0,
                "unmatched_region_count": 0,
                "pass_threshold": 95,
                "review_threshold": 85,
            },
        },
    }
    _refresh_runtime_digest(output)
    return output


def test_empty_complete_result_is_validated_and_returns_frozen_identities():
    run = _run()
    result = write_adapter_results(_Session(), run, _output(run))

    assert result.snapshot_sha256 == run["snapshot_sha256"]
    assert result.configuration_sha256 == run["configuration_sha256"]
    assert result.profile_digest == run["profile_digest"]
    assert result.verification_status == "UNVERIFIED"


def test_summary_cannot_contradict_item_derived_aggregate():
    run = _run()
    output = _output(run)
    output["verification"]["summary"].update(
        verification_status="PASS",
        evaluation_reason="EVALUATED",
        total_count=1,
        evaluated_count=1,
        pass_count=1,
    )

    with pytest.raises(JobInvariantError, match="summary does not match"):
        write_adapter_results(_Session(), run, output)


def test_region_confidence_semantics_is_required_and_exact():
    run = _run()
    output = _output(run)
    output["ocr"]["regions"] = [{
        "region_index": 0,
        "engine_region_index": 0,
        "text": "text",
        "confidence": 0.75,
        "confidence_semantics": "detection",
        "detection_confidence": None,
        "detection_confidence_unavailable_reason": "NOT_EXPOSED_BY_PROFILE",
        "polygon": [[0.25, 0.25], [4.75, 0.25], [4.75, 2.5], [0.25, 2.5]],
        "bbox": {"x": 0.25, "y": 0.25, "width": 4.5, "height": 2.25},
        "clipped": False,
    }]
    output["verification"]["summary"]["unmatched_region_count"] = 1

    with pytest.raises(JobInvariantError, match="confidence semantics"):
        write_adapter_results(_Session(), run, output)


def test_nonempty_raw_audit_retains_private_engine_text_and_geometry():
    run = _run()
    output = _output(run)
    output["ocr"]["regions"] = [{
        "region_index": 0,
        "engine_region_index": 7,
        "text": "raw engine text",
        "confidence": 0.75,
        "confidence_semantics": "recognition",
        "detection_confidence": None,
        "detection_confidence_unavailable_reason": "NOT_EXPOSED_BY_PROFILE",
        "polygon": [[0.25, 0.25], [4.75, 0.25], [4.75, 2.5], [0.25, 2.5]],
        "bbox": {"x": 0.25, "y": 0.25, "width": 4.5, "height": 2.25},
        "clipped": False,
    }]
    output["ocr"]["raw_audit"]["regions"] = [{
        "engine_region_index": 7,
        "engine_polygon": [[0.25, 0.25], [4.75, 0.25], [4.75, 2.5], [0.25, 2.5]],
        "transformed_preclip_polygon": [[0.25, 0.25], [4.75, 0.25], [4.75, 2.5], [0.25, 2.5]],
        "raw_text": "raw engine text",
        "recognition_confidence": 0.75,
        "detection_confidence": None,
    }]
    output["verification"]["summary"]["unmatched_region_count"] = 1
    session = _Session()

    write_adapter_results(session, run, output)

    ocr_result = session.added[0]
    assert ocr_result.raw_audit["regions"][0]["raw_text"] == "raw engine text"


def test_raw_audit_text_obeys_persistable_scalar_limit():
    run = _run()
    output = _output(run)
    output["ocr"]["raw_audit"]["regions"] = [{
        "engine_region_index": 0,
        "engine_polygon": [[0, 0], [1, 0], [1, 1], [0, 1]],
        "transformed_preclip_polygon": [[0, 0], [1, 0], [1, 1], [0, 1]],
        "raw_text": "x" * 10001,
        "recognition_confidence": 0.75,
        "detection_confidence": None,
    }]

    with pytest.raises(JobInvariantError, match="raw audit text"):
        write_adapter_results(_Session(), run, output)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda output: output["ocr"]["runtime_manifest"].update(secret_path="C:/private/model"), "runtime manifest"),
        (lambda output: output["ocr"]["raw_audit"].update(engine_payload={}), "raw OCR audit"),
        (lambda output: output["ocr"]["timings_ms"].update(total=-1), "OCR timing total"),
    ],
)
def test_registered_runtime_audit_and_timing_shapes_are_closed(mutate, message):
    run = _run()
    output = _output(run)
    mutate(output)

    with pytest.raises(JobInvariantError, match=message):
        write_adapter_results(_Session(), run, output)


def test_runtime_facts_must_be_exact_projection_of_frozen_profile():
    run = _run()
    output = _output(run)
    output["ocr"]["runtime_manifest"]["thread_count"] = 2
    _refresh_runtime_digest(output)

    with pytest.raises(JobInvariantError, match="frozen profile"):
        write_adapter_results(_Session(), run, output)


def test_runtime_python_minor_must_match_frozen_profile_exactly():
    run = _run()
    output = _output(run)
    output["ocr"]["runtime_manifest"]["python_version"] = "3.120.0"
    _refresh_runtime_digest(output)

    with pytest.raises(JobInvariantError, match="frozen profile"):
        write_adapter_results(_Session(), run, output)


def test_runtime_package_and_native_package_records_are_preserved_exactly():
    run = _run()
    output = _output(run)
    package = {
        "name": "runtime-wheel",
        "version": "1.2.3",
        "filename": "runtime_wheel-1.2.3-py3-none-any.whl",
        "byte_size": 123,
        "sha256": "1" * 64,
    }
    native_package = {
        "name": "libgomp1",
        "version": "14.2.0-19",
        "architecture": "amd64",
        "copyright_sha256": "2" * 64,
    }
    profile = dict(load_fixture_profile_document("fixture-contract-v1").manifest)
    profile["engine"] = dict(profile["engine"])
    profile["engine"]["packages"] = [package]
    profile["engine"]["native_packages"] = [native_package]
    profile_bytes = rfc8785.dumps(profile)
    run["profile_canonical"] = profile_bytes
    run["profile_digest"] = hashlib.sha256(profile_bytes).hexdigest()
    output["ocr"]["profile_sha256"] = run["profile_digest"]
    output["ocr"]["runtime_manifest"]["packages"] = [package]
    output["ocr"]["runtime_manifest"]["native_packages"] = [native_package]
    _refresh_runtime_digest(output)
    session = _Session()

    write_adapter_results(session, run, output)

    assert session.added[0].runtime_manifest["packages"] == [package]
    assert session.added[0].runtime_manifest["native_packages"] == [native_package]


@pytest.mark.parametrize("key", ["packages", "native_packages"])
def test_runtime_dependency_records_must_match_the_frozen_profile(key):
    run = _run()
    output = _output(run)
    if key == "packages":
        output["ocr"]["runtime_manifest"][key] = [{
            "name": "unexpected",
            "version": "1",
            "filename": "unexpected-1-py3-none-any.whl",
            "byte_size": 1,
            "sha256": "3" * 64,
        }]
    else:
        output["ocr"]["runtime_manifest"][key] = [{
            "name": "unexpected",
            "version": "1",
            "architecture": "amd64",
            "copyright_sha256": "4" * 64,
        }]
    _refresh_runtime_digest(output)

    with pytest.raises(JobInvariantError, match="frozen profile"):
        write_adapter_results(_Session(), run, output)


def test_runtime_manifest_digest_must_cover_the_complete_manifest():
    run = _run()
    output = _output(run)
    output["ocr"]["runtime_manifest"]["architecture"] = "tampered"

    with pytest.raises(JobInvariantError, match="digest does not match"):
        write_adapter_results(_Session(), run, output)


def test_frozen_profile_requires_canonical_bytes_digest_and_versioned_schema():
    run = _run()
    output = _output(run)
    profile = dict(load_fixture_profile_document("fixture-contract-v1").manifest)
    profile["engine"] = dict(profile["engine"])
    del profile["engine"]["native_packages"]
    profile_bytes = rfc8785.dumps(profile)
    run["profile_canonical"] = profile_bytes
    run["profile_digest"] = hashlib.sha256(profile_bytes).hexdigest()
    output["ocr"]["profile_sha256"] = run["profile_digest"]

    with pytest.raises(JobInvariantError, match="Frozen profile manifest is invalid"):
        write_adapter_results(_Session(), run, output)
