"""Capture an explicitly supplied command; never infer or rerun a test."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument("label")
parser.add_argument("command", nargs=argparse.REMAINDER)
args = parser.parse_args()
command = args.command[1:] if args.command[:1] == ["--"] else args.command
root = Path(__file__).resolve().parents[2]
directory = root / ".orchestration/reports/BACKEND-OCR-001-runtime-rework-evidence-03"
directory.mkdir(exist_ok=True)
log = directory / (args.label + ".log")
record = directory / (args.label + ".json")
if log.exists() or record.exists():
    raise SystemExit("Evidence labels are immutable; choose a new label")
source_paths = ["backend/app/workers/ocr.py", "backend/app/workers/ocr_source.py",
                "tests/backend/test_ocr_runner.py", "tests/backend/test_ocr_source_read.py",
                "tests/backend/test_ocr_runtime_integration.py"]
def source_hashes():
    return {path: hashlib.sha256((root / path).read_bytes()).hexdigest()
            for path in source_paths if (root / path).exists()}

data = {"argv": command, "cwd": str(root), "started_utc": datetime.now(timezone.utc).isoformat(),
        "capture_host_os": platform.platform(), "capture_python": sys.version,
        "source_before": source_hashes()}
with log.open("wb") as stream:
    process = subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT)
data.update(ended_utc=datetime.now(timezone.utc).isoformat(), exit_code=process.returncode,
            log_path=str(log.relative_to(root)), log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
            source_after=source_hashes())
record.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(log.read_text(encoding="utf-8", errors="replace")[-12000:])
print(json.dumps(data))
sys.exit(process.returncode)
