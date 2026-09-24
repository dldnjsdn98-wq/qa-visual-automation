# Phase 2 durable upload contract

Contract ID: P2-UPLOAD-v1. Document revision: 2. Owner: 02 / ARCH-UPLOAD-001.
Status: author submission candidate; independent REVIEW-ARCH-UPLOAD-001 acceptance and PM READY are required before implementation. This document specifies planned behavior, not product PASS.
Dependency: Phase 1 ACCEPTED, recorded in [PM activation](../../.orchestration/handoffs/PHASE-2-activation-01.md).
Scope: API, persistent receipt, object recovery, producer and queue protocol. Existing manual uploads and originals are preserved.

## 1. Versions and compatibility

This document supersedes only the Phase 2 outlines in [API](api-contract.md), [data flow](data-flow.md), and [domain model](domain-model.md). Their Phase 1 sections remain the accepted manual contract. API route version, upload_protocol_version, metadata_version, fingerprint_version, manifest_version and queue_state_version are separate version domains, initially 1. Document revision does not silently change a wire version. Future incompatible canonicalization requires a new fingerprint/protocol version with an explicit migration and old-receipt replay policy; never recompute an existing receipt under a new algorithm.

POST /api/v1/projects/{project_id}/screenshots continues to accept exactly two multipart parts, file and metadata (JSON string). Manual uses the existing source="manual" schema: no client_upload_id, upload_protocol_version, expected_file_hash or Idempotency-Key; supplying any of these, including null, returns 422 VALIDATION_ERROR. Two identical valid manual submissions still create two resources with 201. No automatic manual retry is introduced.

Agent and automation use the same route, image rules and core fields, with the following closed metadata-part schema:

| Field | Requirement |
| --- | --- |
| upload_protocol_version | Required integer 1, not bool/string/float |
| client_upload_id | Required UUID v4 generated once by producer; canonical lowercase hyphenated string persisted before publication |
| build_id, locale_id, category_id, situation_id | Required UUIDs; normalize typed IDs to lowercase hyphenated form |
| source | Required agent or automation; uploader preserves producer source |
| metadata_version | Optional integer 1, default 1; null invalid |
| metadata | Optional CaptureMetadata object, default {}; null invalid |
| expected_file_hash | Optional lowercase 64-hex SHA-256 assertion; uploader always supplies its persisted original hash; null invalid |

Project ID comes only from the URL. No metadata-part project_id, timestamp, screenshot ID, dimensions or filename override is accepted. Original filename comes from file disposition. CaptureMetadata and image limits remain as in Phase 1: file 1..20,971,520 bytes, whole request <=22,020,096 bytes, metadata part <=32,768 bytes, capture metadata <=16,384 compact UTF-8 bytes, container depth <=5, <=100 total object keys, single PNG/JPEG frame, each dimension <=16,384, <=40,000,000 pixels, complete decode and MIME/signature match, supplied resolution equals decoded dimensions. No image re-encoding. Existing bounded in-memory buffering is permitted for Phase 2; 21 MiB is a wire limit, not a peak-RAM claim. Count received bytes before unbounded growth, account for parser/decoder copies and impose bounded request concurrency. Streaming redesign is not required for this contract.

Agent protocol additionally rejects duplicate JSON object keys (at every depth) and numbers outside section 3's canonical number domain. These restrictions do not alter manual input acceptance. Recursive U+0000/surrogate checks precede normalization/sanitization; malformed UTF-8 is rejected, valid supplementary scalars and combining sequences remain intact.

### 1.1 Header and response policy

Idempotency-Key remains unsupported for every source: presence (empty, duplicate, malformed, matching or mismatching) returns 422 VALIDATION_ERROR with field body and fixed reason "Idempotency-Key is not supported; use client_upload_id for agent uploads". There is no header/body precedence or fallback and no header-based receipt lookup. UUID is scoped by project, never globally by header. Other request IDs are ignored; X-Request-ID is generated independently on every response, including replays/errors.

Success body remains the existing Screenshot object, not a receipt envelope. All existing fields stay present. Extend source to manual|agent|automation and client_upload_id to UUID|null; valid pairs are manual/null and agent-or-automation/non-null. List/detail and source filter support those three sources with existing paging/filter rules. No receipt internals, attempt token, storage key or fingerprint is public. Receipt matching uses the returned identity, original hash and complete context, as in section 8.

| Outcome | Status / code | Headers and side effects |
| --- | --- | --- |
| Manual successful insert | 201 Screenshot | Location; X-Request-ID; no Idempotency-Replayed |
| This agent request completes its owned attempt | 201 Screenshot | Location; Idempotency-Replayed: false |
| Valid identical completed receipt, including uncertain-commit recovery via fresh connection | 200 original Screenshot | Same Location; Idempotency-Replayed: true; original id/uploaded_at |
| Same scoped ID, valid different fingerprint | 409 IDEMPOTENCY_CONFLICT | No Retry-After; never changes existing receipt |
| Same fingerprint with unexpired PROCESSING lease, or a fenced former owner | 409 UPLOAD_IN_PROGRESS | Retry-After: positive integer seconds, see section 5 |
| Invalid types/version/Unicode/duplicate keys/hash assertion | 422 VALIDATION_ERROR | No receipt creation or mutation; safe field reason |
| Invalid image / MIME / request size | Existing 422 INVALID_IMAGE / 415 UNSUPPORTED_MEDIA_TYPE / 413 UPLOAD_TOO_LARGE | No receipt creation or mutation |
| Missing project/scoped reference / scope mismatch | Existing 404 RESOURCE_NOT_FOUND / 422 VALIDATION_ERROR | No new reservation; completed replay uses receipt identity, see section 4 |
| Transient storage/DB, including unresolved commit | 503 STORAGE_UNAVAILABLE / DATABASE_UNAVAILABLE | Retry-After: 5; outcome may be unknown |
| Unexpected internal failure | 500 INTERNAL_ERROR | Existing safe envelope; no claim of rollback |

All errors retain the Phase 1 Error envelope and server X-Request-ID; details never echo unsafe input. Location is /api/v1/projects/{project_id}/screenshots/{id} on both 201 and 200 replay. Idempotency-Replayed is emitted only on successful agent/automation responses. Retry-After is omitted for terminal 409/422. CORS retains explicit loopback origins and exposes Location, X-Request-ID, Retry-After, Idempotency-Replayed; never broaden origins/credentials. Browser manual FormData still owns its boundary. Unexpected transport/proxy headers are not identity inputs. No automatic redirects by the uploader.

