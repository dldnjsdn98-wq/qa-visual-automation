# REVIEW-UPLOAD-001 independent rereview / Reviewer 08

Date: 2026-09-25  
Source root: `C:\Dev\qa-visual-automation`  
Activation: `.orchestration/handoffs/PHASE-2-review-recovery-rework-01.md`  
Prior formal review retained: `.orchestration/reports/REVIEW-UPLOAD-001-08.md` (`1da2d73e837d62bc4b9926f41b168a56d12bc64bd9ab8c56001640d7c234bab8`) and `.orchestration/handoffs/REVIEW-UPLOAD-001-08.md` (`f182ffe3eb83b7ae193bb7c5efdca4d852c950108bce0822d11fff919dee13cf`)

## Disposition

**ACCEPTED.**

The matching Backend, uploader and Frontend/Web corrections satisfy the accepted Phase 2 contract in independent execution. All nine open findings from the preceding formal review are resolved. Reviewer 08 recommends that PM01 promote AC-P2-01 through AC-P2-04 to PASS and record this new review result; PM01 remains the sole owner of `.orchestration/ACCEPTANCE.yaml`, `TASKS.yaml`, `PROJECT_STATE.yaml`, and phase status.

The only retained execution limit is that the explicit `pg_is_in_recovery()` fail-closed branch was not run against a real recovery/standby PostgreSQL server. The complete corrected reconciliation matrix ran against a fresh PostgreSQL 17 primary, and static inspection confirms the primary guard. This is recorded as a NOT_RUN limit, not a remaining Phase 2 blocker.

## Acceptance recommendation

| Criterion | Reviewer recommendation | Independent basis |
| --- | --- | --- |
| AC-P2-01 Durable offline queue preserves originals | PASS | Windows uploader risk suite: 133 passed, 1 Linux-only skip. Linux local-filesystem/origin boundary: 109 passed, 1 Windows-only skip. Crash/restart, producer publication, durable state, recovery and original-preservation cases passed. |
| AC-P2-02 Retry/backoff and terminal failures | PASS | Windows worker/protocol/producer/recovery suite passed; independent live discarded-201, process restart and exact-200 replay passed; failed/exhausted originals and matching-response transition rules are covered. |
| AC-P2-03 Idempotency and duplicate prevention survive restart | PASS | Fresh PostgreSQL risk set: 90 passed. Reviewer receipt transaction matrix: 4 passed. Live lost-201/restart/replay: 1 passed. These cover concurrent first arbitration, DB-clock expiry/takeover, fence freshness and denial, ambiguous commit outcomes, lock timeout, atomic completion, migration preservation and reconciliation. |
| AC-P2-04 Uploaded screenshots and metadata appear in Web | PASS | Current-harness independent live run and actual browser inspection showed exactly manual, agent and automation rows; exact originals, source, dimensions, IDs and nested multilingual/empty-string metadata were displayed. Vitest 26 passed, TypeScript typecheck passed, and the production Web build returned 0. |

## Submitted correction identity

| Submission | SHA-256 |
| --- | --- |
| Backend report | `095d641be32bce1d0c66672c875a34493c96555acca604a53c21ad96dfafa0a4` |
| Backend handoff | `1881739c037e5f0dfdc191807ff7dbef10b81f4e295b6bf8d4ac2efd0cdad322` |
| Backend 77-file manifest | `a8b5225bceb106cc3e09883eb3e68c2a28d659f8c0ee9ec65eb6974ffa7696a0` |
| Uploader report | `6658de2c47c8ca4050db535ac19f5ee5e296a69d96a281b74a32301030054483` |
| Uploader handoff | `e85302871e857e8ece42b33c80bd0d2ef802b5ea0e49ffe624af24f69cd9c9b9` |
| Uploader 35-file manifest | `eefafa7ce16a82b8f30613612968b6acb74b3ba09f3f2f2788547a7937b9c934` |
| Frontend current-harness report | `7bdb230738299c8c8fbdd1d6f54799b6c38bf55d423385fc2315f3c78ad37f6c` |
| Frontend current-harness handoff | `29340fb500630ccd8f47ab64f026bc4026717ab1904763b2353848b6e8ee4fa0` |
| Frontend owner evidence JSON | `20381330b485f0617b2933eeb2e16068e59ce66035e81fa64ab4c8f1d15563dd` |
| Frontend owner Web log | `f25fb855e2a93338665dc4942cd76d00f0448ef6428ca7166c436d6978b31577` |
| Executed/current Web harness | `3d4952eb33bf6c4c928563a128d7b6fa7d19305ce4005096fdce61fbbe69ee1c` |
| Frontend integration contract test | `a30e873a2ee7f6b3163a048efa5407cbb183ab695cfb1164c990fbb93ca2373c` |

