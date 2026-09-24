# BACKEND-UPLOAD-001 — Backend upload execution plan

Date: 2026-09-25 KST

Owner: 03 Backend

Status: **execution plan complete; implementation BLOCKED**

Difficulty: **상** — durable project-scoped identity, PostgreSQL concurrency/fencing, ambiguous-commit recovery, and object/DB reconciliation affect persistent data across process restarts

Requested model: `gpt-5.6-sol` / `high`

Actual model: **unverified**; dispatch requested the value, but repository/runtime evidence does not prove the executing model

Branch / commit: null / null; no commit or push

## 1. Gate and evidence boundary

This report completes the read-only execution plan requested for Backend 03. It does not activate or implement `BACKEND-UPLOAD-001`.

Current authoritative repository state still records Phase 1 ACCEPTED/DONE, Phase 2 IN_PROGRESS, `ARCH-UPLOAD-001` READY_FOR_REVIEW, `REVIEW-ARCH-UPLOAD-001` READY, `BACKEND-UPLOAD-001` BLOCKED, and `AC-P2-01` through `AC-P2-04` NOT_RUN. The latest PM resumption instruction additionally reports that the Reviewer found an origin-binding MAJOR and selected CHANGES_REQUESTED, while the formal review report/handoff is still being filed. That expected correction is scoped to role 06 spool/config/ACK/CLI according to current evidence; no Backend API, manual-upload, receipt, or database change is inferred before the corrected contract revision is submitted and independently accepted.

Implementation may start only after all of the following are true:

1. the exact corrected `P2-UPLOAD-v1` revision and hashes are submitted;
2. `ARCH-UPLOAD-001` and `REVIEW-ARCH-UPLOAD-001` are ACCEPTED/DONE for that exact revision;
3. PM promotes Backend and uploader together and marks `BACKEND-UPLOAD-001` READY;
4. PM confirms Backend's exclusive `backend/` and `tests/backend/` claims and grants a serialized claim for each shared file, especially `pyproject.toml`;
5. Backend rechecks the accepted revision against this plan and revises only the affected plan portions before product work.

The evidence in this report is limited to source/document inspection and three read-only subagent analyses: additive migration/data preservation, receipt service/reconciliation/fault barriers, and Python 3.12 JCS/dependency handling. One service analysis initially hit a usage limit and was resumed successfully. No product source, test, migration, dependency, lock, database, service, PM YAML, `DECISIONS.md`, mobile proposal, or architecture contract was changed. No Phase 2 product test was run. Historical Phase 1 PASS results are not Phase 2 evidence.

## 2. Contract baseline to revalidate at activation

This plan targets submitted `P2-UPLOAD-v1` revision 1 unless the required corrected revision changes Backend sections 1–6 or 9–10. The Backend baseline is:

- retain the existing multipart route and unchanged manual behavior;
- reject any `Idempotency-Key` header with 422; agent identity is body `client_upload_id`, scoped by project;
- return 201 plus `Idempotency-Replayed: false` for the attempt that first completes, 200 plus `Idempotency-Replayed: true` for a completed replay, and the same Screenshot/Location for both;
- return 409 `IDEMPOTENCY_CONFLICT` for the same scoped identity with a different fingerprint;
- return 409 `UPLOAD_IN_PROGRESS` with a positive lease-derived `Retry-After` for an active attempt or fenced former owner;
- use RFC 8785 JCS bytes with UTF-16 key ordering, exact Unicode without normalization, and the specified finite binary64 numeric domain; persist those exact bytes in `canonical_request` with a 64 KiB maximum;
- use composite receipt identity `(project_id, client_upload_id)` without a redundant global receipt UUID;
- use `PROCESSING`, `COMPLETED`, and `FAILED`, a strictly increasing generation, a fresh random attempt token, and a fresh candidate Screenshot ID/key for every generation;
- use PostgreSQL `clock_timestamp()`, a default 60-second lease, renewal no later than every 20 seconds, and generation plus token in every renew/transition/finalize predicate;
- insert Screenshot and set receipt COMPLETED atomically in one short READ COMMITTED transaction;
- retain receipt identity indefinitely and never deduplicate by file hash alone;
- protect every Screenshot key and every PROCESSING candidate key during reconciliation, including expired/recoverable attempts; only exclusive maintenance may mark abandoned PROCESSING attempts FAILED and later consider their unreferenced old objects;
- agent workers never delete published final objects; manual compensation remains unchanged.