AC-P2-04 Web minimum: list/detail display source and existing relational context; detail additionally displays client_upload_id when non-null, metadata_version and the complete bounded CaptureMetadata object, including unknown nested keys, empty strings, nulls and Unicode, as safe text/structured JSON. No raw HTML. Existing source rendering can remain; separate manual request type from the expanded Screenshot response type. A source filter UI is not required, although the API enum expands.

## 2. Identity and immutable intent

Receipt key K=(project_id, client_upload_id); UUID v4 collision is a payload conflict, not permission to allocate a new ID automatically. Same UUID in another project is a distinct scope. Producer makes one UUID per intended capture, stores it durably, and never changes it on retry, restart, timeout, failed/ uploaded reclassification or explicit retry. A new intentional capture uses a new ID even if bytes are identical.

Once ready is published, original bytes, filename, source, all core IDs, metadata and versions are immutable. Edit/replacement requires an explicit new queue item/UUID and preserves the old record; no automatic conflict resolution by new UUID. expected_file_hash asserts bytes only; a matching hash is insufficient for duplicate equivalence.

## 3. Fingerprint version 1

Server computes SHA-256 over received original bytes after bounded staging and complete image validation; it never trusts expected_file_hash. A supplied mismatching assertion is 422, before receipt lookup or mutation.

Canonical payload is the object with exactly these keys:
fingerprint_version=1, upload_protocol_version=1, project_id, build_id, locale_id, category_id, situation_id, source, original_filename, metadata_version=1, metadata, file_hash, media_type, size_bytes, width, height.
Exclude client_upload_id (part of K), expected_file_hash (assertion only), incoming headers, multipart boundary/order, raw JSON whitespace/key order, local paths/times, receipt fields and server id/uploaded_at/content_url.

Typed core UUIDs are canonical lowercase hyphenated strings. Default omitted metadata_version/metadata to 1/{}. All other strings are exact Unicode scalar sequences with no NFC/NFD, case folding or whitespace trimming except the specified filename sanitization. Nested metadata.run_id is validated as UUID but its supplied string spelling remains stored/fingerprinted; it is not a core typed ID normalization target. Unknown metadata null is significant; missing key is distinct from key:null; arrays retain order; booleans differ from numbers.

Filename algorithm exactly mirrors current Phase 1 Python behavior: validate the complete original decoded filename/disposition Unicode before a multipart library can strip a path; replace backslash with slash; take final component; remove Unicode general category Cc; apply Python str.strip() Unicode whitespace semantics; require 1..255 scalars. No normalization of remaining Unicode. Producer sends and persists an already sanitized basename. Backend fingerprints and returns this sanitized basename. Different raw path prefixes yielding the same sanitized name are semantically equal; an invalid prefix is rejected even if the final basename would be valid.

Canonical serialization: RFC 8785 JSON Canonicalization Scheme (JCS), UTF-8, no BOM or trailing newline. Keys sort by UTF-16 code units per JCS, including nested metadata keys; not Python's default Unicode code-point ordering. Escaping/numeric serialization follows JCS, not json.dumps(sort_keys=True). Fingerprint = lowercase SHA-256 hex of these canonical bytes. Implementers must use a conforming implementation or tested equivalent and record its version; dependency/shared-file changes require PM ownership.

Agent number domain: JSON numeric tokens decode to finite IEEE-754 binary64, with correctly rounded conversion; reject nonzero tokens that underflow to zero, infinities/NaN, and any resulting integral value outside [-9007199254740991,9007199254740991]. Negative zero canonicalizes to 0; 1, 1.0 and 1e0 are equivalent. Nonintegral decimal tokens that round to the same binary64 value have the same meaning. Persist/return values such that JCS canonicalization round-trips to the same values (JSONB decimal serialization must not change the binary64 value). Reject unsupported values as 422, never hash lossy platform-specific strings. Resolution dimensions still require JSON integers, not bool/float. Capture metadata byte-size check uses the existing compact literal-Unicode JSON convention after numeric decoding; JCS hashing is a separate operation.

Canonicalization examples (synthetic, not product evidence):
- Omitted defaults vs explicit metadata_version:1 and metadata:{}: equal.
- Metadata {"b":1.0,"a":"한글"} vs {"a":"\uD55C\uAE00","b":1}: equal.
- Metadata {"note":"é"} vs {"note":"e\u0301"}: different.
- {"note":null} vs {}: different; [1,2] vs [2,1]: different; true vs 1: different.
- Raw filename C:\\capture\\a.png vs a.png: equal after valid sanitization.
- Same K and file hash, changed situation/source/filename/unknown metadata: different, terminal 409 after complete validation.
- Same K and different valid bytes: different; an incorrect expected hash instead returns 422.
- Different client_upload_id with identical payload/hash: different receipts and Screenshot IDs, no hash deduplication.
- Same client_upload_id in a different project with that project's valid references: distinct receipt.
- Metadata keys U+1F600 and U+E000 sort with U+1F600 first under JCS; test this explicitly.

### 3.1 Wire example

Project: 11111111-1111-4111-8111-111111111111. File part filename: tutorial-ja.png, Content-Type: image/png. The hash below is an illustrative placeholder; replace it with the actual synthetic fixture SHA-256 before sending.

```json
{"upload_protocol_version":1,"client_upload_id":"66666666-6666-4666-8666-666666666666","build_id":"22222222-2222-4222-8222-222222222222","locale_id":"33333333-3333-4333-8333-333333333333","category_id":"44444444-4444-4444-8444-444444444444","situation_id":"55555555-5555-4555-8555-555555555555","source":"agent","metadata_version":1,"metadata":{"device":"테스트","checkpoint":"日本語 😀"},"expected_file_hash":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
```

For a valid fixture, first response has 201, Idempotency-Replayed:false, that project's Location and the existing Screenshot fields including client_upload_id above, source:agent, computed file_hash, original_filename:tutorial-ja.png, and the submitted capture context. Resend the exact request after a lost response: 200, Idempotency-Replayed:true, same id/uploaded_at/hash/context. Change checkpoint under the same ID: 409 IDEMPOTENCY_CONFLICT, no Retry-After. A second connection during its active lease: 409 UPLOAD_IN_PROGRESS and Retry-After computed from lease. There is no independently invented response hash or fake successful file example.

## 4. Validation and reservation order

