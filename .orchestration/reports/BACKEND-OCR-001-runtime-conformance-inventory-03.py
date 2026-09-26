"""Inventory immutable Backend03 conformance captures without executing them.

The caller supplies a new JSON output path in the conformance evidence directory.
This helper never starts a test, container, or any other child process.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVIDENCE = (
    ROOT / ".orchestration/reports/BACKEND-OCR-001-runtime-conformance-evidence-03"
)
DEFAULT_WORKER42 = ROOT / ".orchestration/reports/OCR-001-05-source-manifest.txt"
HEX64 = set("0123456789abcdef")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_to_root(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in HEX64 for character in value.lower())
    )


def safe_root_file(value: object) -> Path | None:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        return None
    candidate = (ROOT / value).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError:
        return None
    return candidate


def safe_evidence_file(value: object, evidence: Path) -> Path | None:
    candidate = safe_root_file(value)
    if candidate is None:
        return None
    try:
        candidate.relative_to(evidence)
    except ValueError:
        return None
    return candidate


def parse_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def capture_shape(data: object) -> bool:
    return isinstance(data, dict) and "argv" in data and "log_path" in data


def source_snapshot(value: object, label: str) -> tuple[dict[str, str], list[str]]:
    if not isinstance(value, dict):
        return {}, [f"{label} is not an object"]
    snapshot: dict[str, str] = {}
    errors: list[str] = []
    for path, digest in sorted(value.items()):
        if not isinstance(path, str) or safe_root_file(path) is None:
            errors.append(f"{label} has unsafe source path {path!r}")
        elif not is_sha256(digest):
            errors.append(f"{label} has invalid SHA-256 for {path}")
        else:
            snapshot[path] = digest
    return snapshot, errors


def junit_inventory(path: Path) -> dict[str, object]:
    result: dict[str, object] = {"path": relative_to_root(path)}
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as error:
        result.update(valid=False, error=str(error))
        return result

    cases = root.findall(".//testcase")
    counts = {"tests": len(cases), "failures": 0, "errors": 0, "skipped": 0}
    for case in cases:
        if case.find("failure") is not None:
            counts["failures"] += 1
        if case.find("error") is not None:
            counts["errors"] += 1
        if case.find("skipped") is not None:
            counts["skipped"] += 1
    counts["passed"] = (
        counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
    )

    suites = [root] if root.tag == "testsuite" else root.findall(".//testsuite")
    leaf_suites = [
        suite
        for suite in suites
        if not suite.findall("./testsuite")
    ]
    declared: dict[str, int] = {}
    declared_valid = True
    for key in ("tests", "failures", "errors", "skipped"):
        try:
            declared[key] = sum(int(suite.attrib.get(key, "0")) for suite in leaf_suites)
        except ValueError:
            declared_valid = False
    declared_matches_actual = declared_valid and all(
        declared[key] == counts[key] for key in declared
    )
    result.update(
        valid=declared_matches_actual,
        actual_case_counts=counts,
        declared_leaf_suite_counts=declared if declared_valid else None,
        declared_matches_actual=declared_matches_actual,
        elapsed_seconds=sum(float(case.attrib.get("time", "0")) for case in cases),
        sha256=sha256(path),
        bytes=path.stat().st_size,
    )
    return result


def capture_inventory(json_path: Path, data: dict[str, object], evidence: Path) -> dict[str, object]:
    label = json_path.stem
    issues: list[str] = []
    argv = data.get("argv")
    if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
        issues.append("argv is not a string array")
        argv = None
    for field in ("started_utc", "ended_utc"):
        if not parse_timestamp(data.get(field)):
            issues.append(f"{field} is not an ISO-8601 timestamp")
    if not isinstance(data.get("exit_code"), int) or isinstance(data.get("exit_code"), bool):
        issues.append("exit_code is not an integer")

    before, before_issues = source_snapshot(data.get("source_before"), "source_before")
    after, after_issues = source_snapshot(data.get("source_after"), "source_after")
    issues.extend(before_issues)
    issues.extend(after_issues)
    paths = sorted(set(before) | set(after))
    source_changes = [
        {"path": path, "before": before.get(path), "after": after.get(path)}
        for path in paths
        if before.get(path) != after.get(path)
    ]
    current_source: list[dict[str, object]] = []
    for path in paths:
        current_path = safe_root_file(path)
        assert current_path is not None
        current = sha256(current_path) if current_path.is_file() else None
        current_source.append(
            {
                "path": path,
                "capture_after": after.get(path),
                "current": current,
                "matches_capture_after": current == after.get(path) and current is not None,
            }
        )

    log_path = safe_evidence_file(data.get("log_path"), evidence)
    log: dict[str, object]
    if log_path is None:
        issues.append("log_path is absent, unsafe, or outside the evidence directory")
        log = {"valid": False}
    elif not log_path.is_file():
        issues.append("referenced log file is missing")
        log = {"path": relative_to_root(log_path), "valid": False, "missing": True}
    else:
        actual = sha256(log_path)
        expected = data.get("log_sha256")
        matches = is_sha256(expected) and actual == expected
        if not matches:
            issues.append("referenced log SHA-256 does not match capture record")
        log = {
            "path": relative_to_root(log_path),
            "valid": matches,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "bytes": log_path.stat().st_size,
        }

    xml_path = evidence / f"{label}.xml"
    junit = junit_inventory(xml_path) if xml_path.is_file() else {"present": False}
    if junit.get("present") is not False and not junit.get("valid"):
        issues.append("JUnit XML is not parseable or has invalid declared counts")
    if junit.get("present") is not False and not junit.get("declared_matches_actual"):
        issues.append("JUnit declared case counts do not match parsed test cases")
    argv_text = " ".join(argv) if argv is not None else ""
    build_command_failure = (
        data.get("exit_code") not in (None, 0)
        and junit.get("present") is False
        and "docker" in argv_text.lower()
        and (" build " in f" {argv_text.lower()} " or "buildx" in argv_text.lower())
    )
    return {
        "label": label,
        "record_path": relative_to_root(json_path),
        "record_sha256": sha256(json_path),
        "record_bytes": json_path.stat().st_size,
        "argv": argv,
        "started_utc": data.get("started_utc"),
        "ended_utc": data.get("ended_utc"),
        "exit_code": data.get("exit_code"),
        "log": log,
        "junit": junit,
        "command_outcome": (
            "COMMAND_FAILURE_NOT_PRODUCT_TEST"
            if build_command_failure
            else "RECORDED_EXIT_CODE_ONLY"
        ),
        "command_outcome_note": (
            "A denied or failed Docker build/configuration command is retained as a command failure, not a product test result."
            if build_command_failure
            else "The recorded exit code is inventory data; this helper does not infer product-test status."
        ),
        "source_before_after_changes": source_changes,
        "current_source_comparison": current_source,
        "current_source_test_pass_inference": "NOT_INFERRED",
        "current_source_test_pass_note": (
            "A hash match to a capture does not establish that any test passed on current source."
        ),
        "valid": not issues,
        "issues": issues,
    }


def worker42_inventory(manifest: Path) -> dict[str, object]:
    result: dict[str, object] = {"manifest_path": relative_to_root(manifest)}
    try:
        raw = manifest.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        result.update(valid=False, issues=[str(error)])
        return result

    issues: list[str] = []
    lines = text.splitlines()
    headers: dict[str, str] = {}
    row_start = 0
    for index, line in enumerate(lines):
        if not line:
            row_start = index + 1
            break
        if "=" not in line:
            issues.append(f"invalid header line {index + 1}")
            continue
        key, value = line.split("=", 1)
        headers[key] = value
    else:
        issues.append("missing blank separator after headers")
        row_start = len(lines)

    expected_count: int | None
    try:
        expected_count = int(headers.get("count", ""))
    except ValueError:
        expected_count = None
        issues.append("count header is not an integer")
    if headers.get("schema_version") != "1":
        issues.append("schema_version is not 1")
    expected_aggregate = headers.get("aggregate_sha256")
    if not is_sha256(expected_aggregate):
        issues.append("aggregate_sha256 header is invalid")

    rows: list[dict[str, object]] = []
    canonical_path_hash_rows: list[str] = []
    canonical_full_rows: list[str] = []
    for expected_ordinal, line in enumerate(lines[row_start:], start=1):
        fields = line.split("\t")
        if len(fields) != 4:
            issues.append(f"row {row_start + expected_ordinal} does not have four tab fields")
            continue
        ordinal, path_text, byte_count, expected_digest = fields
        expected_ordinal_text = f"{expected_ordinal:04d}"
        if ordinal != expected_ordinal_text:
            issues.append(f"row ordinal {ordinal!r} is not {expected_ordinal_text!r}")
        try:
            declared_bytes = int(byte_count)
            if declared_bytes < 0:
                raise ValueError
        except ValueError:
            declared_bytes = None
            issues.append(f"invalid byte count for {path_text}")
        source = safe_root_file(path_text)
        if source is None:
            issues.append(f"unsafe Worker42 path {path_text!r}")
        elif not (path_text.startswith("worker/") or path_text.startswith("tests/ocr/")):
            issues.append(f"out-of-scope Worker42 path {path_text!r}")
        if not is_sha256(expected_digest):
            issues.append(f"invalid SHA-256 for {path_text}")
        actual_digest = sha256(source) if source is not None and source.is_file() else None
        actual_bytes = source.stat().st_size if source is not None and source.is_file() else None
        matches = (
            actual_digest == expected_digest
            and actual_bytes == declared_bytes
            and actual_digest is not None
        )
        if not matches:
            issues.append(f"Worker42 current file does not match {path_text}")
        rows.append(
            {
                "ordinal": ordinal,
                "path": path_text,
                "expected_bytes": declared_bytes,
                "actual_bytes": actual_bytes,
                "expected_sha256": expected_digest,
                "actual_sha256": actual_digest,
                "matches": matches,
            }
        )
        canonical_path_hash_rows.append(f"{path_text} {expected_digest}")
        canonical_full_rows.append(line)
    if expected_count != len(rows):
        issues.append(f"count header {expected_count!r} does not match parsed rows {len(rows)}")

    aggregates = {
        "path_sha256_lf": hashlib.sha256(
            ("\n".join(canonical_path_hash_rows) + "\n").encode("utf-8")
        ).hexdigest(),
        "full_tab_rows_lf": hashlib.sha256(
            ("\n".join(canonical_full_rows) + "\n").encode("utf-8")
        ).hexdigest(),
    }
    aggregate_format = next(
        (name for name, digest in aggregates.items() if digest == expected_aggregate), None
    )
    if aggregate_format is None:
        issues.append("aggregate_sha256 does not match a supported parsed-row canonicalization")
    result.update(
        manifest_sha256=hashlib.sha256(raw).hexdigest(),
        manifest_bytes=len(raw),
        headers=headers,
        parsed_rows=len(rows),
        aggregate_candidates=aggregates,
        aggregate_format=aggregate_format,
        rows=rows,
        valid=not issues,
        issues=issues,
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--validate-worker42",
        action="store_true",
        help="validate the immutable OCR-001-05 42-entry source manifest",
    )
    parser.add_argument("--worker42-manifest", type=Path, default=DEFAULT_WORKER42)
    args = parser.parse_args()

    evidence = args.evidence_dir.resolve()
    if not evidence.is_dir():
        parser.error("--evidence-dir must be an existing directory")
    output = args.output.resolve()
    if output.parent != evidence:
        parser.error("--output must be directly inside --evidence-dir")
    if output.exists():
        parser.error("--output already exists; evidence inventory outputs are immutable")
    if output.suffix.lower() != ".json":
        parser.error("--output must have a .json suffix")

    captures: list[dict[str, object]] = []
    non_capture_json: list[dict[str, object]] = []
    for json_path in sorted(evidence.glob("*.json")):
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            non_capture_json.append(
                {"path": relative_to_root(json_path), "valid_json": False, "error": str(error)}
            )
            continue
        if capture_shape(data):
            captures.append(capture_inventory(json_path, data, evidence))
        else:
            non_capture_json.append(
                {
                    "path": relative_to_root(json_path),
                    "valid_json": True,
                    "sha256": sha256(json_path),
                    "reason": "not a capture record",
                }
            )

    known_xml = {entry["label"] for entry in captures}
    unpaired_xml = [
        junit_inventory(xml_path)
        for xml_path in sorted(evidence.glob("*.xml"))
        if xml_path.stem not in known_xml
    ]
    worker42 = worker42_inventory(args.worker42_manifest.resolve()) if args.validate_worker42 else None
    valid = (
        all(capture["valid"] for capture in captures)
        and all(item.get("valid", False) for item in unpaired_xml)
        and (worker42 is None or worker42["valid"])
    )
    inventory = {
        "schema_version": 1,
        "kind": "BACKEND-OCR-001-runtime-conformance-inventory",
        "evidence_dir": relative_to_root(evidence),
        "capture_count": len(captures),
        "captures": captures,
        "non_capture_json": non_capture_json,
        "unpaired_junit": unpaired_xml,
        "worker42": worker42,
        "valid": valid,
        "current_source_test_pass_inference": "NOT_INFERRED",
        "current_source_test_pass_note": (
            "This is an evidence inventory. It never runs tests and does not promote owner evidence or AC status."
        ),
    }
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(inventory, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