## 3. Exact planned file and function changes after activation

### Request, schemas, response, and errors

`backend/app/api/v1/screenshots.py`

- Keep `POST /projects/{project_id}/screenshots` and its two multipart parts.
- Replace the Phase 1-only validation branch with strict manual versus agent/automation metadata parsing. Any `Idempotency-Key` presence remains a 422 validation error.
- Convert `UploadOutcome` to HTTP: first completion 201/false, replay 200/true, both with identical Location; active/fenced outcome 409 plus computed positive Retry-After.
- Expand `ScreenshotFilter.source` to `manual|agent|automation` while preserving all current pagination/time/catalog predicates.
- Keep browser-managed multipart boundaries and all existing request/body limits.

`backend/app/schemas/screenshots.py`

- Preserve `ScreenshotUpload` as the closed manual request model.
- Add a closed `AgentScreenshotUpload` discriminated by `source in {agent,automation}`, requiring protocol/fingerprint version fields, UUIDv4 `client_upload_id`, supplied image facts/hash fields required by the accepted contract, and recursively validated metadata.
- Expand the read `Screenshot` schema to all three source values and `client_upload_id: UUID | None`; manual responses remain null.
- Keep defaults and missing-versus-null semantics exactly as the accepted contract specifies; do not normalize Unicode.

`backend/app/errors.py`, `backend/app/api/middleware.py`, `backend/app/main.py`

- Add stable mappings for `IDEMPOTENCY_CONFLICT` and `UPLOAD_IN_PROGRESS` and allow an error outcome to carry its exact `Retry-After`.
- Preserve the current 503 `Retry-After: 5`; do not let generic middleware replace the computed 409 value.
- Expose `Idempotency-Replayed` through CORS in addition to Location, X-Request-ID, and Retry-After without broadening origins or credentials.

`backend/openapi.json`, `backend/contract-examples.json`, `backend/README.md`

- Regenerate/document the accepted request variants, response statuses/headers, error codes, recovery behavior, and operator maintenance rules only after implementation tests pass.

### Models and migration

`backend/app/models/screenshots.py`

- Replace `ck_screenshot_phase1` with `ck_screenshot_source_client_upload`:
  `(source='manual' AND client_upload_id IS NULL) OR (source IN ('agent','automation') AND client_upload_id IS NOT NULL)`.
- Add partial unique `(project_id, client_upload_id) WHERE client_upload_id IS NOT NULL`.
- Add `UNIQUE(project_id, id, client_upload_id)` for the completed receipt identity FK.
- Keep global storage-key uniqueness, project/id uniqueness, file hash format, catalog FKs, and all manual rows unchanged. Do not make `file_hash` unique.

New `backend/app/models/upload_receipts.py`

- Define `UploadReceipt` with the exact columns and invariants in section 4 below.

`backend/app/models/__init__.py`

- Export `UploadReceipt` so Alembic metadata and runtime mappings include the new table.

New `backend/migrations/versions/0003_phase2_upload_receipts.py`

- Add the schema in one new migration whose `down_revision` is the applied `0002_phase1_domain` revision. Never edit `0001` or `0002`.

### Receipt repository and service

New `backend/app/repositories/upload_receipts.py`; repository functions flush/return rows and never commit or roll back:

- `sample_db_clock(session)` reads `clock_timestamp()` after the relevant receipt row lock.
- `insert_first_attempt(session, intent, fence)` uses composite-key `INSERT ... ON CONFLICT DO NOTHING RETURNING` with generation 1 and the preselected token/candidate values.
- `lock_receipt(session, project_id, client_upload_id)` uses `SELECT ... FOR UPDATE`.
- `take_over_locked(session, receipt, now, fence)` accepts only equal immutable intent and eligible FAILED or `lease_expires_at <= now`, then increments generation and installs a fresh token/candidate ID/key.
- `renew_locked(session, fence, now)` requires PROCESSING, matching fingerprint/generation/token, and `lease_expires_at > now`.
- `mark_failed_locked(session, fence, error_code)` updates only the still-owned PROCESSING generation.
- `insert_screenshot(session, attempt, facts)` and `complete_locked(session, receipt, screenshot)` support one atomic final transaction.
- `load_completed_screenshot(session, receipt)` treats an identity mismatch or missing committed target as an integrity incident.

New `backend/app/services/upload_receipts.py`:

- `build_canonical_intent(...)` validates the numeric/Unicode domain, emits exact JCS bytes, rejects duplicates before ordinary dict construction, and returns bytes plus lowercase SHA-256.
- `reserve_or_replay(factory, intent, fence_factory)` returns `OWNED`, `REPLAY`, `CONFLICT`, or `IN_PROGRESS`; existing immutable intent comparison precedes current contextual FK validation, while new/takeover attempts revalidate scoped references in the reservation transaction.
- `recover_reservation_commit(...)` uses a fresh primary READ COMMITTED transaction. For an ambiguous first insert it repeats composite-key INSERT...ON CONFLICT arbitration with the same attempted values before locking/reading the winner; it does not rely on `SELECT FOR UPDATE` to lock absence.
- `renew_attempt(...)` uses a separate short session/transaction.
- `finalize_attempt(...)` locks the receipt, samples DB time, verifies exact fence and unexpired lease, revalidates references, inserts Screenshot, sets COMPLETED, and commits once.
- `recover_finalize_commit(...)` locks/reads on a fresh primary connection and returns a committed Screenshot as a replay, re-finalizes only after confirmed rollback of the same generation, or fences a stale generation.
- `fail_after_known_rollback(...)` marks FAILED only after rollback is certain; ambiguous commits never trigger FAILED.
- `resolve_fenced_owner(...)` rereads the winner and returns a completed replay or a positive current Retry-After.
- Configure 5-second lock wait bounds for receipt transactions and map timeouts to 503/Retry-After 5.

`backend/app/services/screenshots.py`

- Rename/preserve the present `upload(...)` flow as `upload_manual(...)`; its known-rollback published-object compensation remains manual-only.
- Add `upload_agent(...)`: stage/inspect/assert facts, canonicalize, reserve, publish only the owned generation candidate, stop/join renewal, finalize, and return `UploadOutcome`.
- Add `verify_candidate_object(...)` for same-generation `ObjectExists`; require exact hash and size, otherwise alert and return STORAGE_UNAVAILABLE without overwrite.
- Add an injected `LeaseKeeper` using its own SessionFactory, renewing at no more than 20-second intervals. Any failed/unknown renewal blocks finalization and preserves the object.
- Add an injected no-op `UploadFaultInjector.hit(point, context)` at the barriers in section 5. Avoid a production global commit monkeypatch seam.
- Never call the current `cleanup()` for an agent-published object. Only the private staging token is discarded after its I/O ends.

`backend/app/storage/base.py`, `backend/app/storage/local.py`

- Add a narrowly typed exact-object verification operation only if the current open/read/stat API cannot atomically provide the facts required by `verify_candidate_object`; preserve no-overwrite publication and path protections.

### Reconciliation

Refactor `backend/app/maintenance/reconcile_storage.py` into:

- `assert_exclusive_primary(session, writers_stopped)`;
- `inventory_db_references(session)`, returning all Screenshot keys and all PROCESSING candidate keys regardless of lease expiry;
- `inventory_storage_complete(storage)`;
- `mark_abandoned_processing(factory)`, available only in apply mode under verified exclusivity and using locked fenced transitions;
- `classify_candidates(...)`, where age alone never grants deletion;
- `recheck_delete_eligibility(factory, key)`, querying a fresh primary snapshot immediately before deletion for both Screenshot and PROCESSING references;
- `delete_exact_candidate(storage, key)`.

Dry-run reports `would_mark_failed` and `eligible_after_failed` without state changes. Apply first commits explicit abandoned PROCESSING to FAILED, then considers only unreferenced FAILED/obsolete objects older than 24 hours. Any incomplete inventory or DB/recheck uncertainty stops deletion. Missing or mismatched referenced originals remain reported and preserved.

## 4. Exact additive `0003` order and constraints

Use ordinary transactional PostgreSQL DDL; do not silently introduce `CONCURRENTLY` or a new extension.

1. Add Screenshot `UNIQUE(project_id,id,client_upload_id)` so the later three-column FK has a target.
2. Add `ck_screenshot_source_client_upload` as NOT VALID, validate it against existing rows, and keep the old check until validation succeeds.
3. Add unique partial index `uq_screenshots_project_client_upload_id` on `(project_id,client_upload_id) WHERE client_upload_id IS NOT NULL`.
4. Create `upload_receipts` with:
   - `project_id UUID NOT NULL`, `client_upload_id UUID NOT NULL`;
   - `fingerprint_version INTEGER NOT NULL`, `upload_protocol_version INTEGER NOT NULL`;
   - `request_fingerprint CHAR(64) NOT NULL`, `canonical_request BYTEA NOT NULL`;
   - `state VARCHAR(16) NOT NULL`;
   - `attempt_generation BIGINT NOT NULL`, `attempt_token UUID NOT NULL`;
   - `candidate_screenshot_id UUID NOT NULL`, `candidate_storage_key TEXT NOT NULL`;
   - `screenshot_id UUID NULL`, `lease_expires_at TIMESTAMPTZ NULL`;
   - `last_error_code VARCHAR(64) NULL`;
   - `created_at` and `updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()`.
5. Add receipt `PRIMARY KEY(project_id,client_upload_id)`, `UNIQUE(candidate_storage_key)`, and uniqueness for non-null `screenshot_id`.
6. Add checks:
   - both protocol versions equal 1;
   - fingerprint matches `^[0-9a-f]{64}$`;
   - `octet_length(canonical_request) BETWEEN 1 AND 65536`;
   - state is PROCESSING, COMPLETED, or FAILED;
   - `attempt_generation >= 1`;
   - `client_upload_id` and `attempt_token` are canonical UUIDv4 values;
   - candidate key equals `objects/{project_id}/{candidate_screenshot_id}.png` or `.jpg`;
   - PROCESSING has null `screenshot_id` and non-null lease;
   - FAILED has null `screenshot_id` and null lease;
   - COMPLETED has `screenshot_id=candidate_screenshot_id`, null lease, and null error;
   - non-null error codes have length 1–64 and the accepted safe-code grammar.
7. Add restrictive FKs in this order:
   - `project_id -> projects(id) ON DELETE RESTRICT`;
   - `(project_id,screenshot_id) -> screenshots(project_id,id) ON DELETE RESTRICT`;
   - `(project_id,screenshot_id,client_upload_id) -> screenshots(project_id,id,client_upload_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED`.
8. Add `ix_upload_receipts_processing_lease_expires_at` on `lease_expires_at WHERE state='PROCESSING'` and `ix_upload_receipts_project_id`.
9. Drop `ck_screenshot_phase1` only after the replacement check validates.

Do not backfill historical manual Screenshots or create synthetic receipts. `SHA256(canonical_request)==request_fingerprint` and immutable intent columns are verified by the receipt service before every use and by tests; no unapproved `pgcrypto` dependency or update trigger is added. Repository update methods must never rewrite project/client identity, versions, canonical bytes, fingerprint, or created time.