1. Bound actual request bytes independently of Content-Length; verify multipart media/shape and reject Idempotency-Key. Read-only parsing/private staging is allowed. Strict UTF-8/JSON plus recursive Unicode validation precedes normalization; reject duplicate keys for agent. Then closed schema/types/versions, metadata bounds, filename, image/MIME/size/dimensions/resolution and supplied hash assertion. Invalid input creates no application row/published object.
2. Verify path project exists; compute version-1 fingerprint from fully validated payload. Receipt operations always use authoritative primary DB and READ COMMITTED, never replica/cache. DB unavailable: 503, retain only safe owned staging.
3. In a short transaction serialize K using PK insert conflict handling/row lock. Inspect existing receipt before current contextual FK revalidation: different fingerprint yields 409 even if old metadata references have subsequently disappeared; completed equal fingerprint returns its stored committed Screenshot. Completed receipts keep their parents alive through restrictive FKs, so a missing committed target is an integrity incident (503 DATABASE_UNAVAILABLE plus alert), never a fresh insert.
4. New or takeover attempts revalidate all current scoped references inside reservation transaction. Missing reference/scope error wins over new reservation; do not mutate the receipt on failed validation. Atomically create PROCESSING or take over eligible state as section 5. Commit reservation before publication; resolve uncertain reservation outcome by primary locked read and attempt-token equality before proceeding.
5. Publish only after ownership is confirmed. Finalize in a separate short transaction as section 6, revalidating references/constraints. Never hold a DB transaction open during multipart reading, image decode, file publication or network response. Lock wait must be bounded (5 seconds; timeout 503 DATABASE_UNAVAILABLE with Retry-After:5).
6. Replay still validates received bytes/image/hash/Unicode; it is not a shortcut accepting malformed payloads. Receipt lookup alone cannot acknowledge a differently supplied image.

## 5. Receipt schema, lease and retention

Add upload_receipts without rewriting applied migrations. Retain every existing Screenshot ID/hash/filename/metadata/storage key. New Screenshot CHECK:
(source='manual' AND client_upload_id IS NULL) OR (source IN ('agent','automation') AND client_upload_id IS NOT NULL).
Add unique(project_id,client_upload_id) WHERE client_upload_id IS NOT NULL; file_hash is not unique.

| Receipt column | Type / invariant |
| --- | --- |
| project_id, client_upload_id | UUID composite PK; project FK ON DELETE RESTRICT |
| fingerprint_version, upload_protocol_version | integer NOT NULL, =1 |
| request_fingerprint | char(64) NOT NULL, lowercase hex, immutable |
| state | PROCESSING, COMPLETED or FAILED, NOT NULL |
| attempt_generation | bigint NOT NULL >=1, strictly increases on every takeover/retry, never reset/wrap |
| attempt_token | UUID NOT NULL, new random v4 on every generation |
| candidate_screenshot_id | UUID NOT NULL, fresh per generation, used in object key; immutable within attempt |
| candidate_storage_key | text NOT NULL, unique, generated objects/{project_uuid}/{candidate_screenshot_uuid}.png or .jpg |
| screenshot_id | UUID nullable; composite (project_id,screenshot_id) FK to screenshots(project_id,id), ON DELETE RESTRICT; unique when non-null |
| lease_expires_at | timestamptz; non-null exactly when PROCESSING |
| last_error_code | nullable bounded safe code (<=64 chars), no raw payload/SQL |
| created_at, updated_at | timestamptz NOT NULL, primary DB assigned |

PROCESSING/FAILED require screenshot_id NULL; COMPLETED requires screenshot_id=candidate_screenshot_id, lease NULL and last_error_code NULL. FAILED requires lease NULL. In a completed pair the Screenshot must have the same project/client_upload_id, source and fingerprint-derived context; enforce service transaction plus composite identity FK/constraint wherever possible. Backend must include a deferrable composite FK (project_id,screenshot_id,client_upload_id) to a corresponding Screenshot UNIQUE(project_id,id,client_upload_id), in addition to the stated project scoping, so completed receipts cannot point to another upload's screenshot. Candidate file extension follows decoded MIME. Add a partial index on lease_expires_at for PROCESSING and a project_id index for restrictive deletion checks; PK/unique constraints cover identity lookups. Persist immutable canonical payload (canonical_request BYTEA NOT NULL, exact JCS bytes, bounded <=64 KiB) alongside its hash to support audit and collision diagnosis; check its hash before use. Never replace original intent during retries.

Retention: no automatic receipt TTL, pruning or reuse, including FAILED receipts. COMPLETED and its Screenshot/original remain indefinitely; no Screenshot DELETE endpoint in this phase. Project deletion is blocked by receipts as well as screenshots. Failed reservations retain identity even if unused context parents are later deleted; corrected metadata requires a new explicit intent. Future deletion/retention must preserve permanent deduplication tombstones or explicitly version a bounded retry promise; no such change is authorized here.

Lease: authoritative time is PostgreSQL clock_timestamp(), sampled after acquiring the receipt row lock. Do not use transaction-start now(), application wall clock, client timestamp or local monotonic time for server expiry. Default duration 60 seconds; renew every <=20 seconds during long work using a short independent transaction. Renewal predicate: PROCESSING, matching K/fingerprint/generation/token, and lease_expires_at > sampled DB time; new expiry=sampled time+60s. Expired owner cannot revive its lease. Equality counts as expired. Failed renewal/unavailable DB stops finalization; leave uncertain objects for maintenance.

Takeover: same fingerprint and PROCESSING with lease_expires_at <= DB time, or FAILED, may atomically set PROCESSING, generation+1, fresh token/candidate ID/key, expiry=DB time+60s and clear error. FAILED means an already reserved attempt stopped with confirmed noncompletion, including final reference loss; pre-reservation invalid requests/conflicting payloads never create FAILED. No automatic server retry loop is required; client resubmission drives takeover. First reservation generation=1. Overflow is an operational blocker, never wrap.

An active competitor receives Retry-After=max(1,ceil((lease_expires_at-DB time) seconds)); a fenced owner rereads and returns completed same-request replay if available, otherwise UPLOAD_IN_PROGRESS with current remaining lease or 1 second. A DB lookup failure returns 503, never guesses state. Transition/renew/finalize operations compare BOTH generation and token. Application locks alone are not sufficient across processes.


## 6. Object ownership and crash recovery

