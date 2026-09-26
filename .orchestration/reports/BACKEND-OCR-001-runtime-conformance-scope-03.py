"""Validate the frozen Backend checkpoint and report only scoped source changes."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
report_root = root / '.orchestration/reports'
manifest = report_root / 'BACKEND-OCR-001-runtime-conformance-source-manifest.txt'
baseline_path = report_root / 'BACKEND-OCR-001-runtime-rework-evidence-03/baseline.json'
baseline = json.loads(baseline_path.read_text())['file_sha256']
snapshot = {}
for line in manifest.read_text().splitlines():
    parts = line.split(' ')
    if len(parts) == 2 and len(parts[1]) == 64 and all(c in '0123456789abcdef' for c in parts[1]):
        snapshot[parts[0]] = parts[1]
allowed = {
    'backend/app/workers/ocr.py', 'backend/app/workers/ocr_source.py',
    'backend/app/workers/ocr_runtime.py', 'backend/app/workers/ocr_containment.py',
    'backend/app/workers/ocr_admission.py', 'backend/app/services/verification_jobs.py',
    'backend/app/services/verification_runs.py', 'backend/README.md',
    'tests/backend/test_ocr_runner.py', 'tests/backend/test_ocr_source_read.py',
    'tests/backend/test_ocr_runtime_integration.py', 'tests/backend/test_ocr_runtime_db.py',
    'tests/backend/test_ocr_containment.py', 'tests/backend/test_ocr_admission.py',
    'tests/backend/test_ocr_api.py',
}
current = {p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in snapshot}
changed = sorted(p for p in snapshot if p in baseline and baseline[p] != current[p])
added = sorted(p for p in snapshot if p not in baseline)
removed = sorted(p for p in baseline if (p.startswith(('backend/', 'tests/backend/'))
                 or p == 'pyproject.toml') and p not in snapshot)
drift = sorted(p for p in snapshot if snapshot[p] != current[p])
unexpected = sorted((set(changed) | set(added) | set(removed)) - allowed)
result = dict(
    kind='source-scope-check', source_count=len(snapshot),
    manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
    baseline_sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
    changed_existing=changed, added=added, removed=removed,
    changed_after_freeze=drift, outside_claims=unexpected,
    valid=not(drift or unexpected or removed),
)
output = report_root / 'BACKEND-OCR-001-runtime-conformance-evidence-03/source-scope-01.json'
with output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(result))
raise SystemExit(0 if result['valid'] else 1)