All 77 Backend and all 35 uploader manifest entries were independently rehashed against current files with zero mismatches. Both manifests are ordinally sorted and exactly complete for their declared inventories. Their only overlap is `pyproject.toml`, producing 111 unique paths; adding the current Web harness produces the expected 112-path current snapshot. The six submitted Frontend implementation files also match PM's recorded hashes:

- `frontend/lib/types.ts` — `050e57b9691fe70555d5af5d71e051519587e9f41101a660f81e79c609867894`
- `frontend/lib/api.ts` — `d878049044a2a2f51f774e9101a9fb7337df1193d376094627d1662db0f5b04c`
- `frontend/components/screenshots.tsx` — `f0bb3b21081269ae7fa4c7132a766505ac634738e47dc356bad9bdd7a8ed8c9d`
- `frontend/app/globals.css` — `62cdf7877404b6b3c93f9bedd5b92aee1f527c2d85dff7eda9d42786f4c5a3f6`
- `frontend/tests/api.test.ts` — `79ad3cfc27be8e0994761531a8184ae42be596c3a5e4d6bc8f1d24c026a801f7`
- `frontend/tests/components.test.tsx` — `1755be9b3c61ed7783433c99cf45795d004b3af61b9540bf5bcc985bdd21e74f`

## Independent execution

Environment: Windows NT 10.0.26200.0; PowerShell 7.6.5; project Python 3.12.10; bundled Node 24.19.0; pnpm 11.25.0; Docker client/server 29.7.2, API 1.55, Linux amd64 daemon. PostgreSQL image ID: `sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`. Backend Linux reference image: `sha256:f5d00d7ef450f7150f87794061991ffea1d25bcea6ef7dce9ef67ea40072669b`.

Every database, storage tree and uploader spool used fresh synthetic isolation. No user/shared database was reset or accessed.

| Lane / command | Result | Evidence SHA-256 |
| --- | --- | --- |
| `python -m pytest` over `test_request_concurrency.py`, `test_finalize_reference_lock.py`, full `test_screenshots.py`, full `test_reconcile_upload_receipts.py`, `test_0002_data_is_preserved_by_additive_0003_migration`, upload receipt constraints, response contract and JCS fingerprint tests against fresh PostgreSQL 17 | PASS: 90 passed, 1 deprecation warning, 6.05s | `REVIEW-UPLOAD-001-rereview-08-a.xml` — `299e386db2021931de6d2ca7fa2c3eb85d6164af5ee360104bdb42815ea688de` |
| `.venv\Scripts\python.exe -m pytest tests/upload/test_durable_fs.py tests/upload/test_origin_binding.py tests/upload/test_producer_state.py tests/upload/test_protocol_json.py tests/upload/test_worker_recovery.py` | PASS: 133 passed, 1 Linux-only skip, 1.80s | `REVIEW-UPLOAD-001-rereview-08-b-win.xml` — `8c503482561e5ee022c01113d5ee40b616d198a341acdc0c565f2d162db113d0` |
| `docker run --rm --name qa-review08-b-linux-0b4bf42e -e PYTHONPATH=/workspace -v C:\Dev\qa-visual-automation:/workspace:ro ... python -m pytest /workspace/tests/upload/test_durable_fs.py /workspace/tests/upload/test_origin_binding.py -q --junitxml=...` | PASS: 109 passed, 1 Windows-only skip, 1 read-only cache warning, 1.39s | `REVIEW-UPLOAD-001-rereview-08-b-linux.xml` — `ff6a77086a4baeb2a624562086d08c09a995af075ed010b212a4ecf29a0b1210` |
| Independent live lost-201 / Backend+uploader restart / exact-200 replay | PASS: 1 passed, 8.52s | `REVIEW-UPLOAD-001-rereview-08-b-live.xml` — `664292dd30e7ca907796bc9d73cb78ef958026931bb3cba37ea01383130482ef` |
| Vitest API/components using review-local cache config | PASS: 2 files, 26 tests, 0 failures | `REVIEW-UPLOAD-001-rereview-08-c-vitest.xml` — `9ad4aa291433832da7536c668bbc96ec5f31272d617429c0e18e90685e52c3c5` |
| `pnpm exec tsc --noEmit` from `frontend` | PASS, exit 0 | No standalone output artifact; generated untracked `frontend/pnpm-lock.yaml` was removed and all six submitted source hashes still matched. |
| `.venv\Scripts\python.exe .orchestration/reports/REVIEW-UPLOAD-001-rereview-08-web-wrapper.py` plus actual in-app browser inspection | PASS: production build 0; three source rows and three detail/original views independently inspected | Evidence JSON `659e99459156caeea0c6fdcf884ccfaf8e6718a580afff3ecfc704342f26bf65`; Web log `f6fdd82f259e1667a3e21846fd259992eb985fac0af5111812b3b27f584fc83b` |
| Reviewer receipt matrix against a fresh PostgreSQL 17 container with explicit repository `--basetemp` | PASS: 4 passed, 5.76s | Matrix `a9c412933f68f0d09b164dc6304e99648fab29415ae9edc9f588cfba787a1d93`; JUnit `0ccff437eabf5ab6fa8f39af4d00793525b488e42c079e479eb64e964554bbcf` |
| `git diff --check` | PASS, exit 0; only Git line-ending conversion warnings | No source mutation from the check. |

