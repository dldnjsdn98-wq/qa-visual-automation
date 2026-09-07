# Data flow and storage policy — ARCH-001

Revision 2: targeted correction of R08-ARCH-001; existing design retained; independent re-review pending.

Architect contract; pending independent review. This document specifies implementation and failure behavior; no functional acceptance is claimed.

## Catalog and review flow

1. Web creates Project → Build, Locale, Category → Situation; create StringKey using stable string_id.
2. Create StringEntries for selected Build/Locale. Assign ordered StringKeys to Build + Situation with atomic PUT.
3. Upload screenshot with the five scoped reference dimensions and source=manual. Server derives original filename, timestamp, hash and image properties.
4. List applies Project path plus AND filters. Detail independently loads image and Expected Strings using Screenshot's Build/Locale/Situation.
5. Expected Strings LEFT JOIN preserves missing translations. Catalog edits become visible on refetch; Phase 1 does not preserve upload-time expected text. Phase 3 verification snapshots must freeze their actual inputs.

## Storage abstraction

Application services inject this behavior, independent of filesystem/S3 implementation:

| Operation | Required behavior |
| --- | --- |
| stage(stream, limits) → StagedObject(token, byte_count, sha256) | Private nonservable staging; bounded streaming, unique token, no user-derived path |
| inspect(staged) → decoded image facts | Caller/decoder validates complete image, type/dimensions/frames; original stays unchanged |
| publish(staged, generated_key) → StoredObject | Durable complete bytes visible only after success; no overwrite of existing key |
| open_read(key) → stream plus byte_count | Application-authorized access; never accepts arbitrary user path |
| stat(key) → size/existence | Diagnose integrity and ambiguous writes |
| delete(key), discard_stage(token) | Idempotent missing-object success; delete only this operation's exact owned object |
| list_objects/list_staging (paged, age metadata) | Maintenance reconciliation, never exposed to browser |

Errors distinguish not found, unavailable and already exists. No SDK objects leak to routers. Local adapter resolves configured STORAGE_ROOT (default storage/local) relative to project root, rejects traversal/escape and symlink/reparse-point escape. Layout: staging/{random_token}, objects/{project_uuid}/{screenshot_uuid}.{validated_ext}. Store relative opaque key in DB. Temporary/final paths remain on one filesystem. Flush/fsync file before atomic no-overwrite publication, with directory durability where supported; Backend documents and tests Windows/Linux filesystem behavior. Future S3 adapter uses complete object publication with equivalent no-partial/no-overwrite behavior, not assumed filesystem rename.

Never trust filename, MIME, client hash or metadata IDs. Validate per api-contract.md before publishing. Decoder reads staging under memory/pixel limits. Preserve original bytes. Storage binaries, captures and QA data stay outside Git. Backend content route is the only image URL. Future cloud URLs may use short-lived access after project authorization; cloud implementation is out of scope.

## Phase 1 upload transaction and failure recovery

1. Bound the whole incoming request, strictly decode UTF-8/JSON and apply the API Unicode policy to all metadata keys/string values and the incoming filename before sanitization. Reject NUL or invalid scalar sequences with 422 VALIDATION_ERROR and safe field paths. Complete remaining metadata validation and check Project/references. Allocate server screenshot UUID and unique storage key. Stream to private staging while computing SHA-256/size. Multipart parsing may stage bytes before metadata arrives, but Unicode-invalid requests never reach publication or application DB writes; discard staging on rejection.
2. Decode/validate original; compare optional resolution. Publish durable original to generated final key. No DB Screenshot row exists yet. Request timeouts/cancellation must never skip cleanup bookkeeping; crashed-process leftovers are recovered by maintenance.
3. Begin short DB transaction; revalidate scoped references (they could have changed/deleted), insert Screenshot with server uploaded_at and commit. DB constraints protect races. Only committed rows appear in list/detail. Successful response occurs after both durable publication and commit.
4. If DB failure is known to roll back, delete only this request's final key. If deletion fails, retain it for reconciliation and log the key/request ID internally. Do not return a URL to uncommitted data.
5. If commit outcome is ambiguous (connection drops during commit), never immediately delete the object. Query by allocated screenshot UUID in a fresh connection to primary. If confirmed committed, return the committed resource if the connection permits. If unresolvable, return 503 and retain object for reconciliation. Client inspects list before retrying.