A candidate ID/key is deterministic FROM THE CURRENT RESERVED ATTEMPT, not from the receipt key across all attempts. Every new generation gets a fresh Screenshot UUID and objects/{project_id}/{candidate_id}.{ext}; existing LocalStorage grammar is preserved. Stale publication can leave only that generation's orphan. Never reuse another generation's key, hash-path or client filename. This replaces Backend03's cross-attempt deterministic-key proposal: immutable per-attempt keys plus no worker deletion make filesystem actions safe even though PostgreSQL cannot fence filesystem publication.

Publish complete original bytes with no-overwrite and file/directory flush where supported. A retry within the SAME confirmed generation may verify an existing exact key/hash/size and continue; mismatch is STORAGE_UNAVAILABLE with an alert, never overwrite. Unknown publication result is not proof of absence.

Finalize in a short READ COMMITTED transaction: lock receipt, sample clock_timestamp(), require PROCESSING and exact K/fingerprint/generation/token with unexpired lease; revalidate scoped references; insert Screenshot with candidate ID/key, K and validated immutable facts; update receipt COMPLETED, screenshot_id=candidate_id, lease/error=NULL; commit both together. Repositories/dependency cleanup never commit. No file/network I/O in this transaction. Lease validity is evaluated at the locked decision point; expiration during this short transaction does not undo serialization, because takeover waits for its lock. Row/statement/transaction waits must be bounded and tested.

Known rollback: a fresh fenced transaction can mark the same still-owned PROCESSING generation FAILED; never mutate another generation or COMPLETED. If that bookkeeping fails, leave it for expiry. Reference disappearance during finalization yields the existing 404/422 to the client, keeps immutable receipt identity, and records FAILED only after confirmed rollback (FAILED also covers such stopped attempts, not just infrastructure errors). Same-payload retry must pass current references before takeover. Corrected context needs a new intent.

For agent requests, request workers NEVER delete published final objects, including after known rollback or lost lease. Only discard the exact private staging token after that request's I/O has stopped. Published leftovers go to exclusive maintenance. Manual compensation remains unchanged. This intentionally trades temporary disk use for a simple enforceable ownership boundary.

On ambiguous reserve/finalize commit, invalidate the connection, retain every published object, and never mark FAILED based on uncertainty. Use a fresh PRIMARY READ COMMITTED transaction acquiring the same row lock; wait for the surviving original transaction to finish. For uncertain FIRST INSERT with no visible row, an ordinary SELECT FOR UPDATE cannot lock absence: arbitrate through the composite unique-key INSERT ... ON CONFLICT (same validated intent), which waits for the original insert outcome, then lock/read the winner. Do not publish before the committed reservation identifies the exact owned generation/token/candidate. The 5s lock timeout returns 503 DATABASE_UNAVAILABLE, Retry-After:5; no guessing or deletion.

Recovery outcomes:
- Matching COMPLETED: return 200 replay of committed Screenshot, original ID/time/context.
- Matching own PROCESSING, unexpired lease: verify own published object or publish if definitely absent, then fenced finalize; alternatively return retryable conflict. Do not send 201 without confirmed final commit.
- Another generation: deny stale finalization; return matching completed replay or UPLOAD_IN_PROGRESS/current lease delay.
- Confirmed rolled-back reservation: same-intent unique-key arbitration may reserve afresh; no blind assumption from a snapshot.
- Primary/lock outcome unresolved: 503, retain data, retry same ID.

A completed missing/mismatched object is an operational incident: retain Screenshot/receipt, content returns 503 STORAGE_UNAVAILABLE and alert. Never insert a second Screenshot or automatically overwrite the original. Replay normally acknowledges the committed record, not a fresh storage audit; known corruption during replay returns 503. Backup restoration is separately authorized.

Maintenance extends the existing exclusive protocol. Stop/drain or terminate all manual/agent HTTP writers, lease renewers and recovery jobs and their surviving DB transactions; keep them stopped throughout deletion. Confirm primary/not in recovery and complete inventories, fail closed on any uncertainty. Protect ALL Screenshot keys AND PROCESSING candidate keys, including expired/recoverable receipts. Under exclusivity, explicitly mark confirmed abandoned PROCESSING attempts FAILED before considering their key orphaned. FAILED/obsolete attempt objects are eligible only when unreferenced and older than 24h. Fresh primary reference/state recheck immediately before exact-key deletion; no recursive wipe. Staging older than 24h is eligible only under the same exclusive rule. Missing/mismatched referenced originals are reported/preserved. Lease expiry/file age alone never authorizes deletion. Back up DB/storage from one quiescent checkpoint.

## 7. Producer and queue protocol

Durability promise: process termination/restart on a local filesystem supporting atomic same-volume rename and file flush. Sync directory metadata where supported; explicitly test/document Windows and Linux. No unconditional sudden-power-loss guarantee on Windows where directory flush is unavailable. Reject cross-volume roots/network shares and fail closed if required locking/atomic operations are unsupported. Never test crashes against real user captures.

Layout: captures/{pending,uploaded,failed}/{client_upload_id}/ on one local volume. UUID directory name must match manifest; local UUID names are globally unique although server K is project-scoped. Fixed item files: original.png OR original.jpg, manifest.json, ready.json; agent adds state.json and initialized.json. Temporary files end .tmp and are never upload candidates. Safe diagnostics use diagnostic-* names and are never protocol authority. Reject traversal/symlinks/reparse points, unexpected files and outside-root paths. No overwrite/merge of existing item directories.

Closed manifest_version=1 schema (all required):
- manifest_version:1, upload_protocol_version:1, client_upload_id:UUIDv4, project_id:UUID.
- image_file:"original.png"|"original.jpg", original_filename:sanitized basename, file_hash:lowercase SHA256, size_bytes:positive integer, media_type:"image/png"|"image/jpeg", width/height:positive integer.
- request:{build_id,locale_id,category_id,situation_id,source,metadata_version:1,metadata:{...}}; source is agent or automation, core IDs are UUIDs, same API rules.
No endpoint, credentials, arbitrary paths or unknown top-level fields. Strict UTF-8/JSON/duplicate-key/Unicode/number rules from section 3. Manifest <=64KiB, ready <=1KiB, state including ack <=256KiB; enforce before decode. Digest covers exact manifest bytes, not JCS. File facts must match complete decode. Producer persists an already sanitized filename and canonical core IDs. Configured Backend origin is bound by immutable spool-root binding.json as defined in sections 7.1/7.2; no in-place destination migration is supported.

