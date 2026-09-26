# BACKEND-OCR-001 runtime rework / blocked draft checkpoint / Backend03

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

All host commands ran at `C:\Dev\qa-visual-automation`, Windows 11 build26200, Python3.12.14. Each command JSON contains exact argv, start/end UTC, exit code, host facts and source hashes before/after. Log and JUnit bytes are inventoried below. Each pytest run emitted one existing deprecation warning.

| Evidence label | Actual outcome | JUnit elapsed |
| --- | --- | --- |
| windows-jobs-results-01 | 26 passed / 0 failed / 0 skipped | 1.982 s |
| windows-source-01 | 16 passed / 0 failed / 0 skipped | 4.116 s |
| windows-runner-02 | 1 passed / 3 failed / 5 skipped | 6.363 s |
| windows-oversize-03 | 1 passed / 0 failed / 0 skipped | 0.621 s |
| linux-independent-01 | 19 passed / 0 failed / 0 skipped | 6.439 s |

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

Draft source manifest has97 files, ordinal path ordering, LF payload and aggregate `081dabaa09e862c645bb191d81cf4e8d7affc238554e08b8580fa95905d905a5`. Manifest SHA-256: `fbaf582a8d8606b1ab794e42a54e2de48513d43783cf899dd28a7c0c2639e039`. It labels itself BLOCKED_DRAFT, not final qualification. Product hashes: ocr.py `638f29322859a68add9530337f3135364938a34be2543161c67d1d5674cd70c4`; ocr_source.py `b685fc61cedbe4d10e81cc88e93341987c5af39f6f5bac6a3a97d5a59cc26a6f`.

`git diff --check` returned0 (line-ending warnings only). This command does not inspect untracked additions; scope hashes and captured execution separately identify the new files. No commit, push, deployment, dependency/storage/provider/API/profile/Worker/frontend/PM-state edits were made by Backend03.

Preserved prior artifacts: runtime-resume report SHA73919a4de478f1c85484f3388ac776b7a85e542cff316fea06d6ff89cb918afc; handoff SHAa04677b98e76996020c98d54c1fbb2a61f7f85e2b4bdc7bd39d38f6878979d97; Backend95 manifest SHA7b3bb7e5638f1e7cbda101bd2e5451f5453c0b547e410b3b9d7d06a3b8e2e23d; reproducibility addendum SHAaef7bea1af2d8c57938736be4ad8b95e6a7c4dc23e30d210ec314ce8c2274d18. Frontend04 pre-fix evidence was not modified or reclassified.

## Captured commands

### windows-jobs-results-01

```json
[".\\.pytest_cache\\agent-clean-win\\Scripts\\python.exe", "-m", "pytest", "tests/backend/test_ocr_jobs.py", "tests/backend/test_ocr_result_validation.py", "tests/backend/test_finalize_reference_lock.py", "-q", "--tb=short", "-p", "no:cacheprovider", "--basetemp", ".pytest_cache/backend-runtime-rework-jobs-01", "--junitxml", ".orchestration/reports/BACKEND-OCR-001-runtime-rework-evidence-03/windows-jobs-results-01.xml"]
```

### windows-source-01

```json
[".\\.pytest_cache\\agent-clean-win\\Scripts\\python.exe", "-m", "pytest", "tests/backend/test_ocr_source_read.py", "-q", "--tb=short", "-p", "no:cacheprovider", "-o", "junit_family=xunit1", "--basetemp", ".pytest_cache/backend-runtime-rework-source-01", "--junitxml", ".orchestration/reports/BACKEND-OCR-001-runtime-rework-evidence-03/windows-source-01.xml"]
```

### windows-runner-02

```json
[".\\.pytest_cache\\agent-clean-win\\Scripts\\python.exe", "-m", "pytest", "tests/backend/test_ocr_runner.py", "-q", "-rs", "--tb=short", "-p", "no:cacheprovider", "-o", "junit_family=xunit1", "--basetemp", ".pytest_cache/backend-runtime-rework-runner-02", "--junitxml", ".orchestration/reports/BACKEND-OCR-001-runtime-rework-evidence-03/windows-runner-02.xml"]
```

### windows-oversize-03

```json
[".\\.pytest_cache\\agent-clean-win\\Scripts\\python.exe", "-m", "pytest", "tests/backend/test_ocr_runner.py::test_oversized_ipc_frame_is_result_limit_exceeded", "-q", "--tb=short", "-p", "no:cacheprovider", "-o", "junit_family=xunit1", "--basetemp", ".pytest_cache/backend-runtime-rework-oversize-03", "--junitxml", ".orchestration/reports/BACKEND-OCR-001-runtime-rework-evidence-03/windows-oversize-03.xml"]
```

### linux-independent-01

