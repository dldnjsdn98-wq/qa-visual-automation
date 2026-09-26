"""Write the blocked draft checkpoint from existing, captured evidence only."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[2]
reports = root / '.orchestration/reports'
evidence = reports / 'BACKEND-OCR-001-runtime-rework-evidence-03'
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

baseline = json.loads((evidence / 'baseline.json').read_text())['file_sha256']
changed = {p: digest(root / p) if (root / p).exists() else None
           for p, old in baseline.items()
           if not (root / p).exists() or digest(root / p) != old}
new = [p.relative_to(root).as_posix() for directory in ('backend', 'tests/backend')
       for p in (root / directory).rglob('*')
       if p.is_file() and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts
       and p.suffix not in ('.pyc', '.pyo') and p.relative_to(root).as_posix() not in baseline]
worker = json.loads((evidence / 'worker-baseline.json').read_text())
worker_checks = [{'path': row['path'], 'actual': digest(root / row['path']),
                  'expected': row['expected']} for row in worker['checks']]
allowed = {'backend/app/workers/ocr.py', 'backend/app/workers/ocr_source.py',
           'tests/backend/test_ocr_runner.py', 'tests/backend/test_ocr_source_read.py',
           'tests/backend/test_ocr_runtime_integration.py'}
scope = {'status': 'BLOCKED_DRAFT_CHECKPOINT', 'changed': changed, 'new': sorted(new),
         'unexpected': sorted((set(changed) | set(new)) - allowed),
         'worker_checks': worker_checks,
         'worker_all_match': all(r['actual'] == r['expected'] for r in worker_checks),
         'worker_manifest_sha256': digest(reports / 'OCR-001-05-source-manifest.txt')}
(evidence / 'scope-checkpoint.json').write_text(json.dumps(scope, indent=2) + '\n')
inventory = {p.name: {'sha256': digest(p), 'bytes': p.stat().st_size}
             for p in sorted(evidence.iterdir()) if p.is_file() and p.name != 'artifact-inventory.json'}
(evidence / 'artifact-inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')

labels = ['windows-jobs-results-01', 'windows-source-01', 'windows-runner-02',
          'windows-oversize-03', 'linux-independent-01']
results = []
for label in labels:
    suite = ET.parse(evidence / (label + '.xml')).find('.//testsuite')
    a = suite.attrib
    passed = int(a['tests']) - int(a['failures']) - int(a['errors']) - int(a['skipped'])
    results.append(f"| {label} | {passed} passed / {a['failures']} failed / {a['skipped']} skipped | {a['time']} s |")
artifact_rows = '\n'.join(f"| `{name}` | `{value['sha256']}` |" for name, value in inventory.items())
commands = '\n\n'.join('### ' + label + '\n\n```json\n' + json.dumps(
    json.loads((evidence / (label + '.json')).read_text())['argv'], ensure_ascii=False) + '\n```'
    for label in labels)
manifest = reports / 'BACKEND-OCR-001-runtime-rework-draft-source-manifest.txt'

report = '''# BACKEND-OCR-001 runtime rework / blocked draft checkpoint / Backend03

Date: 2026-09-25. Task: P3-RUNTIME-001. Status: BLOCKED_DRAFT_NOT_READY_FOR_REVIEW.
Branch and commit: null. This is partial owner evidence, not contract compliance, final qualification, or acceptance.

## Disposition and implementation

PM authorized runner/source helper and three backend test files under `.orchestration/handoffs/PHASE-3-runtime-rework-01.md`. The draft isolates metadata, storage, adapters and DB work in one spawn child; validates durable size 1..20,971,520 before storage access; reads expected size plus one guard byte; verifies exact length and SHA-256 on the same returned buffer; bounds IPC; and reserves cleanup within the original 300-second budget. `RuntimeSpec` serializes a trusted database URL string with repr disabled, not an engine/session. No secrets were logged.

Independent Astra review and PM identified a contract violation: accepted contract line58 explicitly says the child has no DB write authority. The draft moves heartbeat, stage, fail and finalize into that child. PM instructed Backend03 to hold further product changes pending Architect02 disposition. The two product files remain a rejected draft; do not deploy or use this snapshot for Frontend04 live verification. No product changes occurred after this hold.

Blanket quarantine also changes known timeout/resource/crash outcomes into lease-expiry recovery instead of preserving the required causal failure/retry state. A sequential DB-writing failure child or mutation handshake was proposed but NOT authorized or implemented. Lost IPC cannot establish zero result rows. Existing fresh-primary locked/fenced ambiguity recovery remains authoritative.

The conforming alternative keeps metadata/source/OCR/matching in one read-only child and restores claim/heartbeat/stage/finalize/fail to the parent. Phase/result IPC remains bounded. Its unresolved concern is parent database/network waits: synchronous calls may delay supervision, while a Python thread cannot be safely force-stopped; existing connect/statement/lock timeouts do not prove thread termination within the attempt budget. This concrete question is with PM/Architect02. Already-validated COMMIT completion under contract60 is permitted; strict server-side no-late-COMMIT is NOT an added requirement or remaining blocker.

RSS remains sampled direct-child observation, not a proven descendant/short-peak hard cap. Architect02 interpretation is pending. No cgroup, Job Object, profile or security change was made.

## Delegation actually used

- 최상: Astra medium implementation, followed by a separate Astra medium independent read-only review.
- 상: Sol high target tests.
- 하: Terra high initial evidence scaffolds (earlier segment).
- 최하: Luna high baseline/Worker42 scope verification.
- 중 Sol medium: no separate suitable slice was needed. No duplicate task was created merely to use a model.

## Actual captured execution

All host commands ran at `C:\\Dev\\qa-visual-automation`, Windows 11 build26200, Python3.12.14. Each command JSON contains exact argv, start/end UTC, exit code, host facts and source hashes before/after. Log and JUnit bytes are inventoried below. Each pytest run emitted one existing deprecation warning.

| Evidence label | Actual outcome | JUnit elapsed |
| --- | --- | --- |
''' + '\n'.join(results) + '''

The Windows runner failure at frozen test hash46304fee contains two unresolved cleanup failures (timeout and RSS paths return unproven-termination quarantine instead of the expected causal error), plus an oversized-frame test error. The frame receive allowance is MAX_RESULT_BYTES+1 including its protocol tag. Parent corrected only the test payload from MAX_RESULT_BYTES+1 to MAX_RESULT_BYTES+2; targeted `windows-oversize-03` then passed. New runner-test hash is72d42ff5704d31b1193a71bb5fb7ea1d24de32561a7c9c9d4b75ed5cf88feeda. Cleanup expectations were NOT weakened, and these failed cases were NOT rerun after the hold.

Cleanup-cause execution count: (1) Sol's initial diagnostic, (2) parent's captured windows-runner-02. Two observed executions, not three. Design reviews and non-test pauses are not failure attempts. No third identical cleanup execution occurred. At a third occurrence, stop that path per PM. Sol's initial diagnostic was16 passed/5 failed in13.81s, before later fixture corrections; it had no raw-log/JUnit file or recoverable source hashes. Its exact argv and limitations are retained in `BACKEND-OCR-001-runtime-rework-tests-sol-high-03.md`; no artifacts were fabricated retroactively.

Blocked source open/read went through the real `load_attempt` with a blocking test storage object inside a spawned process. Windows measured2.031000/2.016000s; Linux2.004958/2.005138s. Work cutoff was2s inside an absolute3s stop budget (assertion permits0.25s scheduler tolerance); this is a short fault simulation, not a literal300s soak. All four recorded exitcode-15, dead child and dead receiver, and no post-load marker. The test never starts a production heartbeat, so its unchanged parent-thread inventory does not prove production heartbeat cleanup. Production deadline/RSS cleanup failures remain separate.

Windows raw partial/truncated POSIX frames are explicitly skipped because Windows uses message-mode PipeConnection. Their Windows equivalence remains NOT_RUN. Linux partial/truncated and oversized frames passed. Three architecture-dependent run_once probes are explicitly skipped, not passed.

Linux used a newly rebuilt diagnostic-only test image `qa-backend-ocr-rework-diagnostic:20260925`, ID `sha256:d9d1ce1e3bf2374db4958d3b91e2eb88ceb7f1c4054f70d2d087f9ae3d449cb0`, linux/amd64, Python3.12.14 slim trixie. Existing `backend/Dockerfile.test` was unchanged; build and pip-check completed. Network was disabled, baked `/app` code was used, and only this evidence directory was mounted at `/evidence`. No DB/model mount was used. The container used --rm. This is NOT a production qualification image; no production image was rebuilt and prior accepted tags were preserved.

The26-test Windows DB slice used the existing fixture's uniquely allocated `qa_backend_test_<uuid>` database and per-test storage; normal successful teardown runs only on that allocated synthetic database. Its exact generated name was not captured by those existing tests. No shared/user DB was reset. Real OCRRunner/model integration was NOT_RUN due to the explicit design hold.

## Remaining verification matrix

| Area | Status |
| --- | --- |
| Source size boundaries, exact bytes/hash, read errors, Windows/Linux blocked acquisition | PASS for isolated loader/supervisor mechanics |
| Linux partial/truncated/oversized IPC; Windows oversized IPC | PASS for isolated protocol mechanics |
| Windows partial/truncated transport equivalence | NOT_RUN |
| Shared source-to-matching remaining budget, production heartbeat cleanup | PENDING |
| Windows deadline/RSS shutdown and no receiver residue | FAIL, two paths unresolved |
| Retry cause/state preservation, claim ACK, stale fence and commit/lost IPC integration | PENDING; three draft probes SKIPPED |
| Final production image, real qualified-model OCRRunner integration | NOT_RUN / PM design hold |
| Existing jobs/result/reference-lock regression |26 PASS; not proof of the new runner's integration |
| All AC-P3-01..04, Frontend04 affected rerun, Reviewer08 | NOT_RUN / remain PM-controlled |

## Scope and identities

Only the authorized five source/test paths changed against the recorded pre-edit baseline; no unexpected baseline differences were found. Worker42 remained42/42 exact matches. Actual Worker manifest SHA-256 is `98ea7e81109668dd073ef4f011b4d4c14eff3eea2a96340a00062f6850050b0a`; the initial owner scaffold omitted one zero, corrected here without editing Worker or prior evidence. Worker aggregate remains `058a445d90b7c50897f77f503a31e7dd425ea71f845a70a40666816e3c7a7b94`.

Draft source manifest has97 files, ordinal path ordering, LF payload and aggregate `081dabaa09e862c645bb191d81cf4e8d7affc238554e08b8580fa95905d905a5`. Manifest SHA-256: `''' + digest(manifest) + '''`. It labels itself BLOCKED_DRAFT, not final qualification. Product hashes: ocr.py `638f29322859a68add9530337f3135364938a34be2543161c67d1d5674cd70c4`; ocr_source.py `b685fc61cedbe4d10e81cc88e93341987c5af39f6f5bac6a3a97d5a59cc26a6f`.

`git diff --check` returned0 (line-ending warnings only). This command does not inspect untracked additions; scope hashes and captured execution separately identify the new files. No commit, push, deployment, dependency/storage/provider/API/profile/Worker/frontend/PM-state edits were made by Backend03.

Preserved prior artifacts: runtime-resume report SHA73919a4de478f1c85484f3388ac776b7a85e542cff316fea06d6ff89cb918afc; handoff SHAa04677b98e76996020c98d54c1fbb2a61f7f85e2b4bdc7bd39d38f6878979d97; Backend95 manifest SHA7b3bb7e5638f1e7cbda101bd2e5451f5453c0b547e410b3b9d7d06a3b8e2e23d; reproducibility addendum SHAaef7bea1af2d8c57938736be4ad8b95e6a7c4dc23e30d210ec314ce8c2274d18. Frontend04 pre-fix evidence was not modified or reclassified.

## Captured commands

''' + commands + '''

## Raw evidence inventory

Paths below are relative to `.orchestration/reports/BACKEND-OCR-001-runtime-rework-evidence-03/`. `artifact-inventory.json` additionally records sizes. The capture helper, source-manifest generator and this checkpoint generator are Backend03-only evidence artifacts.

| Artifact | SHA-256 |
| --- | --- |
''' + artifact_rows + '''

## Next owner

PM/Architect02 must resolve the child-authority/parent-DB cleanup design question. Backend03 then corrects the two-file runner design, preserves causal retry/fence behavior, fixes cleanup failures and completes captured affected integration and final image evidence. Only PM may activate Frontend04 rerun and then Reviewer08. This checkpoint does not activate either.
'''
(reports / 'BACKEND-OCR-001-runtime-rework-03.md').write_text(report, encoding='utf-8')
handoff = '''# BACKEND-OCR-001 runtime rework checkpoint / Backend03

- Task: P3-RUNTIME-001. Status: BLOCKED_DRAFT_NOT_READY_FOR_REVIEW.
- Branch/commit: null. No final qualification or acceptance claimed.
- Detailed report: `.orchestration/reports/BACKEND-OCR-001-runtime-rework-03.md`.
- Draft97-file manifest: `.orchestration/reports/BACKEND-OCR-001-runtime-rework-draft-source-manifest.txt`.

Current two-file draft moves DB writes into a child, conflicting with accepted contract58. PM explicitly held further product changes pending Architect02. Timeout quarantine also does not preserve required causal retry behavior. Parent-owned DB alternative has an unresolved bounded network/thread-cleanup question. Already-validated COMMIT completion under contract60 is allowed; strict server late-COMMIT prohibition is not required.

Captured actual tests: Windows existing jobs/results/reference locks26 PASS; source loader16 PASS; runner1 PASS/3 FAIL/5 SKIP; corrected oversize-only1 PASS; Linux independent loader/IPC19 PASS. Two Windows shutdown paths still fail. Initial Sol diagnostic16 PASS/5 FAIL has no raw log/JUnit/source hashes and remains explicitly limited evidence. Only two cleanup-cause executions occurred; no third retry or weakened expected result. Windows raw partial/truncated IPC and three architecture-dependent probes are skipped. Real OCR integration and final production image NOT_RUN.

Parent changed only the oversized-frame fixture after Sol freeze (max result bytes+2 exceeds the payload+tag allowance); runner-test SHA72d42ff5704d31b1193a71bb5fb7ea1d24de32561a7c9c9d4b75ed5cf88feeda. Other tests/product identities and exact commands/log/XML hashes are in the report and capture JSON. Diagnostic image d9d1ce1e3bf2374db4958d3b91e2eb88ceb7f1c4054f70d2d087f9ae3d449cb0 is only for independent Linux tests, not deployment or live rerun.

Worker42 unchanged, actual manifest SHA98ea7e81109668dd073ef4f011b4d4c14eff3eea2a96340a00062f6850050b0a. Backend97 draft aggregate081dabaa09e862c645bb191d81cf4e8d7affc238554e08b8580fa95905d905a5. Scope checkpoint has no unexpected changes. Prior reports/images/Web evidence remain preserved.

Next owner: PM/Architect02 disposition, then Backend03 compliant implementation and affected evidence. Frontend04/Reviewer08 remain inactive. AC-P3-01..04 NOT_RUN. No push/deploy/user deletion/DB reset/security changes.
'''
(root / '.orchestration/handoffs/BACKEND-OCR-001-runtime-rework-03.md').write_text(handoff, encoding='utf-8')
for p in [reports / 'BACKEND-OCR-001-runtime-rework-03.md', root / '.orchestration/handoffs/BACKEND-OCR-001-runtime-rework-03.md', evidence / 'artifact-inventory.json']:
    print(p.relative_to(root), digest(p))
print('unexpected', scope['unexpected'], 'worker_match', scope['worker_all_match'])