Publication sequence:
1. Exclusively create pending item directory/UUID; write original.tmp, flush/close, atomically rename to fixed image filename; sync parent where supported.
2. Compute actual hash/size/facts; write manifest.json.tmp, flush/close, rename manifest.json, sync parent.
3. Write ready.json.tmp containing exactly {"manifest_version":1,"manifest_sha256":"<SHA256 of exact manifest.json bytes>"}; flush/close, rename ready.json LAST, sync parent.
Producer then relinquishes immutable files. Only complete ready+matching manifest+matching image is eligible. Image-only/manifest-only/temp/truncated/unready is never submitted. A pair without marker stays unready indefinitely; only its producer may finish publication after revalidating its own known intent. Agent never infers readiness from age/stable file size. Invalid ready item is quarantined with original and diagnostics retained, no HTTP.

Single agent process per spool: hold an OS-managed exclusive lock handle at captures/.upload-agent.lock throughout execution, outside movable item directories. Lock-file existence/age is not ownership. Second process exits without mutation/HTTP; process termination releases handle. No local lease stealing or distributed workers. Sequential sends are sufficient. Producer writes separate exclusive directories, never agent state.

Protocol v1 uses atomic per-item state.json, NOT SQLite. Manifest/ready own immutable per-item intent; binding.json owns the destination; state owns progress; directory scan is the index. There is no queue DB to rebuild. This replaces 06's SQLite proposal to avoid a second authority across DB/file moves for a single agent. Missing/corrupt state is never silently reconstructed after prior ownership evidence; retain/quarantine rather than reset attempts or lose ack.

state.json closed fields:
queue_state_version:1; client_upload_id; manifest_sha256; state:PENDING|IN_FLIGHT|RETRY_WAIT|ACKED|UPLOADED|FAILED; state_revision:integer>=1; attempt_count:integer>=0 (lifetime); retry_epoch:integer>=0; epoch_attempt_count:integer>=0; last_attempt_at:UTC|null; next_attempt_at:UTC|null; last_error:{code:string<=64,request_id:UUID|null,status:integer|null}|null; ack:object|null.
Initialize PENDING revision=1/counts=0/epoch=0 with null times/error/ack. IN_FLIGHT/RETRY_WAIT require both timestamps and no ack. ACKED/UPLOADED require a valid ack, null next_attempt_at/error. FAILED requires safe error, null next_attempt_at/ack. PENDING has null next_attempt_at/ack. Counts never decrease except epoch_attempt_count on explicit new retry epoch; revision increases on each state change.

State update: write same-directory temp, flush/close, atomic replace, sync parent. Old valid state wins over a partial temp. First initialization writes state BEFORE initialized.json; initialized.json contains exactly {queue_state_version:1,client_upload_id,manifest_sha256}, likewise atomically flushed. Do not send before both are durable. Ready-only with neither is new. Valid state with missing marker repairs marker without resetting state. Marker with missing/corrupt state, or identity/digest mismatch, is quarantine, never a new PENDING item. Loss of both state and marker after storage corruption cannot be distinguished from a fresh item; supported process-crash guarantees do not cover arbitrary deletion/power-loss. Operator recovery must inspect retained backups/server receipt, not automatically declare uploaded; server idempotency still prevents duplicate Screenshot on same-intent resend.

Before EVERY first/retry/recovery send, revalidate marker/manifest immutable identity and original bytes/hash/size/facts; mutation is LOCAL_INTENT_CHANGED terminal. Before HTTP, persist IN_FLIGHT with incremented total/epoch counts, last_attempt_at and precomputed recovery deadline. Crash before send consumes an attempt conservatively. Restart IN_FLIGHT becomes RETRY_WAIT with the same count/deadline (or exhausted FAILED); never reset UUID/attempts. State write failure prevents sending/acknowledging and halts processing with a visible error.

### 7.1 Immutable spool destination binding (revision 2)

The spool root has exactly one destination authority: captures/binding.json, separate from item initialized.json. Closed schema: {"binding_version":1,"backend_origin":"http://127.0.0.1:8001"}. Both fields required; version is integer 1 (not bool/float/string); no unknown keys. Strict UTF-8 JSON without BOM, duplicate keys, NUL or surrogate scalars; maximum 1 KiB checked before decode. backend_origin must ALREADY equal its canonical representation below. The file bytes must be exactly UTF-8 encoding of {"binding_version":1,"backend_origin":"<canonical origin>"} in that key order, with no spaces, escapes, BOM or final newline; validate schema first and then exact reserialization equality. A noncanonical stored value/encoding is corrupt, not silently repaired. The per-item manifest/state/initialized/ack schemas and API fingerprint remain unchanged; they do not hold destination overrides.

Canonical origin grammar is deliberately narrower than a general URL. Accept an ASCII string with case-insensitive http:// or https://, a host, optional :port, and optional single trailing slash. Reject any whitespace/control/non-ASCII character, backslash, percent escape, userinfo (@), query (even empty ?), fragment (even empty #), any other path, empty host/port, unbracketed IPv6 or IPv6 zone ID. Do not trim, percent-decode, use DNS resolution, follow redirects or accept a parser's repaired URL.
- DNS: dot-separated labels of ASCII letters/digits/interior hyphens, each 1..63 characters, total <=253; first/last label characters alphanumeric, no empty labels/trailing dot. Lowercase the name. Reject any label beginning xn-- (case-insensitive); no IDNA conversion. localhost is allowed. To avoid alternate IPv4 notation, a DNS hostname's final label must contain an ASCII letter and must not be a 0x-prefixed hexadecimal integer. Pure numeric hosts must instead pass the IPv4 rule.
- IPv4: exactly four decimal components, each 0..255, no leading zeros except the single digit 0. Reject short/octal/hex/integer address forms such as 127.1, 0177.0.0.1 or 0x7f000001.
- IPv6: brackets mandatory; accept only standard hexadecimal colon notation (no embedded dotted-decimal tail or zone), 128-bit valid address with at most one :: compression. Serialize as eight lowercase hexadecimal groups with leading zeros removed and the first longest zero run of >=2 groups compressed (RFC 5952); retain brackets.
- Port: ASCII decimal digits, 1..65535, no leading zeros; omitted means 80 for http and 443 for https. Drop an explicit default port; preserve every other port. Lowercase scheme; omit the optional root slash.
- Scheme, canonical host and effective port define equality. localhost, 127.0.0.1 and [::1] are DISTINCT bindings even if they resolve to one machine. DNS aliases are never coalesced. This is destination URL continuity, not proof that a server's DB identity cannot change behind the same origin; changing/replacing that server's persistent store is outside this protocol and must preserve its receipts by the existing backup rules.

