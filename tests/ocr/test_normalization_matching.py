from __future__ import annotations

import itertools
import random
import unittest

from worker.verification import normalize_v1, verify_execute
from worker.verification.adapter import _at_least
from worker.verification.assignment import CandidateEdge, assign_candidates


def _snapshot(values: list[tuple[str | None, str]]) -> dict[str, object]:
    return {
        "snapshot_version": 1,
        "sha256": "a" * 64,
        "items": [
            {
                "position": index,
                "string_key_id": f"key-{index}",
                "string_id": f"string-{index}",
                "entry_id": None if status == "missing" else f"entry-{index}",
                "expected_text": value,
                "translation_status": status,
            }
            for index, (value, status) in enumerate(values)
        ],
    }


def _region(index: int, text: str) -> dict[str, object]:
    return {
        "region_index": index,
        "text": text,
        "confidence": 0.9,
        "confidence_semantics": "recognition",
        "detection_confidence": None,
        "detection_confidence_unavailable_reason": "NOT_EXPOSED_BY_PROFILE",
        "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]],
        "bbox": {"x": 0, "y": 0, "width": 1, "height": 1},
        "clipped": False,
        "engine_region_index": index,
    }


CONFIG = {
    "configuration_sha256": "b" * 64,
    "pass_threshold": 95,
    "review_threshold": 85,
    "normalization_version": "norm-v1",
    "matching_version": "one-to-one-levenshtein-v1",
}


class NormalizationTests(unittest.TestCase):
    def test_pinned_rapidfuzz_matches_integer_distance_contract(self) -> None:
        try:
            import rapidfuzz
            from rapidfuzz.distance import Levenshtein
        except ImportError:
            self.skipTest("RapidFuzz is not installed in this interpreter")
        self.assertEqual(rapidfuzz.__version__, "3.14.6")
        pairs = [
            ("a" * 20, "a" * 19 + "b"),
            ("한글 검증", "한글 검정"),
            ("日本語テスト", "日本語テキスト"),
            ("简体中文", "簡體中文"),
            ("😀A", "😀B"),
        ]
        for left, right in pairs:
            distance = Levenshtein.distance(left, right, processor=None)
            maximum = max(len(left), len(right))
            expected = (maximum - distance) / maximum
            self.assertAlmostEqual(
                Levenshtein.normalized_similarity(left, right, processor=None),
                expected,
                places=15,
            )

    def test_unicode_15_nfc_and_explicit_whitespace(self) -> None:
        self.assertEqual(normalize_v1("  e\u0301\r\n\u00a0한  "), "é 한")
        self.assertEqual(normalize_v1("ＡＢＣ １２３"), "ＡＢＣ １２３")
        self.assertEqual(normalize_v1("A\u200bB\ufeffC"), "A\u200bB\ufeffC")
        self.assertEqual(normalize_v1("I"), "I")
        self.assertNotEqual(normalize_v1("I"), normalize_v1("i"))

    def test_exact_normalized_and_threshold_boundaries(self) -> None:
        expected = [
            ("Play", "present"),
            ("e\u0301", "present"),
            ("a" * 20, "present"),
            ("b" * 20, "present"),
            ("c" * 20, "present"),
        ]
        regions = [
            _region(0, "Play"),
            _region(1, "é"),
            _region(2, "a" * 19 + "x"),
            _region(3, "b" * 17 + "xyz"),
            _region(4, "c" * 16 + "wxyz"),
        ]
        output = verify_execute(_snapshot(expected), regions, CONFIG)
        self.assertEqual(
            [item["match_method"] for item in output["items"]],
            ["EXACT", "NORMALIZED", "FUZZY", "FUZZY", "NONE"],
        )
        self.assertEqual(
            [item["verification_status"] for item in output["items"]],
            ["PASS", "PASS", "PASS", "REVIEW", "FAIL"],
        )
        self.assertEqual(output["items"][2]["score_numerator"], 1900)
        self.assertEqual(output["items"][2]["score_denominator"], 20)
        self.assertEqual(output["items"][3]["match_score"], 85.0)
        self.assertEqual(output["items"][4]["match_score"], 0.0)

    def test_unverified_and_no_text_are_distinct(self) -> None:
        output = verify_execute(
            _snapshot([(None, "missing"), ("", "present"), (" \n", "present"), ("Play", "present")]),
            [],
            CONFIG,
        )
        self.assertEqual(
            [item["reason"] for item in output["items"]],
            ["MISSING_TRANSLATION", "EMPTY_EXPECTED", "NORMALIZED_EMPTY_EXPECTED", "NO_MATCH"],
        )
        self.assertEqual(
            [item["verification_status"] for item in output["items"]],
            ["UNVERIFIED", "UNVERIFIED", "UNVERIFIED", "FAIL"],
        )
        self.assertEqual(output["summary"]["verification_status"], "FAIL")
        self.assertTrue(output["summary"]["incomplete"])

    def test_exact_evidence_precedes_cardinality(self) -> None:
        candidates = [
            CandidateEdge(0, 0, "EXACT", 100, 1),
            CandidateEdge(0, 1, "FUZZY", 90, 1),
            CandidateEdge(1, 0, "FUZZY", 90, 1),
        ]
        assigned = assign_candidates(2, 2, candidates)
        self.assertEqual({row: edge.region_index for row, edge in assigned.items()}, {0: 0})

    def test_rational_thresholds_do_not_use_display_rounding(self) -> None:
        self.assertTrue(_at_least(95_000_000, 1_000_000, 95, 1))
        self.assertFalse(_at_least(94_999_999, 1_000_000, 95, 1))
        self.assertTrue(_at_least(85_000_000, 1_000_000, 85, 1))
        self.assertFalse(_at_least(84_999_999, 1_000_000, 85, 1))

    def test_duplicate_expected_and_regions_are_one_to_one(self) -> None:
        output = verify_execute(
            _snapshot([("Play", "present"), ("Play", "present")]),
            [_region(0, "Play")],
            CONFIG,
        )
        self.assertEqual(output["items"][0]["region_index"], 0)
        self.assertEqual(output["items"][0]["verification_status"], "PASS")
        self.assertIsNone(output["items"][1]["region_index"])
        self.assertEqual(output["items"][1]["verification_status"], "FAIL")

    def test_no_expectations_is_successful_unverified(self) -> None:
        output = verify_execute(_snapshot([]), [], CONFIG)
        self.assertEqual(output["summary"]["verification_status"], "UNVERIFIED")
        self.assertEqual(output["summary"]["evaluation_reason"], "NO_EXPECTATIONS")
        self.assertFalse(output["summary"]["incomplete"])