Review-only helper hashes:

- Web wrapper: `aee5cfaff75edf9410c86a0a375275446d29b1a662b592e989ccd84bcaf21c3c`
- Vitest config: `e72dd9492c19e88bfafb8f2c1d19a7fc1d61abd2361d6aaa5743fdbb269c254c`

Receipt-matrix setup history is retained accurately. The first launch did not collect because project venv lacked `rfc8785`; the bundled Python attempt did not collect because that runtime did not expose `pytest`; a subsequent attempt reached setup but the default user pytest temp root was inaccessible. The exact contract version `rfc8785==0.1.4` was added only to the untracked validation venv, and a repository-local `--basetemp` was used. The first body run produced 3 pass / 1 fail because the reviewer test incorrectly expected the service-layer `reserve_or_replay()` to throw the API-layer `DomainError`; inspection showed it correctly returned `ReservationState.IN_PROGRESS` without guessing rolled-back ownership. The reviewer-only assertion was corrected while preserving the persisted old-fence checks, and the final fresh-container run passed 4/4. No product file was changed to obtain a pass.

## Independent Web evidence

The evidence JSON is source-locked to the current harness and contract hashes and has zero mismatches across its nine-file source snapshot. It records a fresh project `c893b321-8b98-43f7-9e67-d3be66a7f481`, three screenshots and two durable receipts:

- agent `a0317c56-1412-49e3-96a4-2dad4c700abf`: source `agent`, non-null Client Upload ID, metadata version 1, 320x180, exact blue `SYNTHETIC AGENT QA` original, nested Korean/Japanese/Arabic/emoji/null/boolean/empty-string content;
- automation `32bb7d3d-d238-49f7-9137-78b9fa9c3850`: source `automation`, non-null Client Upload ID, metadata version 1, 320x180, exact green `SYNTHETIC AUTOMATION QA` original, nested Korean/Japanese/emoji and empty strings;
- manual `15ca291b-4091-44e1-a37f-76d6ff574507`: source `manual`, no Client Upload ID field in the detail UI, metadata version 1, 320x180, exact purple `SYNTHETIC MANUAL QA` original, Unicode/null/boolean/emoji/empty-string content.

The actual browser list showed exactly these three rows with filenames and context labels. The API/database/storage readback had three Screenshots, two COMPLETED receipts, three files and three exact content hashes. This is independent execution, not a relabeling of Owner 04's otherwise matching current-harness evidence.

## Finding dispositions

### R08-P2-PREFLIGHT-001 — RESOLVED

The corrected exact-byte content path was independently exercised within the fresh PostgreSQL Backend set. Normal, missing, length-changed and same-length corruption cases passed while preserving database, receipt and object state. The original evidence gap is closed.

### R08-P2-PREFLIGHT-002 — RESOLVED with explicit standby NOT_RUN limit