Examples: HTTP://LOCALHOST:80/ -> http://localhost; https://Example.COM:443 -> https://example.com; http://[0:0:0:0:0:0:0:1]:8001/ -> http://[::1]:8001. http://localhost:8001 differs from http://127.0.0.1:8001. Ports 080, 0 and 65536, https://host/path, https://host?, https://user@host, https://host# and http://127.1 are rejected.

Initialization is an explicit uploader-local init command, never a side effect of worker startup, producer discovery or retry. It uses the existing root .upload-agent.lock exclusively; the operator must stop/drain producers before initialization. A producer MUST require a valid binding before creating any item directory and preserve it unchanged; it cannot initialize the spool from an item's data/configuration. Producers and normal workers never delete/rebind the root file. Bootstrap never creates an item or performs HTTP.

A pristine spool is absent, or contains ONLY the .upload-agent.lock regular file, optional empty regular .gitkeep, and pending/uploaded/failed directories each absent or empty except an optional empty regular .gitkeep. Root and the three state directories must be ordinary directories; lock, final, temp and .gitkeep must be ordinary regular files; all reject links/reparse points, wrong types and unreadable inspection. No item directory (even empty), image, manifest, diagnostic, ACK/state, unknown root entry, link/reparse point or unreadable inventory is permitted. Create absent root/state directories safely as needed while retaining this definition; directory creation before binding publication is harmless partial initialization. No recursive deletion or automatic adoption of a nonempty legacy spool.

Under the lock, first inspect binding.json and a complete safe root inventory:
1. Valid final binding + same canonical configured origin: explicit init is an idempotent read/verify success, including a populated spool; do not reset or write any item/state or replace binding. Valid final + different origin: BINDING_MISMATCH, refuse even if the spool is empty.
2. Final absent and pristine: write canonical closed-schema bytes to exclusive root binding.json.tmp, flush/close, publish binding.json atomically WITHOUT overwrite on the same volume (hard-link the flushed temp to the absent final, or an OS atomic no-replace rename; never check-then-replace/copy), sync directory where supported, then read/validate final and compare exact expected bytes and origin before reporting success. A publisher that finds an existing final must read/compare it, never replace it. Fail unsupported filesystems instead of falling back to overwrite/copy. A process crash leaves either no final or the complete final, not partial authority.
3. Final absent with only binding.json.tmp in addition to an otherwise pristine spool: normal startup still refuses. A new EXPLICIT init under lock with producers stopped may discard that exact regular no-link temp and restart step 2. A temp is never authority, even if valid or for a different origin; no sends could have been authorized without the final. Unknown temp names or nonpristine inventory require operator investigation, no mutation.
4. Valid final plus binding.json.tmp: final wins. Normal operation validates the final and ignores the temp (never promotes it); explicit matching init also leaves that temp untouched (literal no-op). Unreadable/linked temp fails closed. Crash between final publication and temp unlink/directory sync is handled by this rule.
5. Final corrupt/unreadable/noncanonical/unsupported version: BINDING_INVALID; final absent on nonpristine spool: BINDING_MISSING. Never rewrite, infer from current config, infer from one item/ACK, copy a binding from another spool, or reset attempts. Retain all originals/evidence; explicit init cannot override these failures. Restoration of the SAME binding from a verified backup is separately authorized recovery, not an automatic worker action.

These are spool-level configuration failures: halt before HTTP or any item state/attempt/ack/quarantine/move mutation; diagnostic to stderr/operational log is allowed but do not move items to failed. Merely opening the root lock does not count as item progress. If initialization flush/publication/readback fails, do not start producer/worker. Existing process-crash and Windows directory-durability limits remain in force.

The bound origin is immutable for the lifetime of the spool, even after every item is uploaded or removed. There is NO in-place migration, rebinding, --force adoption, destination override or carrying existing ACKs/items into a spool bound to another origin in v1. To target a different server, initialize a separate pristine spool explicitly and create new capture intents; retain the old spool/ACKs at the original destination. This guarantee covers cooperative protocol operations and the specified process-crash model. An externally deleted binding plus removal of all item/history files cannot be distinguished from a never-used pristine directory; arbitrary deletion is unsupported corruption, not an authorized reset. Operators must restore the same binding from backup and must not invoke init on such a previously used root. No claim of detecting that erased history is made. This replaces revision 1's unspecified operator migration sentence. No change to server request identity, API/manual behavior, receipt retention or fingerprint is implied.

### 7.2 Binding validation during work

Before queue discovery/recovery or any item mutation on startup/restart, canonicalize the configured origin and validate binding.json; require equality. Keep this canonical configured origin and the validated binding value immutable for that process. Do not hot-reload a destination; changed configuration requires restart and the same equality check.

Before every HTTP attempt AND before its IN_FLIGHT/attempt-count write, reread/validate final binding and compare it to the immutable startup values. Build each HTTP URL by concatenating the immutable validated bound origin with the fixed API path and validated UUID components; never use a supplied absolute URL, generic URL-join override, newly read config or manifest. Revalidate before EVERY item/spool-progress mutation, including initial state/initialized creation, RETRY_WAIT, FAILED, diagnostic-file writes and quarantine, not only HTTP. Also revalidate before recording ACKED, each acknowledged directory move/final UPLOADED write, and every recovery/requeue item transition, including those that send no HTTP. A missing/corrupt/mismatched binding halts with the previous durable item state intact. After a response arrives, binding failure must prevent ACK persistence/move; the already counted attempt remains and same-origin replay can recover later. Endpoint continuity validation precedes existing acknowledgment field validation; response/ack JSON is unchanged.

The spool lock serializes agents/init; all supported writers honor immutable binding. A read/check is not a security defense against an external actor replacing files between instructions. Such modification is unsupported corruption; URLs still use the immutable validated startup destination and later checks halt, never switch origin. Do not claim filesystem locking protects against arbitrary external edits.


## 8. Retry, matching acknowledgment and directory recovery

Binding checks in section 7.2 precede every transition below, including retry/failure recording and persisted-ACK recovery; failure halts the spool with no network or item mutation.

HTTP defaults: connect 5s, read/write/pool 30s each, overall attempt deadline 120s. Bound success/error response reading to 128KiB; no automatic redirects. Timeout/disconnect is an unknown outcome, not proof of failure.

