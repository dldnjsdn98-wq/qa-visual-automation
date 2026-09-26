# PREP-BACKEND-OCR-001 — Backend OCR persistence/API preparation

Date: 2026-09-25 KST  
Owner: 03 Backend  
Status: preparation complete; implementation remains blocked  
Branch / commit: null / null  

## Goal, scope and gate

This is a read-only inventory of the existing Backend catalog, Screenshot, upload-receipt, API, migration and PostgreSQL transaction boundaries needed by the Phase 3 OCR/verification contract. The only files created are this report and the matching handoff. No product source, migration, dependency, PM state, architecture contract, worker, Frontend, mobile or Phase 4 file was changed.

Phase 2 is ACCEPTED with AC-P2-01 through AC-P2-04 PASS. `PREP-BACKEND-OCR-001` is READY under `.orchestration/handoffs/PHASE-3-activation-01.md`; AC-P3-01 through AC-P3-04 remain `NOT_RUN`. `BACKEND-OCR-001` remains BLOCKED until the exact `ARCH-OCR-001` revision is independently accepted by `REVIEW-ARCH-OCR-001` and PM grants implementation file ownership. This preparation neither approves the contract nor activates implementation.

## Current inventory and Phase 2 invariants

There is no OCR engine integration, OCR job/outbox, OCR result/region, verification result/item, expected-input snapshot, result history, worker transport, Phase 3 migration, route or OCR dependency in the current Backend. Current model registration contains the catalog, strings, Screenshot and UploadReceipt only (`backend/app/models/__init__.py:1`). Runtime dependencies remain FastAPI, SQLAlchemy, Alembic, psycopg, Pillow, multipart and JCS centered (`pyproject.toml:10`).

| Boundary | Current behavior and exact source | Phase 3 preservation/input |
| --- | --- | --- |
| Catalog scope | Project/Build/Locale/Category/Situation are project-scoped with restrictive relationships (`backend/app/models/catalog.py:26`). | New references must be project-scoped; current rows and delete semantics remain intact. |
| String catalog | `StringKey`, `StringEntry`, and ordered `SituationExpectedString` are separate (`backend/app/models/strings.py:9`, `:16`, `:31`). | Copy the selected values into an immutable snapshot; do not turn mutable catalog rows into result history. |
| Current resolver | One join returns position, key ID/string ID, optional entry ID/text and `present`/`missing`; `text=""` remains present (`backend/app/services/expected_strings.py:41-45`). It returns `catalog_mode="current"`. | Retry must never resolve this live endpoint again. Missing and empty remain distinct. |
| Screenshot | Immutable source identity includes project/build/locale/category/situation, object hash/key, media facts, dimensions, metadata and optional client upload identity (`backend/app/models/screenshots.py:10`). | Job/result references the exact `(project_id, screenshot_id)` and frozen hash/dimensions; no Screenshot mutation. |
| UploadReceipt | Upload-only PROCESSING/COMPLETED/FAILED receipt with generation/token/lease (`backend/app/models/upload_receipts.py:11`, `:35-60`). | Preserve every receipt and its semantics. It is not an OCR job, attempt, identity or result. |
| Durable transaction principles | Primary DB check, `READ COMMITTED`, `lock_timeout='5s'`, DB `clock_timestamp()`, row locks, generation/token fencing (`backend/app/repositories/upload_receipts.py:14-29`, `:56-78`). | Reuse principles in a separate OCR repository. Five seconds is lock wait, not OCR runtime or lease duration. |
| Ambiguous completion | Existing service recovers with a fresh primary transaction and only records failure after confirmed rollback (`backend/app/services/upload_receipts.py:185`, `:254`, `:289`, `:331`). | Claim/finalize acknowledgement loss requires equivalent identity/fence recovery; never guess FAILED. |
| API composition | v1 modules are included by `backend/app/api/v1/router.py:3-7`; the app includes that router at `backend/app/main.py:14`. | Add separate scoped resources after contract acceptance. |
| Errors/pages | Shared errors map integrity/unavailable cases (`backend/app/errors.py:13`); `Page[T]` is `items,total,limit,offset` (`backend/app/schemas/common.py:43-51`). | Preserve the envelope and count/page consistency; define OCR-specific domain codes. |
| Existing expected API | Screenshot expected strings are live current catalog, complete ordered mapping (`docs/architecture/api-contract.md:118-129`). | Keep this endpoint unchanged; historical verification reads frozen data only. |
| Phase 3 architecture invariant | Durable job, OCR regions, selected expected snapshot, matching and verification results; versions/coordinates/confidence/scores/errors; append-only reruns (`docs/architecture/data-flow.md:58-60`, `docs/architecture/domain-model.md:54-58`). | Processing status is separate from quality status and historical inputs/results never change. |