The full corrected receipt-aware reconciliation/F14 matrix passed independently against fresh PostgreSQL 17, including live/expired references, FAILED-before-delete, strict age, refreshed inventory, fresh-reference barriers, maintenance lock/writer assertion and storage/database fail-closed paths. The original gap is closed. A real recovery/standby server was not provisioned, so direct execution of the `pg_is_in_recovery()` branch remains NOT_RUN and is not labeled verified.

### R08-P2-PREFLIGHT-003 — RESOLVED

The populated 0002-to-0003 migration preservation case passed independently. Existing relationships, timestamps, nested Unicode metadata and referenced original bytes were preserved.

### R08-P2-REVIEW-004 — RESOLVED

Fresh PostgreSQL execution now covers concurrent first-insert arbitration, DB-clock expiry including equality, generation/token/candidate freshness, stale renew/finalize/FAILED denial, ambiguous first-insert and finalize commit/rollback outcomes, ambiguous takeover rollback without ownership guessing, five-second bounded lock timeout, exact recovery and atomic Screenshot/receipt completion. The added reviewer matrix passed 4/4, and the broader Backend set passed 90/90.

### R08-P2-REVIEW-005 — RESOLVED

The application now bounds four body-bearing requests per process and rejects excess work before receiving the body with `503 REQUEST_OVERLOADED` and `Retry-After: 1`. Completion, cancellation and downstream-error release paths passed independently in four dedicated tests.

### R08-P2-REVIEW-006 — RESOLVED

Linux mount classification now executes `/proc/self/mountinfo` logic and fails closed for network/unknown/unsupported filesystems. Independent Windows coverage and an actual Linux-container run both passed; each platform skipped only the other platform's classification case.

### R08-P2-REVIEW-007 — RESOLVED

Origin binding and runtime configuration now share the accepted/rejected host behavior. Independent F29 parity coverage passed, including bare `0x` and `0X`.

### R08-P2-REVIEW-008 — RESOLVED

The independently executed/current harness hash is `3d4952...69ee1c` before and after execution. The live run included real agent, automation and manual uploads plus empty-string and multilingual Unicode metadata. Actual browser inspection confirmed all three list/detail/original views.

### R08-P2-REVIEW-009 — RESOLVED

Finalize now holds PostgreSQL key-share locks on every scoped parent through Screenshot insertion and receipt completion. Independent two-connection barrier tests proved delete-waits/success and delete-first 404 plus same-generation fenced FAILED after confirmed rollback, while retaining the bounded lock behavior.

## Limits and non-blocking risks

- NOT_RUN: reconciliation against an actual PostgreSQL recovery/standby node. The primary guard is statically present; no claim of direct standby verification is made.
- The previous LOW renewal stop/join hardening observation remains non-blocking. No duplicate, corruption, permanent loss or fencing failure was established; current retry behavior remains bounded by the lease.
- The Linux pytest cache warning resulted from the deliberate read-only source mount and did not affect collection or execution.

## Cleanup and scope

Independent Web evidence records `web=terminated_exit_1` after the requested stop, `api=stopped`, random `database=dropped`, and `postgres_container=removed`. Post-run inspection found no `qa-review08-*`, `qa-upload-live-*`, or `qa-frontend-test-*` containers, no listeners on review Web/API/database ports, and no matching Web/API wrapper process. Every reviewer PostgreSQL container, including failed harness attempts, was removed in `finally` cleanup.

Reviewer changes are limited to this new report, its paired handoff, and isolated validation artifacts under `.orchestration/reports/`. The reviewer-only venv dependency is untracked. No product source, product test, contract, mobile proposal, owner artifact, PM YAML/state, shared/user database, user data, account/security setting, or deployment was changed. No IP connectivity check, Commit, Push or deployment occurred. Branch / commit: `null` / `null`.

## Model attribution and next action

PM requested `gpt-5.6-sol` with high reasoning for the parent review and server/queue lanes, and `gpt-5.6-sol` with medium reasoning for the Web lane. The runtime exposes no auditable actual model identifier, so actual model attribution remains `unverified`; no model identity is inferred from the request, and no unavailable support-agent result is used as acceptance evidence.

Next owner: PM01. Hash-verify this report and `.orchestration/handoffs/REVIEW-UPLOAD-001-rereview-08.md`, preserve the earlier CHANGES_REQUESTED review in history, record this new ACCEPTED result, promote AC-P2-01 through AC-P2-04 only through PM-owned state, and evaluate Phase 2 promotion under the project gates.