Max 8 HTTP attempts per retry epoch, including first. After attempt n, B=min(300,2^(n-1)) seconds; equal jitter uniform [B/2,B]. Persist chosen next_attempt_at before waiting; pre-send IN_FLIGHT stores this fallback deadline for response loss. Tests inject wall/monotonic clocks and RNG. Retry network/DNS/timeout, 408, 429, 5xx, and only 409 UPLOAD_IN_PROGRESS. Other 4xx including 425 and IDEMPOTENCY_CONFLICT are terminal; 3xx is terminal ENDPOINT_REDIRECT and never followed. Backend v1 emits no 425.

Valid Retry-After delta-seconds or HTTP-date is a MINIMUM: max(backoff deadline, receipt-time + server delay). No 300s cap on a valid server delay. Invalid/missing uses backoff with diagnostic; Backend emits positive delta-seconds. Persist updated deadline before sleep. Persist UTC for restart and use monotonic waiting within a run. Backward clock changes delay conservatively; forward jumps can hasten retry but cannot change identity/server lease. Parse overflow/unrepresentable dates as invalid with diagnostic, never wrap into a negative wait.

Malformed/mismatched success is PROTOCOL_ACK_MISMATCH and retryable up to the same limit, never uploaded. After exhausted IN_FLIGHT or failure of attempt 8, persist FAILED/RETRY_EXHAUSTED with last safe diagnostic and retain files indefinitely. Other terminal responses similarly retain data. No auto-reset, ID rotation, auto-pruning or infinite retry.

Explicit operator retry of unchanged failed intent increments retry_epoch, sets epoch_attempt_count=0, preserves lifetime attempt_count/identity/diagnostics, persists PENDING before failed->pending atomic move. Recovery completes failed/PENDING only if retry_epoch>0; otherwise quarantine. Corrected bytes/context require a new explicit intent/UUID while retaining old evidence. Disk-full/permissions halt with last durable state intact.

Only 201 + Idempotency-Replayed:false or 200 + Idempotency-Replayed:true qualifies for acknowledgment. Require JSON Screenshot with:
- matching project_id, client_upload_id, build/locale/category/situation/source;
- matching metadata_version and complete JCS-equivalent metadata, sanitized original_filename;
- exact file_hash, size_bytes, media_type, width, height;
- valid server UUID id, UTC uploaded_at and exact relative content_url for project/id;
- matching Location detail URL and valid server X-Request-ID.
Require all known field types; ignore unknown additive response fields. Never accept status/hash alone. Body's project/client ID is the stable receipt identity; full context/facts comparison supplies the same fingerprint inputs, so no redundant public fingerprint header is needed. API route/manifest pin protocol v1. No per-ack GET is required; actual content/Web verification remains acceptance work.

Persist ACKED with full validated Screenshot, status, Location, Idempotency-Replayed, X-Request-ID and received_at in ack FIRST. Then atomic no-overwrite directory rename pending->uploaded preserving all files. Finally persist UPLOADED. Recovery under lock:
- pending ACKED -> complete move, no POST;
- uploaded ACKED -> persist UPLOADED, no POST;
- uploaded UPLOADED -> stable;
- pending IN_FLIGHT -> same-ID retry after saved deadline;
- pending FAILED -> complete failed move;
- failed PENDING with retry_epoch>0 -> complete explicit requeue move.
Physical directory alone never proves success. Uploaded without valid ack/state, duplicate identity across roots, target collision or corrupt ack is quarantined/reported; never merge/overwrite/delete copies. Validate ack again during recovery against immutable manifest, not merely the state enum. All ready incomplete/failed originals survive. Safe transition logs include scoped ID/time/attempt/code, never binary/secret/raw invalid payload.

## 9. Required failure trace

Planned product checks below are NOT_RUN. Separate-process termination, multi-connection PostgreSQL and actual integration evidence are required; mocks alone cannot prove these invariants.

| ID | Boundary | Required result / evidence owner |
| --- | --- | --- |
| F01 | Offline / process restart | Same original hash/Unicode/ID/count/deadline; 06, AC01/02 |
| F02 | Image-only / manifest-only / temp / truncated / missing ready | No HTTP; originals retained; 06, AC01 |
| F03 | Crash after each image/manifest/ready rename | Only complete matching ready is eligible; 06 |
| F04 | Invalid Unicode/duplicate keys/numbers/version/MIME/hash | Safe rejection before receipt/publication; valid emoji/combining data survives; 03/06 |
| F05 | First/completed same request/restart replay | 201 then 200 same resource/time; one receipt/Screenshot; 03 real PostgreSQL |
| F06 | Same ID different bytes or same hash changed context/name/source | Terminal 409; existing winner untouched; 03/06 |
| F07 | Different IDs same hash; same UUID other project | Distinct rows, no hash deduplication; 03 |
| F08 | Concurrent reserve / renew / active competitor | One owner, DB clock and Retry-After; 03 |
| F09 | Exact expiry / takeover / delayed stale publish/finalize | Generation/token fence, unique attempt object, no winner deletion; 03 |
| F10 | Unknown first reservation / renewal commit | Unique-key arbitration for absence; locked primary recovery; 03 |
| F11 | Stage/publish failure or crash after publication | No visible incomplete Screenshot, retain orphan; 03 |
| F12 | Known rollback vs late/ambiguous commit | Atomic receipt+Screenshot, no deletion on uncertainty; 03 |
| F13 | Commit then lost response / both process restarts | Same-ID replay, one Screenshot, matching local ack; 03+06 actual integration |
| F14 | Stale cleanup / expired receipt / unavailable primary / partial inventory | Protect winner and recoverable candidate, fail closed, 24h/exclusive rule; 03 |
| F15 | Missing/mismatched committed original | Keep row/receipt, 503 content and alert; 03 |
| F16 | Two local agents / crash before or after send | OS lock, persisted count/deadline, immutable resend; 06 |
| F17 | Backoff/Retry-After/clock jumps/exhaustion/terminal errors | Exact persisted policy, retained originals/diagnostics; 06, AC02 |
| F18 | Wrong/missing success ID/hash/context/status/header/Location | Never ACKED/UPLOADED; bounded protocol retries; 06 |
| F19 | State temp/replace / ACKED / rename / UPLOADED crash | Recover old valid state or matching ack, no duplicate intent; 06 |
| F20 | Corrupt/missing state / full disk / permission / collision | Quarantine/halt, no overwritten originals or false success; 06 |
| F21 | Fresh/additive migration and indefinite receipts | Preserve historical IDs/hash/Unicode/paths, no identity expiry; 03 |
| F22 | Actual agent->Backend/DB/storage->Web | Source/full metadata/ID/list/detail/original hash + manual smoke; 03/06/04, AC04 |
| F23 | JCS order/default/null/number/Unicode/filename vectors | Cross-implementation canonical bytes/hash equality and distinctions; 03/06/08 |
| F24 | Manual/header/source schema/filter | Manual 201/null unchanged, invalid pairings rejected, expanded read types; 03/04 |