Migration history is `0001_bootstrap` → `0002_phase1_domain` → `0003_phase2_upload_receipts` (`backend/migrations/versions/0003_phase2_upload_receipts.py:3,12`). A future Phase 3 migration must be additive `0004` after `0003`. It must preserve every existing Screenshot and UploadReceipt row, UUID, timestamp, constraint, fence, object reference and original byte. It must not edit historical migrations, create synthetic OCR jobs for old Screenshots, or backfill OCR results unless an independently accepted contract explicitly requires that change.

Phase 2 invariants to retain include Screenshot source/client-ID pairing and partial `(project_id, client_upload_id)` uniqueness (`0003_phase2_upload_receipts.py:24-31`), the durable receipt identity and exact completed-Screenshot FK (`:57-61`), protocol/fingerprint/candidate/fence checks (`:63-73`) and processing/inventory indexes (`:74-80`).

## Proposed persistence boundaries pending Architect02 decision

The following is contract input, not an approved schema.

| Proposed boundary | Required responsibility |
| --- | --- |
| Verification run / OCR job | Project-scoped run identity, exact Screenshot identity/hash, enqueue idempotency, processing state, retry budget, lease, generation/token fence, timestamps and bounded processing error. |
| Attempt or event history | Append-only claim/retry/crash/failure evidence where required; current mutable job state must not erase prior terminal attempts. |
| Expected snapshot | One immutable snapshot per user-created run, including project/build/locale/situation and the exact config/version used. |
| Expected snapshot item | Ordered `position`, copied StringKey ID/string ID, copied optional entry ID, copied text and explicit `present`/`missing`. Copied historical IDs/values should not use restrictive FKs to mutable translation rows. |
| OCR result and regions | Append-only result generation with engine/model/language/preprocess/config versions, source dimensions/orientation, OCR text, original decoded pixel coordinates, reading order and confidence `[0,1]`. |
| Verification result and items | Link the exact OCR result and snapshot; preserve normalization/matching version, thresholds, expected/observed text, method, score `[0,100]`, and separate quality/unverified semantics. |

The preliminary Architect02 proposal received during this preparation is compatible with the inventory: explicit `POST` of a screenshot verification run; project-scoped UUIDv4 `client_run_id` as same-ID idempotency identity; one `REPEATABLE READ` creation transaction that copies Screenshot identity/hash, current expected mapping/translations and config into immutable rows and atomically creates a PENDING job; retries reuse that snapshot; a user rerun uses a new ID and new snapshot; DB-primary claim/lease/generation/token fencing; and one transaction to append OCR/verification results and finalize the job. Role05 supplies an adapter to a Backend-owned durable worker loop and has no direct DB ownership.

No direct mismatch was found. Two details still require exact contract wording:

1. Under PostgreSQL `REPEATABLE READ`, define the snapshot instant as the transaction snapshot established by its first data query, not loosely as commit time. Use a single joined catalog read or specify how multiple reads cannot form a mixed snapshot.
2. Copied catalog IDs/values should not restrict future mutable catalog deletion, but the job must retain a project-scoped restrictive reference to the exact Screenshot or otherwise state how historical source evidence survives Screenshot/project deletion. There must be no fallback to current catalog when copied snapshot data is absent or corrupt.

The frozen Screenshot input should also copy the object identity and facts used by the worker (`storage_key`, hash, media type, size, width/height), catalog/context IDs, metadata version/data and any mutable display values that historical UI must reproduce. The worker should open the source once and verify the length/hash of the same bytes passed to OCR; a later second open creates a storage TOCTOU gap. `INPUT_STORAGE_UNAVAILABLE` and `INPUT_HASH_MISMATCH` are processing errors, not quality FAIL.

The execution profile must resolve aliases such as `latest` before commit and freeze concrete engine/package, detection/recognition model ID/revision/artifact digest, ordered language packs, preprocessing/coordinate schema, canonical config/digest, matcher/normalization versions and thresholds. The current resolver's `translation_status` remains `present` for `text=""`; the Phase 3 contract must decide whether the snapshot preserves that pair plus exact text or introduces an explicit `empty` input classification. Either design must keep missing, empty and nonempty distinguishable without changing the existing endpoint.

## Job, recovery and status questions

Suggested processing state machine is `PENDING → RUNNING → SUCCEEDED`, with retryable failures moving to `RETRY_WAIT` and terminal/exhausted failures to `FAILED`. An expired RUNNING lease may be reclaimed with a strictly higher generation and new token. This is a proposal only.

