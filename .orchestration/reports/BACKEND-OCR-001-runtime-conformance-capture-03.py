"""Capture an explicitly supplied command; never infer or rerun a test."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
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
directory = root / ".orchestration/reports/BACKEND-OCR-001-runtime-conformance-evidence-03"
directory.mkdir(exist_ok=True)
log = directory / (args.label + ".log")
record = directory / (args.label + ".json")
if log.exists() or record.exists():
    raise SystemExit("Evidence labels are immutable; choose a new label")
source_paths = ["backend/app/workers/ocr.py", "backend/app/workers/ocr_source.py",
                "tests/backend/test_ocr_runner.py", "tests/backend/test_ocr_source_read.py",
                "tests/backend/test_ocr_runtime_integration.py",
                "backend/app/workers/ocr_runtime.py", "backend/app/workers/ocr_containment.py",
                "backend/app/services/verification_jobs.py",
                "tests/backend/test_ocr_runtime_db.py", "tests/backend/test_ocr_containment.py",
                "backend/app/workers/ocr_admission.py", "tests/backend/test_ocr_admission.py",
                "backend/app/services/verification_runs.py", "tests/backend/test_ocr_api.py",
                "backend/README.md"]
def source_hashes():
    return {path: hashlib.sha256((root / path).read_bytes()).hexdigest()
            for path in source_paths if (root / path).exists()}

data = {"argv": command, "cwd": str(root), "started_utc": datetime.now(timezone.utc).isoformat(),
        "capture_host_os": platform.platform(), "capture_python": sys.version,
        "source_before": source_hashes()}
data["context_sha256"] = {
    path: hashlib.sha256((root / path).read_bytes()).hexdigest()
    for path in (".env", "backend/.env", "pyproject.toml", "backend/Dockerfile",
                 "backend/Dockerfile.test", "backend/requirements.lock",
                 "tests/backend/conftest.py", "docs/architecture/phase-3-ocr-contract.md")
    if (root / path).is_file()
}
data["runtime_environment"] = {
    key: os.environ[key] for key in (
        "QA_OCR_NATIVE_CONTAINMENT_TEST", "QA_OCR_NATIVE_LIMIT_BYTES",
        "QA_OCR_NATIVE_PRESSURE_TEST", "QA_OCR_REAL_RUNTIME_TEST",
        "QA_OCR_MODEL_ROOT", "PADDLE_HOME", "PADDLE_PDX_CACHE_HOME",
        "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "OMP_NUM_THREADS",
        "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS") if key in os.environ
}
with log.open("wb") as stream:
    process = subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT)
data.update(ended_utc=datetime.now(timezone.utc).isoformat(), exit_code=process.returncode,
            log_path=str(log.relative_to(root)), log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
            source_after=source_hashes())
record.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(log.read_text(encoding="utf-8", errors="replace")[-12000:])
print(json.dumps(data))
sys.exit(process.returncode)

