from __future__ import annotations

import platform
import unittest

from worker.ocr import AdapterError, canonicalize_regions, invert_matrix3, transform_point
from worker.ocr.schemas import (
    SCHEMA_NAMES,
    load_schema,
    validate_schema_instance,
    validate_ocr_adapter_output,
    validate_verification_adapter_output,
)


class GeometryTests(unittest.TestCase):
    def test_resize_padding_contract_example(self) -> None:
        regions, audit = canonicalize_regions(
            [
                {
                    "engine_region_index": 7,
                    "text": "Play",
                    "confidence": 0.75,
                    "detection_confidence": None,
                    "polygon": [[60, 70], [160, 70], [160, 95], [60, 95]],
                }
            ],
            width=800,
            height=600,
            original_to_inference_matrix3x3=[[0.5, 0, 10], [0, 0.5, 20], [0, 0, 1]],
        )
        self.assertEqual(regions[0]["polygon"], [[100.0, 100.0], [300.0, 100.0], [300.0, 150.0], [100.0, 150.0]])
        self.assertEqual(regions[0]["bbox"], {"x": 100, "y": 100, "width": 200, "height": 50})
        self.assertFalse(regions[0]["clipped"])
        self.assertEqual(audit[0]["engine_region_index"], 7)
        self.assertEqual(audit[0]["raw_text"], "Play")

    def test_geometric_clipping_not_vertex_clamping(self) -> None:
        regions, _ = canonicalize_regions(
            [
                {
                    "engine_region_index": 0,
                    "text": "edge",
                    "confidence": 0.0,
                    "detection_confidence": 1.0,
                    "polygon": [[-10, 10], [30, -10], [50, 30], [10, 50]],
                }
            ],
            width=40,
            height=40,
            original_to_inference_matrix3x3=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        )
        self.assertTrue(regions[0]["clipped"])
        self.assertGreaterEqual(len(regions[0]["polygon"]), 4)
        self.assertEqual(regions[0]["bbox"], {"x": 0, "y": 0, "width": 40, "height": 40})

    def test_rotation_inverse(self) -> None:
        matrix = [[0, -1, 600], [1, 0, 0], [0, 0, 1]]
        inverse = invert_matrix3(matrix)
        self.assertEqual(transform_point(inverse, (450, 100)), (100.0, 150.0))
        self.assertEqual(transform_point(inverse, (500, 300)), (300.0, 100.0))

    def test_singular_transform_fails_closed(self) -> None:
        with self.assertRaises(AdapterError) as raised:
            invert_matrix3([[1, 0, 0], [0, 0, 0], [0, 0, 1]])
        self.assertEqual(raised.exception.code, "ENGINE_OUTPUT_INVALID")


class SchemaProfileTests(unittest.TestCase):
    def test_locale_lookup_is_case_insensitive_and_normalizes_underscore(self) -> None:
        from worker.ocr.paddle_engine import _validate_locale
        from worker.ocr.profiles import iter_profile_documents

        unified = next(
            document
            for document in iter_profile_documents()
            if "unified" in document.profile_id and document.availability == "AVAILABLE"
        )
        _validate_locale(unified.manifest, {"locale_code": "EN_gb", "ocr_language": "en"})
        with self.assertRaises(AdapterError) as raised:
            _validate_locale(
                unified.manifest,
                {"locale_code": "zh_SG", "ocr_language": "zh-Hans"},
            )
        self.assertEqual(raised.exception.code, "MODEL_UNAVAILABLE")

    def test_all_closed_schemas_load(self) -> None:
        for name in SCHEMA_NAMES:
            schema = load_schema(name)
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            if schema.get("type") == "object":
                self.assertFalse(schema["additionalProperties"])

    def test_production_and_fixture_registries_are_separate(self) -> None:
        from worker.ocr.profiles import (
            iter_fixture_profile_documents,
            iter_profile_documents,
        )

        production = iter_profile_documents()
        self.assertEqual(len(production), 4)
        available = [document for document in production if document.availability == "AVAILABLE"]
        unavailable = [document for document in production if document.availability == "UNAVAILABLE"]
        self.assertEqual(len(available), 2)
        self.assertEqual(len(unavailable), 2)
        for document in available:
            options = {item["name"]: item["value"] for item in document.manifest["engine_options"]}
            self.assertEqual(options["platform_system"], platform.system())
            self.assertTrue(document.production_eligible)
        for document in unavailable:
            self.assertEqual(document.unavailable_code, "UNQUALIFIED_RUNTIME")
        fixture = iter_fixture_profile_documents()[0]
        self.assertEqual(fixture.profile_id, "fixture-contract-v1")
        self.assertEqual(fixture.availability, "AVAILABLE")
        self.assertFalse(fixture.production_eligible)
        self.assertIs(
            validate_schema_instance(
                "profile-manifest", fixture.manifest, stage="OCR"
            ),
            fixture.manifest,
        )

    def test_nested_output_schema_is_closed(self) -> None:
        pixel = "d" * 64
        valid = {
            "adapter_version": 1,
            "source_sha256": "a" * 64,
            "profile_sha256": "b" * 64,
            "pixel_sha256": pixel,
            "runtime_manifest": {
                "profile_id": "fixture-contract-v1",
                "engine_name": "synthetic-fixture",
                "engine_version": "1",
                "packages": [],
                "native_packages": [],
                "artifacts": [],
                "locale_code": "en-US",
                "ocr_language": "en",
                "detected_language": None,
                "detected_language_reason": "NOT_PROVIDED",
                "os": "test",
                "architecture": "test",
                "python_version": "3.12.14",
                "unicode_version": "15.0.0",
                "rapidfuzz_version": "3.14.6",
                "device": "cpu",
                "thread_count": 1,
                "numeric_mode": "fp32",
                "engine_options": [],
                "determinism_limitations": [],
                "runtime_manifest_sha256": "e" * 64,
            },
            "preprocessing": {
                "exif_policy": "ignored-v1",
                "exif_orientation": None,
                "pixel_sha256": pixel,
                "steps": [{
                    "kind": "identity",
                    "input_width": 1,
                    "input_height": 1,
                    "output_width": 1,
                    "output_height": 1,
                    "matrix3x3": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                }],
                "original_to_inference_matrix3x3": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            },
            "regions": [],
            "raw_audit": {"schema_version": 1, "regions": [], "raw_output_sha256": "f" * 64},
            "timings_ms": {"decode": 0, "inference": 0, "projection": 0, "total": 0},
        }
        self.assertIs(validate_ocr_adapter_output(valid), valid)
        valid["runtime_manifest"]["unexpected"] = True
        with self.assertRaises(AdapterError):
            validate_schema_instance("ocr-adapter-output", valid, stage="OCR")

    def test_verification_output_schema_rejects_nonfinite_number(self) -> None:
        value = {
            "adapter_version": 1,
            "snapshot_sha256": "a" * 64,
            "configuration_sha256": "b" * 64,
            "matching_version": "one-to-one-levenshtein-v1",
            "normalization_version": "norm-v1",
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
                "pass_threshold": float("nan"),
                "review_threshold": 85,
            },
        }
        with self.assertRaises(AdapterError):
            validate_schema_instance("verification-adapter-output", value, stage="VERIFY")


if __name__ == "__main__":
    unittest.main()
