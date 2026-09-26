from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import sys
import time
import unicodedata
from pathlib import Path

import rfc8785

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from worker.verification import verify_execute
from worker.verification.assignment import CandidateEdge, assign_candidates


SEED = 20260925


def _peak_rss_bytes() -> int | None:
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            class Counters(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            kernel.GetCurrentProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(Counters),
                wintypes.DWORD,
            ]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            handle = kernel.GetCurrentProcess()
            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            if psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return int(counters.PeakWorkingSetSize)
        except Exception:
            return None
        return None
    try:
        import resource

        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(value if sys.platform == "darwin" else value * 1024)
    except (ImportError, OSError, ValueError):
        return None


def _environment() -> dict[str, object]:
    try:
        import rapidfuzz

        rapidfuzz_version: str | None = rapidfuzz.__version__
    except ImportError:
        rapidfuzz_version = None
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "unicode_version": unicodedata.unidata_version,
        "rapidfuzz_version": rapidfuzz_version,
    }


def assignment_maximum() -> dict[str, object]:
    expected_count = 1_000
    region_count = 1_000
    edge_count = 65_536
    randomizer = random.Random(SEED)
    seen: set[tuple[int, int]] = set()
    edges: list[CandidateEdge] = []
    methods = ("EXACT", "NORMALIZED", "FUZZY")
    while len(edges) < edge_count:
        expected = randomizer.randrange(expected_count)
        region = randomizer.randrange(region_count)
        if (expected, region) in seen:
            continue
        seen.add((expected, region))
        method = methods[randomizer.randrange(len(methods))]
        numerator = 100 if method != "FUZZY" else randomizer.randrange(85, 101)
        edges.append(CandidateEdge(expected, region, method, numerator, 1))
    edge_payload = [
        [
            edge.expected_index,
            edge.region_index,
            edge.method,
            edge.score_numerator,
            edge.score_denominator,
        ]
        for edge in edges
    ]
    input_sha256 = hashlib.sha256(rfc8785.dumps(edge_payload)).hexdigest()
    started = time.perf_counter()
    assigned = assign_candidates(expected_count, region_count, edges)
    elapsed = time.perf_counter() - started
    result_payload = [
        [
            expected,
            edge.region_index,
            edge.method,
            edge.score_numerator,
            edge.score_denominator,
        ]
        for expected, edge in sorted(assigned.items())
    ]
    return {
        "scenario": "assignment-maximum-v1",
        "seed": SEED,
        "expected_count": expected_count,
        "region_count": region_count,
        "eligible_edge_count": len(edges),
        "assigned_count": len(assigned),
        "input_sha256": input_sha256,
        "result_sha256": hashlib.sha256(rfc8785.dumps(result_payload)).hexdigest(),
        "elapsed_seconds": elapsed,
        "peak_rss_bytes": _peak_rss_bytes(),
        "environment": _environment(),
        "scope": "pure assignment only; not whole-attempt OCR qualification",
    }


def verification_work_limit() -> dict[str, object]:
    import string

    count = 256
    alphabet = string.ascii_letters
    texts = [
        "A" * 25
        + alphabet[index % len(alphabet)]
        + alphabet[(index // len(alphabet)) % len(alphabet)]
        for index in range(count)
    ]
    snapshot = {
        "snapshot_version": 1,
        "sha256": "a" * 64,
        "items": [
            {
                "position": index,
                "string_key_id": f"key-{index}",
                "string_id": f"string-{index}",
                "entry_id": f"entry-{index}",
                "expected_text": texts[index],
                "translation_status": "present",
            }
            for index in range(count)
        ],
    }
    regions = [
        {
            "region_index": index,
            "text": texts[(index * 37) % count],
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
    configuration = {
        "configuration_sha256": "b" * 64,
        "pass_threshold": 95,
        "review_threshold": 85,
        "normalization_version": "norm-v1",
        "matching_version": "one-to-one-levenshtein-v1",
    }
    input_sha256 = hashlib.sha256(
        rfc8785.dumps(
            {
                "snapshot": snapshot,
                "regions": regions,
                "configuration": configuration,
            }
        )
    ).hexdigest()
    started = time.perf_counter()
    output = verify_execute(snapshot, regions, configuration)
    elapsed = time.perf_counter() - started
    output_bytes = rfc8785.dumps(output)
    return {
        "scenario": "verification-work-limit-v1",
        "seed": None,
        "expected_count": count,
        "region_count": count,
        "real_pair_count": count * count,
        "distance_work_upper_bound": count * count * 27 * 27,
        "assigned_count": sum(
            item["region_index"] is not None for item in output["items"]
        ),
        "verification_status": output["summary"]["verification_status"],
        "input_sha256": input_sha256,
        "result_sha256": hashlib.sha256(output_bytes).hexdigest(),
        "result_bytes": len(output_bytes),
        "elapsed_seconds": elapsed,
        "peak_rss_bytes": _peak_rss_bytes(),
        "environment": _environment(),
        "scope": "pure verification only; not whole-attempt OCR qualification",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "scenario",
        choices=("assignment-maximum", "verification-work-limit"),
    )
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    if arguments.scenario == "assignment-maximum":
        result = assignment_maximum()
    else:
        result = verification_work_limit()
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if arguments.output is not None:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(encoded, encoding="utf-8", newline="\n")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
