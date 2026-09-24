# PREP-BACKEND-UPLOAD-001 — Backend upload impact and migration preparation

Date: 2026-09-13 KST  
Owner: 03 Backend  
Status: preparation complete; PM/Architect consultation requested  
Difficulty: 중 — bounded read-only mapping and additive migration/test-seam proposal; no persistence implementation or data change  
Requested model: `gpt-5.6-sol` / `medium`  
Actual model: 실제 적용 미확인 (dispatch requested the value; this task has no execution metadata proving the active model)  
Branch / commit: null / null; inspected HEAD `811b1e36199d424d83930f3381c7d71e537bc7d6`, while the shared working tree contains retained uncommitted/untracked Phase 1 work

## Entry, scope and evidence boundary

Latest repository state is authoritative. `.orchestration/PROJECT_STATE.yaml` records Phase 1 ACCEPTED/DONE and Phase 2 IN_PROGRESS for contract/preparation. `PREP-BACKEND-UPLOAD-001` is READY with `PHASE 1 ACCEPTED` satisfied. `ARCH-UPLOAD-001` is still READY and `REVIEW-ARCH-UPLOAD-001`/`BACKEND-UPLOAD-001` remain BLOCKED, so this task does not implement or pre-approve a wire/storage contract.

Current evidence in this report is source inspection of `backend/`, `tests/backend/`, migration/configuration, current gates and the Phase 2 activation plan. Historical Phase 1 test and environment PASS records remain historical and are not relabeled as Phase 2 results. No database query, migration, service operation, storage mutation, upload, test suite or generated-contract refresh was run.

Safe checks performed from `C:\Dev\qa-visual-automation`:

| Check | Result |
| --- | --- |
| Read current state/task/acceptance/decision/activation/phase/role files | PASS; Phase 1 accepted, preparation READY, implementation gated |
| `rg --files backend tests/backend` and focused `rg -n` source/reference scans | PASS; current files and candidate seams mapped below |
| `git rev-parse HEAD` | PASS: `811b1e36199d424d83930f3381c7d71e537bc7d6` |
| `git status --short -- .orchestration backend tests/backend docs/architecture` | PASS with one permission warning for a retained test temporary directory; dirty shared worktree recorded, no files changed by the check |
| `.venv\Scripts\python.exe --version` | NOT_RUN successfully: restricted execution could not launch the venv's underlying interpreter. This is an environment/tool-access result, not a product failure or model limitation; no escalation was needed for this read-only preparation. |

The requested role file is `docs/prompts/03_backend.md` (underscore), not the initially attempted hyphenated path. It was found and read. No `docs/architecture/phase-2-upload-contract.md` existed at inspection time; Architect 02 reported it is being authored separately.

## Current Phase 1 behavior

### Route, request and response

- `backend/app/api/v1/screenshots.py:39-51` exposes one `POST /api/v1/projects/{project_id}/screenshots`, always returns 201 on success and sets `Location`. It explicitly rejects any `Idempotency-Key` header and has no replay/processing response path.
- The route calls `await request.body()` before parsing. `BoundaryMiddleware` also buffers POST/PUT/PATCH bodies up to 21 MiB and replays them. `parse_upload` then creates full in-memory part byte arrays and a `BytesIO`. Phase 2 may retain the existing bounded behavior, but contract/implementation must acknowledge that it is not a streaming reservation seam.
- Multipart requires exactly one `file` and one JSON-string `metadata` part. File limit is 20 MiB, metadata form-part limit 32 KiB, compact decoded metadata limit 16 KiB. The parser validates the unmodified Content-Disposition Unicode before library path handling, then stores a sanitized basename with control characters removed and surrounding whitespace stripped.
- `ScreenshotUpload` and `Screenshot` permit only `source="manual"`; request has no `client_upload_id`, response requires it to be null, and metadata version is literal integer 1. List filtering likewise permits only manual source.
- Current response already has most acknowledgment facts: screenshot/project/catalog IDs, source, sanitized original filename, uploaded time, file hash, MIME, size, dimensions, metadata version/data, client_upload_id and content URL. It has no receipt state/version/fingerprint/fence value.

### Schema and referential integrity

