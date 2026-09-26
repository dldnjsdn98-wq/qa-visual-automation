# REVIEW-UPLOAD-001 / Reviewer 08 read-only preflight

Date: 2026-09-25 KST
Reviewer: 08
Contract: P2-UPLOAD-v1 document revision 2, SHA-256 `e47d3dca18fef169600bf6bebe78a31432105e5a1ae5b80a9934e1bf4ee8f843`
Difficulty/model: high; parent and two bounded subagents requested `gpt-5.6-sol/high`; actual applied models unverified.

## Status and boundary

This is a read-only risk preflight, not the final `REVIEW-UPLOAD-001` execution or disposition. The review task remains BLOCKED until `FRONTEND-UPLOAD-VERIFY-001` submits actual Web evidence and PM activates the full review.

At initial delegation, Backend and Frontend implementation submissions were `READY_FOR_REVIEW` while uploader cleanup was still running. During this preflight PM reported the final uploader report/handoff received with matching hashes, all three implementations `READY_FOR_REVIEW`, and Frontend Web verification activated `READY`. That update was integrated without starting a duplicate uploader audit.

No DB/service/Docker/product test was run. No product, uploader, Frontend, PM YAML, contract, environment, Commit, Push, or IP-connectivity action was performed. Owner results below remain owner evidence and are not relabeled independent PASS.

## Submitted evidence snapshot

| Artifact | SHA-256 / status |
| --- | --- |
| `.orchestration/reports/BACKEND-UPLOAD-001-03.md` | `7d6fb450f5bfec711bcc633bc934722faf08f5e12d7749cadd86c9fcb0f0f75b` |
| `.orchestration/reports/BACKEND-UPLOAD-001-03-addendum.md` | `6b07c32b61dfa8bcbbf51ad6bc516baff3b430a42e933fdb49c5e35ad15df267` |
| `.orchestration/reports/BACKEND-UPLOAD-001-linux-final.txt` | `742bf80c48bd1bb9e1e8361b9742ac5d87fa75810f3b9ff7013148b00f6de4c7` |
| `.orchestration/handoffs/BACKEND-UPLOAD-001-03.md` | `8c6f86e62385fe98bd45bdb76e95e359f00dc9e950fc9ce56d9cc94f7af9ab7e` |
| Backend owner result | 94 Linux/PostgreSQL tests; image build and `pip check` reported PASS; not rerun |
| `.orchestration/reports/FRONTEND-UPLOAD-001-04.md` | `a44f28be39eebf2dae5cc0fe92457f3c95588615e7fc3026206301cf5d1454cb` |
| Frontend product files | All six submitted hashes independently matched PM state; owner 26 tests/typecheck/build not rerun |
| `.orchestration/reports/UPLOAD-001-06.md` | `08a0c633d87e839f8c1d37707af6cf5cdd3e39bebf17f7df081a4a90f7dbfbda` |
| `.orchestration/handoffs/UPLOAD-001-06.md` | `f2e4160aa09ed055aef6c27e4e7f7e81713773531ef08146cc0b38b711771920` |
| Uploader owner result | Final Windows 63 including live lost-201/restart/replay reported PASS; Linux 57+1 skip predates final five F26 cases |

The Backend report's abbreviated Linux command is made reproducible by its addendum: it records the executed shared synthetic-container path and a standalone equivalent with an ephemeral PostgreSQL 17 container, explicit synthetic credentials, random per-suite databases, Alembic head, and forced cleanup. The addendum correctly supersedes the unsupported “missing Windows interpreter” statement with native Windows Backend suite `NOT_RUN`.

For drift detection, I hashed sorted UTF-8 lines of `relative/path sha256` for all 75 files under `backend/`, `tests/backend/`, plus `pyproject.toml`, with one final LF. Aggregate SHA-256: `6d05846c63c9ef29d5e523134b8dad9dad2f33ed0fbac74f6720ac4f23c97f3f`.

## Preflight findings

The findings below describe the original inspected snapshot. Corrected Backend evidence has since been received and hash-verified as recorded in the final update; all three findings remain OPEN pending independent closure. Original paths/line numbers and hashes are retained as historical evidence, not descriptions of the corrected snapshot.

### R08-P2-PREFLIGHT-001 — MAJOR product defect — same-length object corruption is served

Contract section 6, line 159 requires a missing or mismatched committed original to return `503 STORAGE_UNAVAILABLE`, preserving the Screenshot/receipt and never serving or overwriting the bad object.

Actual trace:

1. `backend/app/services/screenshots.py:224-233` opens the referenced object, reads `row.size_bytes + 1`, and checks only the stat/read lengths.
2. It does not compare SHA-256 with `row.file_hash` and does not call the existing `storage.verify_exact(...)` method.
3. `backend/app/api/v1/screenshots.py:90-95` returns those bytes as HTTP 200 with a one-hour private cache header.
4. Replace a committed object with different bytes of exactly the same length. Both length checks pass, so the substituted content is returned and may be cached as the committed original.