class AssignmentExhaustiveTests(unittest.TestCase):
    @staticmethod
    def _brute(
        expected_count: int,
        region_count: int,
        candidates: list[CandidateEdge],
    ) -> dict[int, CandidateEdge]:
        lookup = {(edge.expected_index, edge.region_index): edge for edge in candidates}
        options = [
            [
                *sorted(
                    edge.region_index
                    for edge in candidates
                    if edge.expected_index == row
                ),
                region_count,
            ]
            for row in range(expected_count)
        ]
        best_objective: tuple[int, int, int, int] | None = None
        best_vector: tuple[int, ...] | None = None
        best: dict[int, CandidateEdge] = {}
        for vector in itertools.product(*options):
            real = [right for right in vector if right < region_count]
            if len(real) != len(set(real)):
                continue
            edges = [
                lookup[(row, right)]
                for row, right in enumerate(vector)
                if right < region_count
            ]
            objective = (
                sum(edge.method == "EXACT" for edge in edges),
                sum(edge.method == "NORMALIZED" for edge in edges),
                len(edges),
                sum(edge.micro_score for edge in edges),
            )
            if (
                best_objective is None
                or objective > best_objective
                or (objective == best_objective and vector < best_vector)
            ):
                best_objective = objective
                best_vector = vector
                best = {edge.expected_index: edge for edge in edges}
        return best

    def test_sparse_solver_matches_bruteforce(self) -> None:
        randomizer = random.Random(20260925)
        methods = ["EXACT", "NORMALIZED", "FUZZY"]
        for _ in range(250):
            expected_count = randomizer.randint(1, 4)
            region_count = randomizer.randint(0, 4)
            candidates: list[CandidateEdge] = []
            for row in range(expected_count):
                for region in range(region_count):
                    if randomizer.random() < 0.55:
                        method = randomizer.choice(methods)
                        numerator = 100 if method != "FUZZY" else randomizer.randint(85, 100)
                        candidates.append(
                            CandidateEdge(row, region, method, numerator, 1)
                        )
            actual = assign_candidates(expected_count, region_count, candidates)
            expected = self._brute(expected_count, region_count, candidates)
            self.assertEqual(
                {row: edge.region_index for row, edge in actual.items()},
                {row: edge.region_index for row, edge in expected.items()},
            )


if __name__ == "__main__":
    unittest.main()