- `screenshots` has project-scoped composite FKs for Build, Locale and Category/Situation, restrictive deletion, positive size/dimensions, SHA-256 format, JSON object/version checks, globally unique storage key and project/id uniqueness.
- Existing migration/model constraint `ck_screenshot_phase1` requires `source='manual' AND client_upload_id IS NULL`. The nullable UUID column already exists but has no uniqueness or FK. Existing manual rows therefore provide a clean additive compatibility baseline.
- The engine defaults to REPEATABLE READ; upload explicitly switches its post-publication write to READ COMMITTED. Repositories flush but do not commit. Request dependency cleanup rolls back only.

### Storage and transaction sequence

Current `services/screenshots.py` sequence is:

1. validate project/catalog references in the current DB snapshot;
2. rollback that read snapshot before image/storage I/O;
3. stage original bytes and compute SHA-256; decode/validate image and optional resolution;
4. generate Screenshot UUID and `objects/{project_id}/{screenshot_id}.{ext}` key;
5. atomically publish by no-overwrite hard link;
6. open READ COMMITTED transaction, revalidate references, insert/flush Screenshot;
7. commit; return the new Screenshot;
8. on known pre-commit/IntegrityError rollback, delete the exact published key; on ambiguous SQLAlchemy commit failure, invalidate the session and look up the generated Screenshot ID using a fresh Session. If found, return it; otherwise retain the object and return 503 with manual list-inspection guidance.

The sequence is safe for a single manual request but provides no stable producer identity across requests. Same bytes/context currently create distinct screenshots. A response-lost retry creates another row/object. An ambiguous commit with no discoverable Screenshot leaves an object for later reconciliation, with no durable request record that can answer a replay.

### Reconciliation

`maintenance/reconcile_storage.py` requires the operator assertion `--writers-stopped`, a primary DB and complete inventories. It treats only `Screenshot.storage_key` as an object reference, reports missing/hash mismatches, and may delete unreferenced objects/staging older than 24 hours after a fresh primary Screenshot lookup. A receipt-owned object published before Screenshot completion would currently look orphaned and can be deleted. The fresh check also examines only Screenshot, so receipt awareness is mandatory before Phase 2 objects are published.

## Proposed Backend shape for Architect review

This is a design input, not an approved contract.

### Receipt as request identity and object ownership

Add a project-scoped durable upload receipt rather than overloading Screenshot as an in-progress row. At minimum the approved design needs:

- stable receipt UUID and unique `(project_id, client_upload_id)` for agent requests;
- protocol/fingerprint version plus immutable payload fingerprint and component facts needed to explain a mismatch (server file SHA-256 and canonical context/metadata/filename facts, without storing rejected raw input or secrets);
- state constrained to an explicit state machine, with created/updated timestamps and no automatic expiry in the initial design;
- server-chosen Screenshot UUID and deterministic storage key reserved before publication, so a retry/takeover addresses the same row/object;
- nullable completed Screenshot reference with project-scoped FK and uniqueness, populated only in the completion transaction;
- lease owner/token, DB-clock lease expiry and monotonically increasing fencing generation for processing/takeover; terminal error fields only if the contract requires durable diagnostics and with bounded/sanitized content;
- checks tying state to required/forbidden columns, and indexes for unique request identity, expired active leases, incomplete receipt recovery and completed Screenshot lookup.

Keep existing Screenshot rows untouched. Agent-completed Screenshots should retain `client_upload_id` and `source='agent'` for Web/API display. Prefer both a partial unique index on Screenshot `(project_id, client_upload_id) WHERE client_upload_id IS NOT NULL` as a final safety invariant and receipt uniqueness as the protocol authority. The Architect must decide whether Screenshot also references receipt or receipt alone references Screenshot; avoid an unnecessary circular FK.

### Suggested crash-safe sequence

1. Parse/validate the bounded request, sanitize filename, validate project relationships and inspect staged bytes to obtain authoritative file facts. Compute a versioned canonical payload fingerprint.
2. In a short DB transaction, insert or lock the `(project_id, client_upload_id)` receipt. Same ID/same fingerprint branches to completed replay or active/recoverable processing; same ID/different fingerprint returns conflict. Reserve Screenshot ID/storage key and acquire a DB-clock lease/fence. Commit this reservation before durable object publication.
3. Publish to the receipt-owned deterministic key with no-overwrite. If it already exists, stat/hash/size it; accept only an exact match. Never let a stale worker delete that key merely because its lease expired.
4. In one READ COMMITTED transaction, conditionally update the receipt by current owner/fence, revalidate catalog references, insert the reserved Screenshot and mark the receipt completed with the Screenshot reference. A stale fence changes zero rows and cannot complete.
5. Return 201 for first completion and the contract-selected replay status (201 or 200) with the same Screenshot identity and explicit replay signal. A response failure after commit is recovered through receipt lookup on resend.

