r"""Static ARCH-001 evidence only; does not test implemented APIs or acceptance.

Run from repository root: .\.venv\Scripts\python.exe docs/architecture/check_contract.py
"""

import json
import re
from pathlib import Path
from uuid import UUID

import yaml


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "architecture"


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    documents = [DOCS / name for name in (
        "overview.md", "domain-model.md", "api-contract.md", "data-flow.md"
    )]
    examples = []
    links = 0
    for path in documents:
        content = path.read_text(encoding="utf-8-sig")
        check("ARCH-001" in content, f"Missing contract owner: {path.name}")
        check(content.count("```") % 2 == 0, f"Unclosed code fence: {path.name}")
        for target in re.findall(r"\]\(([^)]+)\)", content):
            if "://" not in target and not target.startswith("#"):
                check((path.parent / target.split("#")[0]).is_file(), f"Broken link: {target}")
                links += 1
        check(not re.search(r"[A-Z]:[\\/].*(?:python|node)(?:\.exe)?", content, re.I),
              f"Machine executable path in {path.name}")
        for block in re.findall(r"```json\s*\n(.*?)\n```", content, re.S):
            examples.append(json.loads(block))

    check(len(examples) == 4, "Expected four independently parseable JSON examples")
    error, expected, upload, screenshot = examples
    UUID(error["error"]["request_id"])
    check(expected["total"] == len(expected["items"]), "Expected count mismatch")
    missing = [item for item in expected["items"] if item["translation_status"] == "missing"]
    check(expected["missing_count"] == len(missing), "Missing count mismatch")
    check(all(item["text"] is None and item["entry_id"] is None for item in missing),
          "Missing translation must preserve nulls")
    check([item["position"] for item in expected["items"]] == list(range(expected["total"])),
          "Expected order mismatch")
    for field in ("build_id", "locale_id", "category_id", "situation_id", "source"):
        check(upload[field] == screenshot[field], f"Upload/response mismatch: {field}")
    for obj in (expected, upload, screenshot):
        for key, value in obj.items():
            if key.endswith("_id") and value is not None:
                UUID(value)
    check(re.fullmatch(r"[0-9a-f]{64}", screenshot["file_hash"]), "Invalid hash shape")
    expected_url = f'/api/v1/projects/{screenshot["project_id"]}/screenshots/{screenshot["id"]}/content'
    check(screenshot["content_url"] == expected_url, "Content URL scope mismatch")
    check("storage_key" not in screenshot, "Storage key exposed")

    def read_yaml(name):
        return yaml.safe_load((ROOT / ".orchestration" / name).read_text(encoding="utf-8-sig"))

    tasks = read_yaml("TASKS.yaml")
    acceptance = read_yaml("ACCEPTANCE.yaml")
    state = read_yaml("PROJECT_STATE.yaml")
    by_id = {task["id"]: task for task in tasks["tasks"]}
    check(len(by_id) == len(tasks["tasks"]), "Duplicate task IDs")
    check(by_id["ARCH-001"]["status"] == "READY_FOR_REVIEW", "Architecture submission missing")
    check(by_id["ARCH-001"]["review_result"] is None, "Owner must not self-accept")
    criterion = next(item for item in acceptance["architecture"] if item["id"] == "AC-ARCH-01")
    check(criterion["status"] in {"NOT_RUN", "FAIL"}, "Re-review submission must not self-accept")
    history = by_id["ARCH-001"].get("review_history", [])
    check(any(item["result"] == "CHANGES_REQUESTED" and item["finding"] == "R08-ARCH-001"
              for item in history), "Prior independent review must remain traceable")
    for item in history:
        check((ROOT / item["evidence"]).is_file(), "Missing historical review evidence")
    check(by_id["ARCH-001"].get("review_requested") is True, "Re-review request missing")
    check((ROOT / by_id["ARCH-001"]["handoff"]).is_file(), "Missing current handoff")
    for evidence in by_id["ARCH-001"]["tests"]:
        check((ROOT / evidence["evidence"]).is_file(), "Missing submission evidence")
    for task_id in ("BACKEND-WEB-001", "FRONTEND-WEB-001", "REVIEW-WEB-001"):
        check(by_id[task_id]["status"] == "BLOCKED", f"Premature promotion: {task_id}")
    check(state["current_phase"] == 1, "Unexpected phase promotion")
    check(state["active_roles"] == ["01", "02"], "Unexpected role activation")
    check(all(phase["status"] != "ACCEPTED" for phase in acceptance["phases"]),
          "Owner must not accept phases")
    print(f"PASS: {len(documents)} documents; {links} local links; {len(examples)} JSON examples")
    print("PASS: example scopes, missing translation semantics, hash shape and content URL")
    print("PASS: orchestration YAML, preserved review history, re-review state and unchanged downstream gates")
    print("NOT_RUN: independent AC-ARCH-01 re-review, product API/DB/storage/Frontend tests")


if __name__ == "__main__":
    main()