```json
["docker", "run", "--rm", "--network", "none", "-v", "C:\\Dev\\qa-visual-automation\\.orchestration\\reports\\BACKEND-OCR-001-runtime-rework-evidence-03:/evidence", "qa-backend-ocr-rework-diagnostic:20260925", "python", "-m", "pytest", "tests/backend/test_ocr_source_read.py", "tests/backend/test_ocr_runner.py::test_partial_ipc_frame_cannot_block_deadline_enforcement", "tests/backend/test_ocr_runner.py::test_truncated_ipc_frame_is_retryable_process_crash", "tests/backend/test_ocr_runner.py::test_oversized_ipc_frame_is_result_limit_exceeded", "-q", "--tb=short", "-p", "no:cacheprovider", "-o", "junit_family=xunit1", "--basetemp", "/tmp/qa-rework-independent", "--junitxml", "/evidence/linux-independent-01.xml"]
```

## Raw evidence inventory

Paths below are relative to `.orchestration/reports/BACKEND-OCR-001-runtime-rework-evidence-03/`. `artifact-inventory.json` additionally records sizes. The capture helper, source-manifest generator and this checkpoint generator are Backend03-only evidence artifacts.

| Artifact | SHA-256 |
| --- | --- |
| `baseline.json` | `c545572230051f07db131403e46793d900639e55e274603af9128eb8485d8214` |
| `diff-check-01.json` | `02ec7eea73f83dcb715df85732ac7b227bd5a5bf73ff0dadd42d4dba5dbc41e5` |
| `diff-check-01.log` | `5df26c96d847b4cd369b4b6085213e744fb14dfd79897cf9d6a40fdeba930638` |
| `draft-image-identity-01.json` | `1e5788874e23cf83d9a387505ad51a33da95807729c2d8dc424f7c739f8c6cb5` |
| `draft-image-identity-01.log` | `205d54c68936fd8316ac55c16a81ba44ccdc0e439a8f903b38a9e0e39a63002e` |
| `draft-test-image-build-01.json` | `14e64b3c169415b915af28854c7967f752babc3d1a801540558875cde89d765c` |
| `draft-test-image-build-01.log` | `fdeed81087fa72d66095cb29142d7441e2adef748ccafa409fea827468c3000d` |
| `linux-independent-01.json` | `5754f77e0bdf6366aed135ea45d6ecc3bf0fa6fcf763517c0b040c413cde1a38` |
| `linux-independent-01.log` | `5c2f6ea8e4c5decd02d66185d325a37e3a51aaf35524c56435c4df42f98d509a` |
| `linux-independent-01.xml` | `4e00abceb72c5d1b9a951c4715d7137beba46395cca4bbfb99b7403073747e97` |
| `preflight-images.json` | `583f5421d47b9d70139b605b80807c4705a8724d2182728b1b394db0e77bfd17` |
| `preflight-images.log` | `d7e025f4e7340e8db22eb95c17db7ba0e68d4a7656e769121f734f7465367c80` |
| `scope-checkpoint.json` | `87ceb2a18ef97f3ff8fad876c2983ee459d3dc0df4ffd12e97ddf1a0921de823` |
| `scope-interim.json` | `731d7d7d0bfd7656aabdc7b0e09db06932d5d551ca21a6da04ee91a3d1512791` |
| `windows-jobs-results-01.json` | `c66aa0a82fc93f3be3127d9a1aba368c9aadaa24fda6627cb18a60ed956361be` |
| `windows-jobs-results-01.log` | `f0b848553996e658ab714c2eff253d25d3efebcf7b5312df869e8a7afd98f967` |
| `windows-jobs-results-01.xml` | `39bafeda4354f7b149d590ca064115fdcc913316edaf63511fb5f0c6294f2a1d` |
| `windows-oversize-03.json` | `0df9c2ad88342cc0cbc46c650ba019df526dca975beb7b09ee6e3a2ae3e043df` |
| `windows-oversize-03.log` | `527593a0e3ca2504278b7f3da19908e19515558974262c80c9b594d6056fb209` |
| `windows-oversize-03.xml` | `13599dc74944ff3a4ab710140070322aaa2b195c17b20e7964cc6c0703020156` |
| `windows-runner-02.json` | `b9c5ef0a100d495a29afadda82dfafa45da2b246a076eefaada570510657194e` |
| `windows-runner-02.log` | `918f0ef8d170c7f6bb6acf2d5877e4107e68dac32ab6e1f8f3b005981adcf1b6` |
| `windows-runner-02.xml` | `80d436c3c35875728826a20a2fb2342d0529d8719ce039d0afc1696b43efecba` |
| `windows-source-01.json` | `19b9b3846d221c5b1903ab2f99aec973c036222ace458d624a5b9a1cd511f59e` |
| `windows-source-01.log` | `78968f0b12885aaf84c01bf9e7cc86a8406bbf42b06fc405970754e3435fa8a7` |
| `windows-source-01.xml` | `8fe7cf6293b2909a5d30507cdfa7916396ca30e0fdf035545e0a83c2dead5ee7` |
| `worker-baseline.json` | `0a09e2c4df30b915a4e055258f787d93ef43147e097242f6d502d8c58031b110` |

## Next owner

PM/Architect02 must resolve the child-authority/parent-DB cleanup design question. Backend03 then corrects the two-file runner design, preserves causal retry/fence behavior, fixes cleanup failures and completes captured affected integration and final image evidence. Only PM may activate Frontend04 rerun and then Reviewer08. This checkpoint does not activate either.