The populated `0002 -> 0003` fixture must compare before/after row count; every Screenshot and catalog ID; source/null client ID; filename/uploaded time; storage key/hash/MIME/size/dimensions; metadata version and complete JSONB/Unicode; original object bytes and recomputed hash; duplicate manual file hashes; and zero receipt rows. Fresh head upgrade and metadata parity are required. Downgrade/re-upgrade runs only on a disposable DB and is never a user-data procedure.

## 5. Planned test files, cases, and fault barriers

All concurrency cases use separate SQLAlchemy Sessions/connections against real disposable PostgreSQL. Restart cases recreate engine/session/service objects while reusing the same database and storage. Time-based cases set controlled DB values/barriers rather than sleeping.

`tests/backend/test_migrations_storage.py`

- update `test_fresh_migration_roundtrip_and_metadata` for the receipt table;
- `test_additive_0002_to_0003_preserves_manual_rows_and_objects`;
- `test_additive_0003_does_not_backfill_manual_receipts`;
- `test_additive_0003_preserves_duplicate_manual_file_hashes_and_null_client_ids`;
- `test_0003_schema_has_expected_constraints_fks_and_partial_indexes`;
- `test_0003_downgrade_to_0002_in_disposable_database`.

New `tests/backend/test_upload_receipt_constraints.py`

- valid PROCESSING/FAILED/COMPLETED shapes;
- reject invalid version/hash/generation/canonical-size/state/key/UUID combinations;
- completed receipt requires the same project, Screenshot, and client ID;
- restrictive deletes, candidate/completed uniqueness, project-scoped identity, Screenshot partial uniqueness;
- equal file hash/canonical request under different client IDs remains distinct.

New `tests/backend/test_upload_receipts_service.py` and `test_upload_receipts_concurrency.py`

- same K/same fingerprint; same K/different fingerprint; digest-equal but canonical-byte-different collision; same bytes/different K; same K in different projects;
- `test_concurrent_same_intent_has_one_generation_one_owner`;
- `test_concurrent_different_fingerprint_conflicts_without_mutation`;
- `test_exact_lease_expiry_allows_single_takeover` including equality-as-expired;
- `test_stale_generation_cannot_renew_finalize_or_mark_failed`;
- `test_delayed_stale_publish_uses_old_generation_key_and_cannot_harm_winner`;
- `test_lock_timeout_returns_503_retry_after_5`.

New `tests/backend/test_screenshots_agent.py` and `test_upload_response_contract.py`

- first 201/false and completed 200/true retain the same ID, Location, uploaded_at, hash, source, client ID, and full context;
- active lease returns 409 with positive computed Retry-After; conflict 409 has no Retry-After;
- Idempotency-Key is always 422;
- no deduplication by hash; source/project scoping; agent/automation pair validation;
- same-generation exact object continues, mismatch returns STORAGE_UNAVAILABLE without overwrite;
- completed missing/mismatched object remains preserved and content returns 503;
- response-send loss replays the committed result.

Existing `tests/backend/test_screenshots.py`

- retain all current manual cases and add `test_manual_duplicate_uploads_still_create_distinct_screenshots` and `test_manual_upload_remains_201_without_idempotency_replayed_header`;
- keep manual agent-only-field rejection and known-rollback object compensation.

New `tests/backend/test_reconcile_upload_receipts.py`

- PROCESSING candidates are protected whether active or expired;
- abandoned PROCESSING is explicitly FAILED before eligibility;
- FAILED/obsolete candidates require age greater than 24 hours and no Screenshot/PROCESSING reference;
- partial inventory or primary recheck failure deletes nothing further;
- exact fresh recheck is required for every delete.

Fault injector points and required cases:

| Barrier | Required assertion/test |
| --- | --- |
| `AFTER_STAGE_BEFORE_RESERVE` | no receipt or published object |
| `RESERVE_BEFORE_COMMIT` | known rollback publishes nothing |
| `RESERVE_AFTER_COMMIT_BEFORE_PUBLISH` | restart resumes the same confirmed generation candidate |
| `RESERVE_COMMIT_OUTCOME_UNKNOWN` | first-insert unique arbitration; ambiguous takeover exact-fence recovery |
| `RENEW_BEFORE_COMMIT` / `RENEW_COMMIT_OUTCOME_UNKNOWN` | renewal failure/uncertainty blocks finalize and preserves object |
| `AFTER_PUBLISH_BEFORE_FINALIZE` | no Screenshot, candidate retained |
| `FINALIZE_BEFORE_COMMIT` | known rollback may fail only the owned generation |
| after Screenshot insert before receipt update | transaction rollback leaves neither durable partial result |
| `FINALIZE_COMMIT_OUTCOME_UNKNOWN` | committed returns replay; confirmed rollback re-finalizes without duplicate |
| `AFTER_FINALIZE_COMMIT_BEFORE_RESPONSE` | retry returns same ID/time as 200 replay |
| `BEFORE_FAILED_COMMIT` | bookkeeping failure leaves recoverable PROCESSING |
| `RECONCILE_AFTER_INVENTORY` | incomplete/failed inventory deletes nothing |
| `RECONCILE_AFTER_ABANDONED_FAILED_COMMIT` | candidate becomes classifiable only after durable FAILED |
| `RECONCILE_BEFORE_DELETE_RECHECK` | primary failure preserves candidate |
| `RECONCILE_AFTER_RECHECK_BEFORE_DELETE` | only the exact rechecked orphan is deleted |

## 6. JCS dependency and shared-file sequence

No package/version is selected by current evidence. `pyproject.toml` requires Python `>=3.12,<3.13`; `backend/requirements.lock`, the inspected virtual environment metadata, and local package cache contain no established RFC 8785 implementation. Package name, version, Python 3.12 compatibility, artifacts, license, maintenance, and hashes therefore remain **unverified**. This uncertainty does not block submission of this plan, but it blocks implementation dependency selection.

After contract acceptance and PM activation, perform a bounded dependency-resolution spike before changing shared files. Record exact package/version, release/source URLs, SPDX license, maintenance state, `Requires-Python`, dependency tree, Windows/Linux artifacts and hashes. Reject a candidate that silently uses Python code-point ordering, loses duplicate keys, accepts NaN/infinity/nonzero underflow/unsafe integrals, or requires an unplanned native toolchain.

The acceptance suite on CPython 3.12 Windows and Linux must compare exact canonical UTF-8 bytes and SHA-256 for:

- official RFC 8785 vectors;
- UTF-16 ordering where U+1F600 sorts before U+E000, including nested keys;
- `-0 -> 0`, and `1`, `1.0`, `1e0` equivalence;
- finite binary64 boundaries, adjacent values, overflow, nonzero underflow such as `1e-4000`, and safe integral limits;
- root/nested/escaped-equivalent duplicate-key rejection before dict construction;
- exact CJK, supplementary emoji, variation selectors, and combining sequences, with composed and decomposed forms remaining distinct;
- missing versus null, array order, boolean versus number, defaults, filename sanitization, and reordered-object equality;
- PostgreSQL JSONB roundtrip through the real psycopg/SQLAlchemy path, preserving each binary64 meaning and Unicode while stored `canonical_request BYTEA` exactly matches pre-insert bytes;
- malformed inputs returning 422 before receipt creation, JSONB write, or publication.

Shared-file sequence:

1. PM grants a serialized claim on `pyproject.toml` after the spike is reviewed.
2. Backend 03 adds the selected direct runtime dependency with its reviewed compatible bound, preserving all existing Backend/dev entries.
3. Backend 03 regenerates `backend/requirements.lock` with `--require-hashes`, exact transitive versions, and approved Windows/Linux artifacts; clean hash-required installs must pass on both platforms.
4. Role 06 pins the same accepted JCS implementation/version in its separate `agent/screenshot_upload/requirements.lock`. Backend's lock is never repurposed for uploader installation.
5. Coordinate any role 06 runtime `httpx`/packaging edit to `pyproject.toml` within the same PM-managed serial window; each owner changes only its allocated content.

## 7. Parallel implementation slices after PM activation

Before parallel work, freeze shared dataclasses/protocols (`CanonicalIntent`, `AttemptFence`, `ReservationOutcome`, `CompletionOutcome`, fault-point names) and the accepted migration/model names. Use disjoint write sets:

1. **Migration/model — 상, Sol/high**: `backend/app/models/screenshots.py`, new `models/upload_receipts.py`, `models/__init__.py`, new `0003`, `test_migrations_storage.py`, new `test_upload_receipt_constraints.py`.
2. **Receipt/fence core — 상, Sol/high**: new `repositories/upload_receipts.py`, new `services/upload_receipts.py`, `test_upload_receipts_service.py`, `test_upload_receipts_concurrency.py`.
3. **Agent orchestration/storage — 상, Sol/high**: `services/screenshots.py`, storage protocol/local implementation if required, `test_screenshots_agent.py`.
4. **Reconciliation — 중, Sol/medium**: `maintenance/reconcile_storage.py`, `test_reconcile_upload_receipts.py`; consume model/public query contracts without editing slice 2.
5. **HTTP/schema/contract exports — 중, Sol/medium**: API router, screenshot schemas, errors/middleware/main, `test_upload_response_contract.py`; regenerate OpenAPI/examples/docs only after integration.
6. **JCS spike/lock — 중, Sol/medium**: dependency evidence and conformance fixture work; `pyproject.toml` and locks remain serial PM-claimed changes.

Overlapping integration files are sequential: `models/__init__.py`, `services/screenshots.py`, `schemas/screenshots.py`, `pyproject.toml`, generated contract exports, and existing manual regression files. The parent/owner reviews every slice, applies the migration on disposable PostgreSQL, runs targeted tests, then the complete Backend suite and accepted Phase 2 integration checks. Requested subagent models are recorded separately from actual models; actual models remain unverified unless dispatch metadata proves them.

## 8. Planned verification and remaining risks

Current completed evidence:

- gate/status, role prompt, submitted contract revision 1, author handoff/report, current Backend seams, migration history, dependency files, and prior preparation were inspected;
- three read-only delegated analyses were recovered and integrated;
- this plan was checked for scope and repository whitespace only after writing.

Future verification, all currently NOT_RUN:

- migration fresh/additive/downgrade-disposable and metadata parity;
- real PostgreSQL concurrency, lock timeout, generation fencing, DB-clock lease, ambiguous reserve/finalize commit, and restart;
- object publication mismatch/unknown outcome, response loss, and receipt-aware exclusive maintenance;
- full JCS/cross-platform/hash-required-install/JSONB roundtrip suite;
- API/manual regressions, generated OpenAPI/examples, complete Backend tests, agent-to-Backend integration, and Web evidence for AC-P2-04.

Material risks at activation are: the corrected contract may change a Backend section; no JCS package is yet evidenced; first-insert absence cannot be serialized by SELECT alone; a renewal worker can race finalize unless stopped/joined; the current `cleanup()` would be destructive if reused for agent objects; current reconciliation protects only Screenshot keys; and migration constraints/FKs can lock durable tables. These risks are addressed by the activation recheck, unique-key arbitration, explicit fence predicates, manual-only compensation, PROCESSING protection, transactional additive migration, and the fault tests above.

Submission of this report does not satisfy any Phase 2 AC and does not request implementation review. Next owner is PM 01 to record the plan while keeping `BACKEND-UPLOAD-001` BLOCKED until corrected-contract independent acceptance and explicit READY/file claims.