- Automatic retry keeps job ID, immutable snapshot and config; a user rerun creates a new `client_run_id`, job, snapshot and append-only result lineage.
- OCR execution may occur more than once. The guarantee is one atomic finalize by the current fence, not exactly-once computation.
- State, job ID, generation and token must all match for renew/finalize/fail. Equality at DB lease expiry must be defined. A stale owner must not revive or append results.
- OCR and matching work occurs outside short DB transactions. Result append and job success transition occur together.
- A lost claim/finalize response is recovered from a fresh primary transaction by durable request identity/fence. Absence after an ambiguous commit is not proof of rollback.
- Processing success and quality FAIL may coexist. Worker failure, missing translation, empty expected text, empty OCR text and zero OCR regions must remain distinguishable and must not be collapsed into PASS/REVIEW/FAIL.

Architect02/PM must resolve these exact points in the reviewed contract:

1. Confirm `client_run_id` scope, UUID canonicalization, retention and same-ID/different-payload conflict rule.
2. Confirm explicit POST as the only initial trigger and whether an outbox is still needed for the Backend worker loop.
3. Define exact processing states, retryable versus terminal error codes, backoff, attempt/time ceilings and crash accounting.
4. Define lease/renewal/runtime values, DB-clock equality, lock/statement/transaction bounds and generation overflow behavior.
5. Define ambiguous enqueue, claim, renew and finalize commit recovery, including whether durable claim-request identity is required.
6. Define immutable retry fields and the exact rerun lineage and new-snapshot behavior.
7. Define the creation transaction's first-query snapshot boundary and how concurrent mapping/text changes or deletes behave.
8. Confirm copied snapshot columns: key ID, string ID, position, optional entry ID, text and translation status; state whether copied IDs have no mutable-catalog FK.
9. Define separate representations for missing translation, empty expected text, empty OCR output, zero regions and worker/engine failure.
10. Confirm original decoded pixel integer coordinate system, origin, rotation transform, bounds and source dimension semantics.
11. Enumerate engine/model/language/preprocess/normalization/matching/config/threshold version fields and digests.
12. Confirm candidate boundaries exactly: score `>=95` PASS, `>=85 and <95` REVIEW, `<85` FAIL, with no fabricated score for unverified/error cases.
13. Define create/status/history/result API routes, first/replay responses, `Location`/`Retry-After`, page order and Web fallback for unknown states.
14. Define Screenshot/project/catalog retention and FK policies so deletes cannot rewrite or orphan historical evidence.
15. Decide whether failure history is immutable attempt/event rows or current job fields plus immutable result generations.
16. Define cleanup/reaper behavior and whether any job, snapshot or result deletion is permitted.
17. Fix Role03/Role05 ownership: Backend owns durable DB job, claim/lease/fence, snapshot, validation and persistence; Worker05 owns OCR/matching computation and cannot mutate catalog, Screenshot or UploadReceipt.
18. Require fail-closed behavior when snapshot rows/config are missing, malformed or inconsistent; never silently use live catalog.

Also state whether append-only behavior is enforced only by service permissions or by database triggers/privileges, whether mapping position gaps are accepted or rejected, and whether mutable Build/Locale/Category/Situation display values must be copied for historical UI reproduction.

## Proposed API and file claims

Prefer a separate scoped verification-run resource, matching Architect02's preliminary naming, rather than embedding changing arrays in Screenshot/StringEntry (`docs/architecture/api-contract.md:171`). Candidate public routes are:

- `POST /api/v1/projects/{project_id}/screenshots/{screenshot_id}/verification-runs`
- `GET /api/v1/projects/{project_id}/verification-runs/{run_id}`
- `GET /api/v1/projects/{project_id}/screenshots/{screenshot_id}/verification-runs?limit=&offset=`
- `GET /api/v1/projects/{project_id}/ocr-results/{result_id}`
- `GET /api/v1/projects/{project_id}/verification-results/{result_id}`

The exact worker claim/renew/complete transport must be a separate trust boundary and is still a contract decision. Existing Screenshot expected strings remains current-catalog behavior.

After acceptance and PM ownership, likely Backend03 files are new OCR model/schema/repository/service/router modules, model/router exports, additive `backend/migrations/versions/0004_*.py`, and new `tests/backend/test_ocr_*.py`. Existing `backend/app/main.py`, errors/common/middleware and migration tests should change only if required. `pyproject.toml` and the Backend lock remain Backend03's sole-edit dependency boundary after approval. No claim is made here over `docs/architecture`, `worker/`, `tests/ocr`, Frontend, mobile or PM YAML/state.