Filesystem publication itself cannot be transactionally fenced by PostgreSQL. Safety therefore depends on deterministic no-overwrite keys, exact content verification, receipt ownership visible to reconciliation, and a rule that stale workers never compensate/delete a receipt-owned winner object. Known failures before durable receipt reservation may discard staging. After reservation/publication, cleanup must be state- and fence-aware.

### Additive migration proposal

Backend 03 should own a new `0003` migration only after the contract revision is independently accepted and PM promotes `BACKEND-UPLOAD-001`.

1. Create the receipt table, constraints and indexes without backfilling historical manual Screenshots into synthetic receipts unless the approved contract establishes a real need. Existing rows remain unchanged.
2. Drop/replace `ck_screenshot_phase1` with an explicit compatibility check: manual requires null client ID; agent requires non-null client ID; no unapproved source values. Add the partial project/client unique index concurrently only if the project migration policy supports PostgreSQL nontransactional DDL; otherwise use ordinary additive DDL in the planned maintenance window and document lock impact.
3. Add the project-scoped nullable receipt-to-Screenshot FK after both tables/constraints exist. Use `ON DELETE RESTRICT`; receipt lifetime and Screenshot deletion are not Phase 2 cleanup shortcuts.
4. Before and after migration in disposable/additive fixtures, assert original Screenshot count, IDs, storage keys, hashes, metadata JSON, exact Unicode and readable bytes are unchanged. Test upgrade from the real 0002 fixture, current metadata parity, fresh install and downgrade only in disposable databases.

Migration risk is at least high for implementation despite this preparation being medium: table/index locks, check replacement, uniqueness discovery, FK ordering, current uncommitted model/migration state, and cleanup behavior affect durable user data. Implementation should therefore use the already assigned `gpt-5.6-sol/high` request and stop if the accepted contract differs materially.

## Exact anticipated ownership

Subject to PM file claims after contract approval:

| Owner 03 files | Expected responsibility |
| --- | --- |
| `backend/app/api/v1/screenshots.py` | versioned agent request/header handling; first/replay/processing/conflict statuses and headers; preserve manual path |
| `backend/app/schemas/screenshots.py` | separate manual/agent request models and response receipt fields without weakening closed schemas |
| `backend/app/models/screenshots.py`, new `backend/app/models/upload_receipts.py`, `backend/app/models/__init__.py` | Screenshot compatibility constraints/index and receipt model/state invariants |
| new `backend/app/repositories/upload_receipts.py` | lock/reserve/replay/takeover/fenced conditional updates; no commit |
| `backend/app/services/screenshots.py`, optionally new `backend/app/services/upload_receipts.py` | orchestration, fingerprint comparison, receipt-owned publication, completion/recovery and compensation rules |
| `backend/app/maintenance/reconcile_storage.py` | complete reference set from Screenshots plus live/nonterminal receipt ownership; fresh pre-delete checks against both |
| `backend/app/storage/base.py`, `backend/app/storage/local.py` | only if approved exact-existing-object verification needs a protocol method; preserve no-overwrite/path protections |
| `backend/app/errors.py`, `backend/app/main.py`, `backend/openapi.json`, `backend/contract-examples.json`, `backend/README.md` | approved status/error/header contract, exports and operator recovery documentation |
| new `backend/migrations/versions/0003_*.py` | additive receipt/compatibility migration; preserve 0001/0002 history |
| `tests/backend/` | receipt API, PostgreSQL concurrency, migration preservation, storage/reconciliation and manual regressions |

Role 06 owns `agent/screenshot_upload/`, `tests/upload/` and the actual agent integration harness. Shared dependency/CLI/config changes need PM file claims. Frontend remains role 04. Backend should not implement queue retry/backoff state owned by the producer, though it must expose deterministic retry/replay/error semantics.

## Required fault-test seams

Prefer explicit internal collaborators/hooks at transaction boundaries over global `Session.commit` monkeypatching. Required reproducible seams/cases:

- after staging/inspection but before receipt reservation;
- after receipt reservation commit but before publication;
- after publication but before Screenshot/final receipt transaction;
- before and after final DB commit, including response-send loss after successful commit;
- concurrent first requests on separate connections, same ID/same payload and same ID/different payload;
- lease expiry and takeover using database time, renewal, stale fence attempting publish/finalize/cleanup;
- existing deterministic object with matching versus mismatching hash/size/media facts;
- DB unavailable during reserve/finalize/replay, storage unavailable, relationship changed after reservation, process restart with a new engine/session and same storage;
- reconciliation dry-run/apply with Screenshot-owned, active receipt-owned, expired recoverable receipt-owned, truly orphaned and stale staging objects; DB failure must delete nothing;
- additive migration with existing manual screenshot IDs/keys/hash/metadata/Unicode/bytes preserved, duplicate-preflight behavior and model parity;
- unchanged manual POST behavior, rejection of agent-only fields on manual schema, and no deduplication solely by equal file hash.

Use barriers and distinct SQLAlchemy Sessions/connections for concurrency. Use DB clock semantics (`clock_timestamp()` or an explicitly chosen equivalent) rather than process wall clock for leases; tests may set controlled expiry values in disposable DBs. Restart tests must recreate service/session objects and reuse the same PostgreSQL/storage, not merely call the same function twice.

## Contract questions requiring Architect 02 decisions

1. What is the exact scope of `client_upload_id`: project-wide UUID, producer-wide, or another namespace? Which party generates it, and must retries preserve it indefinitely?
2. Is `Idempotency-Key` the wire identity, metadata `client_upload_id`, or both? If both, must their canonical UUID values match? Duplicate raw header instances must be rejected rather than collapsed; whitespace/case/UUID textual canonicalization needs an explicit rule.
3. What fields enter payload fingerprint v1: authoritative file SHA-256, project/catalog IDs, source, metadata version/data, sanitized filename, MIME and declared/derived dimensions? Same bytes with different IDs must remain distinct; same ID with any fingerprint component change must conflict.
4. Define JSON canonicalization, especially key order, integer versus decimal representation, negative zero, arbitrary metadata numbers and exact Unicode. Existing policy preserves Unicode scalars and does not normalize combining sequences, so NFC/NFKC normalization would be a contract change.
5. Define filename identity. Current code validates raw Content-Disposition Unicode, then removes path prefixes/control characters and trims. Should fingerprint compare the sanitized stored basename (recommended for OS-path replay compatibility), raw filename bytes, or exclude filename? State how two different raw paths producing the same basename behave.
6. What first/replay/active statuses and headers are required: 201 versus 200 replay, Location, explicit replay/receipt header, active lease 409 versus 425/503, Retry-After source/units, and response body needed for producer acknowledgment? Existing middleware forces Retry-After 5 on every 503, which may conflict with lease/backoff-specific values.
7. Does an invalid request create a receipt? Recommended: reject structural/Unicode/image/reference failures before reserving protocol identity, but specify retry behavior if the same ID later arrives valid. Also define whether changed references after reservation are retryable, terminal or conflict.
8. What is the durable state machine and which states own an object? Specify state/column invariants, lease duration/renewal, DB-clock expression, takeover eligibility, fence increment and zero-row stale-update behavior.
9. Who may verify/reuse/delete a published receipt-owned object after a lease is lost? Recommended: exact-match reuse is allowed; stale-worker deletion is forbidden; only an exclusive receipt-aware recovery/reconciliation process may delete after an approved terminal/retention rule.
10. Is receipt retention permanent for initial Phase 2, as activation suggests? Define deletion behavior relative to Screenshot retention, project deletion and future cleanup; do not let receipt expiry silently remove idempotency guarantees.
11. Should agent and manual upload share one endpoint with discriminated metadata or use a distinct versioned route/media contract? Either choice must preserve the existing manual multipart and its browser-owned boundary.
12. Must Backend parse streaming input for Phase 2, or is the current bounded double-buffer accepted? If streaming changes, define when body hash/validation and reservation occur and how abandoned staging is bounded/reconciled.

## Completion and handoff

Preparation completion condition is met: current versus proposed behavior, exact ownership, preservation/migration risks, fault seams and contract questions are supplied. No Phase 2 AC is PASS, no implementation is READY, and no contract decision is made here.

Next: PM 01 records this preparation submission and routes it to Architect 02. Architect should resolve the twelve questions in the versioned contract and reconcile inputs from roles 03/04/06 before `ARCH-UPLOAD-001` submission. Reviewer 08 must independently accept the exact contract revision. Only then may PM promote `BACKEND-UPLOAD-001`; Backend rechecks the approved revision, file claims and risk level before implementation.