The independent check also confirmed `LocalStorage.verify_exact` does perform stable-handle size and SHA-256 verification at `backend/app/storage/local.py:105-131`; the content path simply does not use it. The existing HTTP regression at `tests/backend/test_screenshots.py:140-151` covers a missing object only. `tests/backend/test_reconcile_upload_receipts.py:50-63` checks `verify_exact` in isolation, not content delivery.

Impact: corrupted or substituted screenshot content can be delivered as valid even though the database identity/hash still names the original. This blocks later acceptance unless Owner 03 fixes the content path and supplies a same-length mismatch regression.

Relevant snapshot hashes:

- `backend/app/services/screenshots.py`: `03e2f92e1f8e3fa465ddbf521c13fb5573a1355011c42e737e3f3f766120a950`
- `backend/app/api/v1/screenshots.py`: `6b03cdc57794edb034c3cf3ce7986f51ecb0e99b8669b30f03df7301e92d67fc`
- `backend/app/storage/local.py`: `ca93d0dce1418ee0db6b2868fdda5c1328e2cf1958411cb0df2214219f370afc`

### R08-P2-PREFLIGHT-002 — MAJOR evidence gap — F14 maintenance safety is not executed against receipts

The implementation in `backend/app/maintenance/reconcile_storage.py` is directionally aligned: it inventories Screenshot and PROCESSING references, verifies committed objects, marks remaining PROCESSING receipts FAILED under asserted exclusivity, refreshes DB inventory, and performs a fresh primary reference recheck before exact deletion.

The submitted executed evidence does not prove those receipt-aware transitions:

- `tests/backend/test_reconcile_upload_receipts.py:21-35` protects a constructed `ProcessingReference` only and never calls `reconcile`.
- The real-DB `reconcile` test at `tests/backend/test_migrations_storage.py:137-161` creates a Screenshot, an orphan, and staging entries, but no `UploadReceipt`.
- Therefore no executed test proves live/expired PROCESSING candidate protection, durable FAILED transition before eligibility, post-transition inventory refresh, 24-hour candidate eligibility, or fresh-reference insertion blocking deletion.

Contract lines 161, 263, and F14 require exclusive receipt-aware maintenance, multi-connection PostgreSQL/fault evidence, and reject mocks alone as proof. Impact: current owner evidence is insufficient for AC-P2-03 maintenance safety even if static source is plausible.

Relevant snapshot hashes:

- `backend/app/maintenance/reconcile_storage.py`: `db7a44c79f039cdc3d54d1e47cfdd34b7a439ff0187b4386acd0d0df651cb059`
- `tests/backend/test_reconcile_upload_receipts.py`: `db023f51bb200f36b5104b8d765a090e5553fa5880c95c9265aeb8c81e030f3c`

### R08-P2-PREFLIGHT-003 — MAJOR evidence gap — populated migration preservation is partial

`backend/migrations/versions/0003_phase2_upload_receipts.py` is statically additive with no migration DML, which lowers but does not eliminate the evidence requirement.

`tests/backend/test_migrations_storage.py:43-99` seeds a Phase-1 Screenshot with `storage_key` and `file_hash`, but its post-upgrade select/assertion at lines 78-91 checks only project, source, null client ID, and filename. It uses default empty metadata and does not re-read and compare `file_hash`, `storage_key`, metadata, or the complete historical row facts required by section 5 line 108 and F21. A migration that altered those values would still pass this test.

Impact: the owner statement that populated `0002→0003` preservation is covered is only partially evidenced. Full review needs an executed populated fixture with non-empty nested Unicode metadata and exact before/after comparison of ID, hash, filename, metadata, storage key, dimensions/media/size and historical timestamps/relationships, plus referenced object-byte readback.

Relevant snapshot hashes:

- `backend/migrations/versions/0003_phase2_upload_receipts.py`: `b882b7eb714ba4b79995b73bfef9e3940108fcda23eb9dbaa05243da121cd228`
- `tests/backend/test_migrations_storage.py`: `387da5e8df93c30a54cd5af508a42c2f928c10543af58c1dd8f0e604bb9e8694`

## Receipt/fencing inspection result

The disjoint receipt/lease/fencing subagent found no concrete source blocker in its bounded read-only pass. This is not execution evidence. The later independent review should still cover the following risk-selected cases against a disposable real PostgreSQL primary:

1. Same key/same intent replay, changed-intent conflict, and same UUID in another project.
2. Concurrent first-insert arbitration with exactly one generation-1 owner and no loser publication.
3. Lease time just before, exactly at, and after DB `clock_timestamp()` expiry; equality must permit takeover.
4. Fresh generation/token/candidate key on takeover and complete stale-owner denial for renew/FAILED/finalize/delete.
5. Ambiguous first insert, takeover, and finalize, each with committed-response-loss and actual rollback outcomes.
6. Known rollback mutating only the still-owned PROCESSING generation after rollback is confirmed.
7. Exact same-generation object recovery versus size/hash mismatch and uncertain publication.
8. Lock, statement, transaction, renewal, primary-detection, and storage failures with bounded safe responses and no guessed ownership.

## Focused commands/evidence required for full review

Do not run these until PM activates the full review and the Backend correction plus Web submission are stable.

1. Owner 03 correction/resubmission must add a targeted content test: upload a synthetic image, replace its object with different same-length bytes, GET `content_url`, require `503 STORAGE_UNAVAILABLE`, and prove the DB row/object are not overwritten or deleted. Then run the targeted test and the complete Backend suite using the standalone ephemeral PostgreSQL command from `BACKEND-UPLOAD-001-03-addendum.md`.
2. Add/run real-DB F14 cases through `reconcile(...)`: live and expired PROCESSING candidate protection; dry-run no mutation; apply-mode durable FAILED-before-eligibility; fault after FAILED commit with no deletion; fresh Screenshot/PROCESSING reference inserted at the pre-delete barrier; unavailable primary and incomplete inventory; exact >24h deletion only.
3. Expand/run the populated `0002→0003` preservation test with exact before/after row and object-byte snapshots, non-empty nested Unicode metadata, and metadata/model parity.
4. Independently execute the receipt/fencing matrix above with fault barriers, not timing sleeps or global ambiguous monkeypatches. Preserve exact request/receipt/Screenshot/object counts and IDs for each outcome.
5. Owner Linux final-source coverage has now been supplemented by the addendum below: 63 collected, 62 passed, 1 opt-in live skipped, including the five F26 cases. The earlier 57-pass snapshot remains historical. After activation, assess final source hashes and independently run the risk-selected uploader checks and Windows live lost-201/restart/replay case. Owner results remain owner evidence.
6. Verify the cross-service live case after all final source hashes stabilize: discarded 201, Backend and uploader restart, exact 200 replay, one receipt/Screenshot/object, matching ID/time/Location/hash, and list/detail/content metadata.
7. Consume the pending `FRONTEND-UPLOAD-VERIFY-001` actual Web submission and independently verify agent/automation source, non-null client ID, metadata version, complete safe multilingual nested metadata, original hash/content, and unchanged manual upload behavior.
8. Recompute the Backend and uploader source manifests before execution. Any drift from the snapshot above or the PM-recorded uploader hashes requires evidence/source rematching before results are combined.

## Commands and attribution

| Action | Result |
| --- | --- |
| Read Backend owner report, addendum, Linux log, handoff, accepted contract and Frontend report | PASS, read-only |
| Hash Backend/Frontend/uploader submitted artifacts and six Frontend product files | PASS, exact reported/PM hashes |
| Inspect actual content read/storage verification, migration, maintenance and relevant tests | PASS, read-only source trace |
| Two disjoint Sol/high subagents | Completed: receipt/fencing found no concrete source gap and produced focused tests; migration/reconcile produced the three findings, each independently checked by parent |
| Backend source manifest | PASS, 75 files, aggregate recorded above |
| Backend/uploader/Frontend/Web tests | NOT_RUN by explicit preflight restriction |
| AC-P2-01 through AC-P2-04 | NOT_RUN; no acceptance inference |

## Next action

Changed file: this preflight report only. Branch/commit: `null` / `null`. No Commit/Push.

PM should route R08-P2-PREFLIGHT-001 to Owner 03 for correction and require focused evidence for R08-P2-PREFLIGHT-002/003 before final review activation. `FRONTEND-UPLOAD-VERIFY-001` may continue on its own gate, but `REVIEW-UPLOAD-001` remains BLOCKED until the actual Web submission and matching corrected Backend/uploader/Frontend evidence are stable. Reviewer 08 will then execute the risk-selected commands and return only the formal `ACCEPTED` or `CHANGES_REQUESTED` disposition.

## Subsequent owner Linux evidence received

PM supplied `.orchestration/reports/UPLOAD-001-linux-final-06.md`; Reviewer read the entire artifact and independently matched SHA-256 `9f0822f563e493650eab23ec8d3fd8e1d819f093e331cc1e56bd3f3ab6643ab6`.

The addendum reports final-source clean Linux execution including all five F26 cases: 63 collected, 62 passed, and exactly one skipped opt-in live integration test in 1.16s. It records zero source bytecode before/after, a clean hash-locked venv, pip check, per-file source hashes, raw pytest output, and source-manifest aggregate `593e1925a36e55b667c752be7cc10ea944f14cf81f034f5d112d23358f7a563e`. The earlier run that consumed pre-existing Windows bytecode is explicitly excluded from qualifying evidence.