## Future isolated validation matrix — all NOT_RUN

| Planned test | Required evidence |
| --- | --- |
| Fresh migration/model parity | Fresh `head`, exact constraints/indexes/FKs and ORM parity. |
| Populated `0003 → 0004` | Preserve all catalog/Screenshot/UploadReceipt fields, Unicode/empty/null JSON, fences and exact object bytes; add only Phase 3 rows/tables. |
| Downgrade/re-upgrade | Disposable database only; no shared/user DB; preserve allowed history according to contract. |
| Snapshot concurrency | Separate connections and barriers around run creation versus mapping replacement, StringEntry update/delete; no mixed or later-mutated historical snapshot. |
| Enqueue idempotency | Concurrent same ID/same payload returns one run/snapshot; same ID/different payload conflicts; lost response replays without recapture. |
| Claim/lease/fence | Two workers, DB-clock before/equal/after expiry, stale renew/finalize/fail denial, strict generation increase and bounded lock/deadlock behavior. |
| Atomic finalize | Crash before/after result append and COMMIT acknowledgement loss produce all-or-nothing current-fence result/job state. |
| History/status semantics | Retry and rerun append; missing/empty/no-region/engine-failure remain distinct; processing and quality state remain separate. |
| Scope/API | Cross-project links rejected by DB, list/detail/history scope, ordering, page total/items snapshot and error envelope. |
| Original preservation | Job success/failure/retry/rerun never changes Screenshot, UploadReceipt or original object hash/bytes. |

Use the existing isolated random PostgreSQL fixture (`tests/backend/conftest.py:25`), populated migration pattern (`tests/backend/test_migrations_storage.py:44`), two-connection barriers (`tests/backend/test_concurrency_contract.py:25`, `tests/backend/test_finalize_reference_lock.py:115`) and deterministic phase fault seam (`tests/backend/test_finalize_reference_lock.py:22`). These are reuse patterns, not executed Phase 3 evidence.

## Actual inspection, evidence and model routing

Environment: `C:\Dev\qa-visual-automation`, Windows/PowerShell, 2026-09-25 KST. Read-only commands used were PowerShell `Get-Content` over the named orchestration/role/source files; focused `Select-String` line scans over models/services/repositories/routes/migrations/architecture; `git status --short`; and SHA-256 inspection of Phase 2/activation evidence by the hygiene subagent. Results: the gate/inventory above was confirmed; the shared working tree already contained retained modifications and untracked files, all preserved. No product command mutated the tree.

| Difficulty | Requested subagent | Scope | Result use | Actual model |
| --- | --- | --- | --- | --- |
| 최상 | `gpt-6-astra` / medium | durable job/lease/fence/recovery risks | design questions and fault matrix | unverified |
| 상 | `gpt-5.6-sol` / high | immutable snapshot/result history | snapshot fields, TOCTOU, retention and profile risks | unverified |
| 중 | `gpt-5.6-sol` / medium | current model/API/migration/dependency inventory | source inventory and file claims | unverified |
| 하 | `gpt-5.6-terra` / high | isolated PostgreSQL/fault seam plan | future test matrix | unverified |
| 최하 | `gpt-5.6-luna` / high | evidence and submission hygiene | gates and evidence hashes | unverified |

Requested routing is recorded separately from actual identity. The available execution output did not provide auditable model telemetry, so no actual model is claimed. Subagent findings are planning inputs, not independent acceptance.

Evidence hashes rechecked during preparation: Phase 2 acceptance handoff `17c524e2bfcad078080e15f04d53dd9713e0c281a396e13f048b1b64b6f1358c`; Reviewer08 report `3802b8b0c510f400dcc88ddd79c70c0e15be3fa3568faae2fd05eb253c19d290`; Reviewer08 handoff `4b32a0758e793ba3426e4e95d50e2f3478d52c165dde3c8b677a6fc87840f934`; Phase 3 activation handoff `4c502c3abdec9a51b953c3c71d0f18a0b68a01613cd42f791b7a715dd9ed6588`.

Tests: pytest `NOT_RUN`; PostgreSQL/migration `NOT_RUN`; OCR engine/worker `NOT_RUN`; API/OpenAPI runtime `NOT_RUN`; dependency installation `NOT_RUN`. These were not required or authorized for this read-only preparation. No Phase 3 PASS is claimed.

## Completion

The preparation deliverable is complete when this report and its handoff are hashed and delivered to PM01 and Architect02. Product implementation remains blocked. Phase 4/mobile scope remains inactive and unchanged. No commit, push, deployment, database mutation/reset, user-data deletion, account/security change or IP check occurred.