| Failure boundary | DB / object state | Required outcome |
| --- | --- | --- |
| Invalid body/type/size/image | no row; staging may exist | 4xx; discard staging; crash leftovers recovered later |
| Invalid Unicode in field, filename or nested metadata key/value | no row; no final object; parser staging possible | 422 VALIDATION_ERROR before publication/write; no stripping/repair; discard staging |
| Storage unavailable/publish fails | no row; staged or orphan final possible | 503; no success; reconcile uncertain publication |
| Known DB rollback after publish | no row; owned final exists | compensating delete; failures logged for maintenance |
| Crash after publish before insert | no row; orphan final | maintenance safely removes unreferenced object |
| Ambiguous commit or crash after commit | row may exist; original exists | never immediate delete; verify DB first |
| Response lost after commit | row and original exist | visible in Web; Phase 1 manual retry may duplicate |
| DB row exists but object disappears | row exists; content unavailable | 503 content, alert; restore backup/original; never silently delete row |

Maintenance is a Phase 1 Backend requirement: provide an explicit dry-run/apply reconciliation command with structured results, deterministic tests and README usage. Run only in exclusive maintenance mode: stop upload writers and wait for all in-flight uploads/transactions to finish or terminate their processes before scanning. Reads may remain active. Reconcile against primary DB; abort without deletion if DB availability/completeness cannot be established. Inspect only adapter-owned staging/objects older than 24 hours. Immediately recheck reference absence before exact-key deletion. This stop-writers rule prevents a collector from racing a published file awaiting insert; age alone is not protection. Crash survivors younger than grace remain until a later run. No recursive storage directory wipe. Report missing referenced objects and size/hash mismatches, but preserve rows/files for diagnosis. Backups must include DB and object store from the same quiescent checkpoint.

## Phase 2 durable upload agent — future

Visual Automation and standalone capture producers write image plus versioned JSON manifest to temporary local files, then atomically mark a queue item ready in captures/pending only when both are durable. Manifest carries client_upload_id, file_hash, core metadata and optional context. Agent alone delivers: pending → persisted attempt/backoff state → upload → confirmed server receipt → captures/uploaded. A timeout/crash retries the same UUID and bytes. Offline, backoff and terminal errors never delete originals; terminal failures retain files/diagnostics in captures/failed. Recovery scans durable manifests and resumes after process restart.

Server reserves a persistent project/client_upload_id receipt with fingerprint and lease before publication. Same fingerprint/completed receipt returns existing Screenshot; different payload conflicts; active lease is retryable. Final receipt completion and Screenshot row commit are one DB transaction. Lease attempt fencing prevents stale writers from finalizing or cleaning a winner's object. Agent moves the local original only after an acknowledged matching response. Receipt retention must cover the supported retry lifetime, with no automatic expiry in the initial design. Hash equality alone is not deduplication: context matters.

## Phase 3 processing — future

Committed Screenshot → durable job/outbox introduced with worker → OCRResult/regions → selected current expected catalog snapshot → exact/normalized/fuzzy matching → VerificationResult/items → Web. Claim work with retry/lease semantics; no unreliable fire-and-forget request background processing. Persist engine/model, thresholds, normalization/version, original coordinate boxes, confidence [0,1], match_score [0,100], expected/observed text and processing errors. Missing translation, missing OCR and job failure must not masquerade as quality PASS/FAIL. Reruns append results; originals and past results remain unchanged.

## Phase 4–6 visual execution — future

Device screenshot → required/optional/forbidden VisualAnchors → detected ScreenState (or uncertain) → Action → bounded screenshot polling → validated Transition.to_state. Uncertain states do not authorize blind input. Use deadlines, attempt limits and diagnostic captures; fixed sleep is not the main control mechanism. Checkpoint writes captures/pending for existing uploader, with run_id/device/resolution/scenario/checkpoint/screen_state metadata. Visual automation never calls Backend upload directly.

Recording captures allowed input, timestamp, before/after originals and detected states. Propose transitions/templates/scenarios for review. Graph stores Transition(from_state,to_state,action,cost), allows multiple edges, and uses finite nonnegative weights. Navigation validates actual state after each action; unexpected/unreachable states trigger bounded replanning/recovery and artifacts. No game internals or developer hooks.

## Verification responsibilities

ARCH-001 verifies specification coverage and consistency only. Backend evidence must include real PostgreSQL migrations/constraints, fixture image validation, DB/storage fault injection including ambiguous commit, safe reconciliation and API response tests. Frontend evidence must include CRUD/filter behavior, dependent selection reset, stale-response handling, missing/empty translations, detail/content rendering and upload errors, plus build/typecheck. Existing bootstrap tests are not these checks. Reviewer 08 evaluates AC-ARCH-01 separately from later AC-WEB-01..13; PM alone promotes downstream roles after acceptance.