This supplements the obsolete Linux snapshot coverage gap at the owner-evidence level. Reviewer has not executed the tests or independently matched the embedded manifest to current uploader source. The skipped Linux live test and owner Windows live result remain separately attributed; cross-service validation must match the corrected Backend submission.

PM also reports preliminary actual-Web JSON received and Owner 03 working on all three preflight findings. No duplicate restart or new audit was dispatched. The three findings remain pending corrected submission and independent review; preliminary Web evidence does not activate full review. `REVIEW-UPLOAD-001` remains BLOCKED and AC-P2-01 through AC-P2-04 remain NOT_RUN.

This update changes this report only. Its original submitted hash was `df50c3b749876a0ad5b310b09c0c2a9e72c3d05a649b3eb458331df1d8e2a6f1`; the new report hash is supplied to PM after readback.

## Corrected Backend submission received

Reviewer read the complete rework report, handoff, execution log, and manifest addendum. Independently measured artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| reports/BACKEND-UPLOAD-001-rework-03.md | b83e53bbc787020b6c81b0b32b57dff3e8a65d3d49d8152911d70b529edac968 |
| handoffs/BACKEND-UPLOAD-001-rework-03.md | 68335accb905f4efafc0545a2ecce7d7c94a9c5cd41c93dea1c44c7fd8a19c8a |
| reports/BACKEND-UPLOAD-001-rework-linux.txt | a31e384c36e8f0caa28f1102496bc3ddf2f8786f3bc27bb0c4f9216622a4d8b1 |
| reports/BACKEND-UPLOAD-001-rework-manifest-addendum.md | e89185a0c8f036d5bcb3a28f048167cc3bbe1c63ecb076b6dfd20e1ec6aa43c5 |
| reports/BACKEND-UPLOAD-001-rework-source-manifest.txt | 1464c7678cf044f0da996c19cc0174dc31581306e7c011ba98ff1e5d1dc754e5 |

All paths in this table are under `.orchestration/`. Reviewer independently verified the manifest's exact file hash, all 75 current source-file hashes, complete current `rg --files backend tests/backend` plus `pyproject.toml` inventory, and ordinal path ordering. Read-only PowerShell checks returned: `PASS canonical manifest=1464c7678cf044f0da996c19cc0174dc31581306e7c011ba98ff1e5d1dc754e5; files=75; all current source hashes and ordinal inventory matched`.

Canonical review input is now this 75-file manifest. The owner rework report/handoff aggregate `d1799260941c7396c4e3931f21eb07e4857e90f7075d84fba962a1f5b672a0fe` is historical, superseded because of culture-sensitive versus ordinal sorting. This aggregate correction itself does not indicate source drift. The earlier preflight 75-file aggregate remains the original pre-correction source snapshot.

Owner rework claims and preserved execution evidence:

- Finding 001: hashes the exact content bytes from one open handle, with HTTP tests for normal, missing, different-length and same-length changed objects and preserved durable state.
- Finding 002: adds real PostgreSQL receipt-aware reconcile coverage, independent sessions, FAILED-commit boundaries, refreshed inventory, fresh pre-delete references, age boundaries and fail-closed fault cases.
- Finding 003: expands the populated migration fixture to complete Screenshot-column snapshots, nested Unicode metadata, timestamps/relationships and actual original-byte preservation without changing migration 0003.
- Owner corrected targeted result: 29 passed. Owner final unmounted Linux image result: 119 passed. The initial test-only `capture_metadata` mapping failure and its correction remain visible in the log. These are OWNER results, not Reviewer test executions.

The focused full-review steps above now consume this corrected submission and its exact targeted selection rather than requesting duplicate owner work. After PM activation, independently inspect and execute `tests/backend/test_screenshots.py::test_content_read_verifies_returned_bytes_and_preserves_state`, `tests/backend/test_reconcile_upload_receipts.py`, and `tests/backend/test_migrations_storage.py::test_0002_data_is_preserved_by_additive_0003_migration`, then integrate the other risk-selected receipt, uploader and actual-Web checks. Recheck final source hashes before combining evidence.

Backend is READY_FOR_REVIEW. R08-P2-PREFLIGHT-001/002/003 remain OPEN for independent closure. PM reports final actual-Web submission in progress; full `REVIEW-UPLOAD-001` remains BLOCKED until that submission and PM activation. No test, service, environment, product, PM-state change, duplicate restart or additional subagent was performed for this update. Only this Reviewer report was updated; prior version SHA-256 was `3500e3cb0ee7dbe2005596e1d8aad6352f76d19a1fb4a8c73432372bee3dd475`.