| F25 | Explicit binding init / concurrent init / no-overwrite publication crash | One durable canonical authority, final readback; no producer/HTTP before final; 06, AC01/03 |
| F26 | A->B restart with PENDING/RETRY_WAIT/IN_FLIGHT/ACKED/UPLOADED | Fail before network/attempt/ACK/move; preserve old spool and receipt provenance; 06, AC01/03 |
| F27 | Binding absent/corrupt/noncanonical/mismatch or partial temp | Exact pristine/init recovery matrix; no adoption of nonempty spool, no authority overwrite; 06 |
| F28 | Binding changes after response / before retry, FAILED, ACKED, move, UPLOADED or recovery write | Last durable state unchanged; whole-spool halt, no item quarantine/false success; 06 |
| F29 | Origin aliases, parser repairs, host/port/IPv6 boundaries | Only defined canonical equivalents equal; rejected origins never reach HTTP; 06 |
| F30 | Attempted in-place rebind/ACK transfer; erased-history corruption boundary | Refuse supported rebind even empty; preserve originals/ACK; document unsupported external erasure, no false detection claim; 06 |

AC01 = AC-P2-01, AC02 = AC-P2-02, AC03 = AC-P2-03 (F05..F16/F18..F21/F23), AC04 = AC-P2-04. Use disposable databases/storage and synthetic images only. Fresh and additive migration tests start from populated Phase1 fixtures; no user downgrade/reset. Add fault barriers at reserve commit, publication, finalize commit, response, each queue state/rename; avoid sleeps/global ambiguous monkeypatches. Historical Phase1 tests are not current Phase2 results.

## 10. Consultation decisions and ownership

Revision 2 addresses R08-P2-ARCH-001 only: owner06 implements immutable spool-root binding/init/validation in config.py, spool.py, producer.py, worker.py, recovery.py, requeue.py and uploader-local __main__.py with tests/upload coverage F25..F30. No new dependency, API/manual/fingerprint/DB schema or common CLI change. README init/failure runbook still requires PM claim. Existing ACKs never migrate to another destination. [Revision 2 evidence](../../.orchestration/reports/ARCH-UPLOAD-001-revision-2-02.md) preserves revision1 snapshots and required counterexample mapping; independent closure pending.

Read preparation reports: [Backend03](../../.orchestration/reports/PREP-BACKEND-UPLOAD-001-03.md), [Uploader06](../../.orchestration/reports/PREP-UPLOAD-001-06.md), [Frontend04](../../.orchestration/reports/FRONTEND-UPLOAD-CHECK-001-04.md). All are design inputs; PM accepted preparation, not this contract. Detailed question-by-question disposition is in [author report](../../.orchestration/reports/ARCH-UPLOAD-001-02.md).

- 03: accept additive migration, primary DB clock/fence, receipt-aware maintenance and fault seams. Replace cross-generation deterministic reuse with a deterministic key per RESERVED generation and no worker final-object deletes. Accept bounded buffering (not a peak-RAM promise). Resolve schema/UUID/header/fingerprint/status questions in sections 1..6.
- 06: accept marker-last same-volume publication and immutable intent; ready.json includes manifest digest rather than an empty marker. Replace SQLite with atomic state plus process lock (section 7); no queue DB/rebuild authority. Replace proposed cap60/full jitter/capped Retry-After with cap300/equal jitter/uncapped server minimum (section 8) to prevent hot loops and premature server retries. Keep 8 attempts/connect5/read-write30; add total120/response bounds. Replace terminal malformed ack with bounded same-ID retries; strict match is mandatory. No public fingerprint required because returned scoped ID plus all fingerprint inputs are compared.
- 04: accept separate manual write and expanded read types, full safe metadata/version/non-null ID detail display, existing source fallback; no source-filter/replay UI expansion. automation source remains automation when forwarded by uploader.
- Windows limitation is explicit process-crash durability, not certified sudden-power-loss resilience. Unsupported filesystems fail closed. This is an implementation acceptance boundary, not a hidden guarantee.
- Retention is indefinite for receipts and queue originals. Recovery is manual after arbitrary disk corruption/unsupported power-loss; never label corrupt/missing ack as success.

File assignments after independent acceptance AND PM READY:
03 exclusively owns backend/ and tests/backend/, including additive 0003 migration, receipt models/repository/service, middleware retry header behavior, canonicalization, CORS/OpenAPI and maintenance; do not rewrite applied 0001/0002.
06 exclusively owns agent/screenshot_upload/ and tests/upload/, including producer helper, manifest/state/lock/client/retry/recovery and actual integration harness. Choose uploader-local python -m agent.screenshot_upload and agent/screenshot_upload/__main__.py; common agent/__main__.py is NOT needed.
04 owns PM-allocated FRONTEND-UPLOAD-001 in frontend/ and tests/frontend/ for manual/read type separation and required detail metadata, targeted tests/build/typecheck; later actual Web verification separately activated.
02 owns this contract, scoped references and own evidence only. 08 independently reviews exact revision/hash; PM alone owns YAML/AC/Phase/DECISIONS and implementation promotion.

Shared-file requests remain gated, not edit authorization: PM should claim pyproject.toml for 06's agent packaging and explicit runtime httpx optional extra while preserving Backend settings; use an agent-owned reproducible agent/screenshot_upload/requirements.lock (06) with resolved runtime/test and JCS dependency versions after PM approval, not Backend's lock. Backend03 maintains its own reproducible JCS dependency path and coordinates any shared pyproject change with PM/06 sequentially. README.md uploader CLI/runbook section only for 06 after PM claim/behavior exists; no root config/Compose/env/common CLI changes required by this contract. New dependencies require reproducible installs and JCS vectors on both platforms. No schema implementation/shared schema file is created by Architect.

Report exact revision/hashes and static checks, distinguish NOT_RUN product acceptance, request READY_FOR_REVIEW via own handoff. No product implementation, Commit or Push. Highest difficulty (persistent cross-process identity/recovery); requested gpt-6-astra / medium, actual application unverified.
