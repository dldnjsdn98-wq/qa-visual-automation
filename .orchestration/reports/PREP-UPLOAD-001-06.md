# PREP-UPLOAD-001 / owner 06 preparation report

- Prepared: 2026-09-13 KST
- Status proposal: preparation complete; submit to PM/Architect for consultation. This does not activate `UPLOAD-001` or claim any Phase 2 acceptance result.
- Difficulty: 중. The work is a bounded inventory and deterministic test design within the existing Phase 2 plan; no protocol or persistence implementation is included.
- Requested model / effort: `gpt-5.6-sol` / `medium`.
- Actual model: 실제 적용 미확인. Dispatch recorded the requested value, but no execution metadata available to this task proves the applied model.

## Scope and current evidence

Read-only inspection covered `agent/`, `tests/upload/`, the `captures/{pending,uploaded,failed}` conventions, root dependency/CLI declarations, current Phase 2 state and accepted architecture cross-references. The only changed files for this task are this report and `.orchestration/handoffs/PREP-UPLOAD-001-06.md`.

Current repository evidence, checked on 2026-09-13:

- `.orchestration/PROJECT_STATE.yaml` identifies Phase 2 as IN_PROGRESS for contract/preparation. `.orchestration/TASKS.yaml` identifies `PREP-UPLOAD-001` as READY with Phase 1 ACCEPTED as its dependency.
- `.orchestration/ACCEPTANCE.yaml` keeps AC-P2-01 through AC-P2-04 at NOT_RUN. No Phase 2 product verification is claimed.
- `agent/screenshot_upload/`, `agent/visual_automation/`, and `tests/upload/` each contain only `.gitkeep`; there is no uploader package, queue implementation, CLI implementation, or upload test harness to extend yet.
- `captures/pending`, `captures/uploaded`, and `captures/failed` exist with only `.gitkeep`. `.gitignore` excludes their runtime contents while retaining `.gitkeep`.
- `README.md` lists `python -m agent screenshot-upload` as a planned CLI, not an implemented command. There is no common `agent/__main__.py` entrypoint.
- `pyproject.toml` packages only `backend*`; it has no `agent*` package discovery or console script. Python is constrained to 3.12. Runtime dependencies do not include an uploader HTTP client; `httpx` is currently a dev dependency and is present in `backend/requirements.lock` for Backend/test use.
- Accepted Phase 1 API behavior still rejects `Idempotency-Key`, requires `source=manual`, and returns `client_upload_id=null`. Current Phase 2 architecture text is future guidance, not an approved executable uploader contract.

Historical results were not rerun. Phase 1 acceptance, Backend tests, migration checks, and browser evidence remain dated owner/Reviewer evidence referenced by the PM activation handoff. They do not establish AC-P2-01..04.

## Proposed producer and queue boundary

This is a consultation proposal for Architect 02, not an implementation decision.

1. A producer allocates one UUID and one item directory on the same local volume under `captures/pending`. The UUID becomes the immutable `client_upload_id` and directory identity.
2. It writes the original image and versioned manifest to temporary names, flushes each file, atomically renames each to its final immutable name, then publishes one zero-length ready marker last. The item is discoverable only when the ready marker and both final payload files exist.
3. The ready marker must never compensate for missing durability. The contract must define the supported durability guarantee on Windows, where Python has no portable directory-fsync equivalent, and require all atomic renames to remain on one filesystem.
4. The uploader validates marker, schema/version, UUID-directory agreement, exact byte count/hash, filename policy, source, scoped IDs, metadata constraints and supported version before importing the item into its queue state. It never uploads temporary, incomplete, mutable, or corrupt items.
5. Keep the manifest and original immutable. Store attempts, next-at time, last safe error, claim owner/expiry, terminal status and acknowledged receipt in a separate SQLite queue database. Use injected clock/random/network/crash seams. SQLite avoids a new queue library and gives transactional claims/restart recovery.
6. Make the local database authoritative for upload/ack progress. After a matching server receipt is durably recorded, moving the item directory from pending to uploaded is a resumable materialization step. A crash before that move safely replays the same UUID. A terminal outcome records diagnostics and retains the original before a resumable move to failed.
7. Default to one uploader process. If multi-process operation is supported, claim with one SQLite transaction and an expiring claim token; every update must compare that token. The contract must define whether an expired local claim may be taken over and how a stale process is fenced.

Suggested owned implementation modules after contract approval and PM promotion:

| Module | Responsibility |
| --- | --- |
| `agent/screenshot_upload/manifest.py` | Closed, versioned manifest model; canonical validation; immutable identity checks |
| `agent/screenshot_upload/spool.py` | Ready-item discovery, same-volume atomic transitions, partial/corrupt quarantine and restart reconciliation |
| `agent/screenshot_upload/queue.py` | SQLite schema/migrations, transactional claims, persisted attempts/backoff/ack and token fencing |
| `agent/screenshot_upload/retry.py` | Retry classification, Retry-After parsing/capping, injected clock and deterministic jitter |
| `agent/screenshot_upload/client.py` | Bounded multipart request and strict response/header/receipt decoding |
| `agent/screenshot_upload/worker.py` | Claim-upload-ack state machine; no capture production or Backend persistence logic |
| `agent/screenshot_upload/config.py` | Validated local paths, API origin, timeouts and retry limits; no credentials in logs |
| `agent/screenshot_upload/__main__.py` | Uploader-specific command until a shared `agent` CLI is explicitly assigned |
| `tests/upload/` | Unit, separate-process crash/restart, fake-clock/network, filesystem recovery and actual Backend integration tests |

The common `agent/__main__.py`, root `pyproject.toml`, dependency lock/constraints, root README and shared configuration are outside owner 06's current exclusive scope and require a PM file claim.

## Contract questions and recommended defaults for Architect 02

These points must be settled before queue/network implementation:

### Readiness and manifest

- Specify the exact directory/file names, manifest media/encoding, `manifest_version`, ready marker name/content, same-volume requirement, and publication ordering. Define whether a ready marker is an empty file, a rename of a prepared marker, or a manifest state field; the recommendation is a separately fsynced marker renamed last.
- Define the minimum crash/power-loss guarantee on Windows and Linux. File flush plus same-volume atomic rename is available; portable Python directory fsync is not available on Windows. State whether sudden power-loss durability on Windows is a documented limitation or requires a platform-specific implementation.
- Define whether an image-final/manifest-final pair without a marker remains indefinitely unready, may be repaired by its producer, or is quarantined after an age threshold. Uploader must never infer readiness from age alone.
- Define the closed manifest fields and normalization: UUID scope, project/build/locale/category/situation IDs, `source`, original filename, media type, exact byte count, expected SHA-256, metadata version/context, creation time if any, and canonical JSON rules. The uploader should compare the actual bytes with the manifest before every first send and recovery send.
- Confirm that any byte, filename, source, scoped-ID, metadata/default or manifest-version change requires a new UUID. Same UUID with changed semantics must become a local terminal conflict rather than silently rewriting identity.
- Define handling for unsupported version, malformed UTF-8/JSON, duplicate keys, residual surrogates/NUL, wrong hash/size, missing pair member, extra files, and UUID/path traversal. Recommendation: never submit; retain original evidence and write a safe diagnostic without echoing hostile input.

### Queue claim and restart

- Confirm SQLite as the local durable state store and identify its owned location. Define schema/version migration policy, corruption handling, backup expectation and whether queue DB loss can rebuild safe PENDING records from immutable ready items without losing acknowledged state.
- Decide single-process-only versus concurrent workers. Recommendation for initial Phase 2: one process with a process lock; still use transactional per-item claim tokens so restart tests exercise stale-claim recovery. If multiple workers are allowed, specify lease duration, renewal, authoritative clock and stale-token fencing.
- Define reconciliation for DB/item-directory disagreement at every pending-to-uploaded/failed rename boundary. A recorded matching acknowledgment must remain authoritative; an uploaded directory without recorded acknowledgment must be revalidated or replayed, never assumed successful from location alone.
- Define whether terminal items can be manually requeued. Recommendation: require an explicit operator command that preserves the same UUID/payload for transient exhaustion and requires a new UUID for corrected payload/metadata.

### Retry and acknowledgment

- Define retryable transport failures and HTTP/error codes. Recommended retryable set: connection/DNS/timeout/response-loss, 408, 425, 429, `409 UPLOAD_IN_PROGRESS`, and 5xx. Recommended terminal set: malformed local item, 400/401/403/404/413/415/422, `409 IDEMPOTENCY_CONFLICT`, unsupported contract version, and malformed/mismatched success response. Exact server error codes remain authoritative.
- Define initial defaults. Recommendation for review: 8 attempts; exponential base 1 s, factor 2, cap 60 s; deterministic full jitter in `[0, computed_delay]`; honor valid delta-seconds or HTTP-date `Retry-After` with a 300 s cap; connect timeout 5 s and read/write timeout 30 s. Persist `attempt_count`, chosen delay, absolute next-at UTC and safe error category before sleeping. Inject wall clock and random source so tests contain no real waits. Architect should accept or replace every number.
- Specify clock rollback/forward behavior and whether `Retry-After` overrides or lower-bounds local backoff. Recommendation: use persisted UTC for restart scheduling, clamp negative delay to zero, and choose the larger of server delay and local randomized delay within the global cap.
- Define the exact success matrix: only 201 first-create or 200 completed-replay; required replay header behavior; response schema/version; and how to treat missing, malformed or contradictory headers.
- A success acknowledgment should match project and all scoped IDs, `client_upload_id`, source, normalized filename, metadata version/context, server `file_hash`, size/media/dimensions as applicable, plus a server-returned fingerprint/version or receipt identity. The current Screenshot response alone does not provide an independently comparable request fingerprint. The contract should add enough receipt data to prevent a syntactically valid but unrelated 200/201 from moving the original to uploaded.
- Define response-loss after server commit: retry exactly the same UUID and immutable payload until a matching completed replay is received. Local attempt exhaustion retains the original and diagnostics; it does not create a new UUID automatically.

## Deterministic failure matrix proposed for `tests/upload/`

All rows are planned and NOT_RUN. Crash cases should run the worker/producer in a separate process and terminate at named injected barriers; restart launches a fresh process against the same temporary spool/SQLite database. Fake clock/random/network adapters eliminate sleeps and nondeterminism.

| ID | Injection / setup | Expected invariant | AC |
| --- | --- | --- | --- |
| P01 | Crash while writing image temp | No ready scan result; temp retained/recoverable; no request | P2-01 |
| P02 | Image final, manifest absent/temp | No request; original retained | P2-01 |
| P03 | Manifest final, image absent/temp | No request; diagnostic only | P2-01 |
| P04 | Both final, marker absent | No request; producer may resume marker publication per contract | P2-01 |
| P05 | Marker present with truncated image or wrong size/hash | No request; terminal/quarantine evidence retains bytes | P2-01, P2-02 |
| P06 | Malformed/unsupported/Unicode-invalid manifest | No request; safe diagnostic; no path escape | P2-01, P2-02 |
| P07 | Crash immediately after marker publication | Fresh process discovers exactly one item with same UUID/bytes | P2-01 |
| Q01 | Two scans/imports of one ready item | One queue identity and one immutable payload | P2-01, P2-03 |
| Q02 | Crash after durable claim before request | Claim expires/recovers; same UUID/bytes retried | P2-01, P2-03 |
| Q03 | Two workers contend for claim | One token sends; stale token cannot update state | P2-03 |
| R01 | Offline connection failure then restart before due time | Attempt/delay persist; no early retry | P2-01, P2-02 |
| R02 | Retry-After delta/date with fake clock | Contract precedence/cap is exact and persisted | P2-02 |
| R03 | Clock moves backward/forward across restart | Delay clamps per contract; no busy loop/overflow | P2-02 |
| R04 | Retryable failures exhaust configured attempts | Failed state and safe diagnostics persist; original remains | P2-02 |
| R05 | Terminal 4xx or idempotency conflict | No automatic retry; original/manifest/diagnostic retained | P2-02, P2-03 |
| A01 | 201 with wrong UUID/hash/project/context | Never record ack or move original | P2-02, P2-03 |
| A02 | 200/201 malformed JSON, missing receipt fields or contradictory replay header | Never record ack; retain diagnostic/original | P2-02, P2-03 |
| A03 | Server commits then response is lost | Restart resends same UUID/bytes; 200 replay resolves to one screenshot | P2-03 |
| A04 | Same UUID with changed bytes/filename/metadata | Local rejection and/or server 409; never overwrite acknowledged identity | P2-03 |
| A05 | Same bytes with different UUIDs/context | Two independent uploads; hash alone does not collapse them | P2-03 |
| S01 | Crash after matching ack is committed locally, before directory move | Restart completes uploaded move without another logical item | P2-01, P2-03 |
| S02 | Crash after directory rename, before transition cleanup | Restart reconciles to acknowledged uploaded state | P2-01, P2-03 |
| S03 | Terminal state committed before failed-directory move | Restart completes failed move; original and diagnostics preserved | P2-01, P2-02 |
| I01 | Actual Backend/PostgreSQL commit plus response loss and both process restarts | One server screenshot/receipt and matching local uploaded item | P2-03, P2-04 |
| I02 | Multilingual metadata/filename and original bytes through agent to Web readback | Exact Unicode, context, bytes/hash/source visible; manual prior upload unchanged | P2-04 |

Additional state-machine property tests should assert that no transition deletes the only original, no unready item calls the client, only a durable matching acknowledgment enables uploaded state, attempt count never decreases, and a stale claim token cannot finalize.

## Dependency and shared-file request

Request PM/02 reserve the following minimal shared changes for the later `UPLOAD-001` implementation, after contract acceptance:

1. `pyproject.toml`: include `agent*` in package discovery and expose either the planned common `python -m agent screenshot-upload` entrypoint or approve uploader-local `python -m agent.screenshot_upload`; add `httpx>=0.28,<1` as a runtime/agent optional dependency rather than relying on a dev-only dependency.
2. Reproducible dependency artifact: extend an approved cross-platform lock/constraints workflow to cover the agent runtime and tests. Do not repurpose Backend's lock without PM/Backend coordination.
3. `README.md`: replace the planned CLI line with exact queue paths, configuration, one-process/worker policy, exit codes, safe manual retry/requeue procedure and supported durability limitations only after behavior exists.
4. Any root/shared config or `agent/__main__.py`: assign exclusive ownership before edit. Owner 06 can avoid a shared entrypoint initially by implementing `agent/screenshot_upload/__main__.py` within its owned tree.

No third-party queue, retry or file-lock dependency is currently justified. Standard-library `sqlite3`, `uuid`, `hashlib`, `json`, `pathlib`, `argparse`, `email.utils` and injected abstractions are sufficient for the proposed core. Reassess only if the approved contract requires platform-specific power-loss guarantees or multi-process locking that cannot be met safely.

## Commands, environment and results

Working directory for every command: `C:\Dev\qa-visual-automation`; shell: PowerShell; date: 2026-09-13 KST.

- `rg --files ...` and targeted `rg -n ...` over orchestration, agent, tests/upload, docs, dependencies and upload references: PASS for source inventory. One unrelated historical Reviewer temp directory returned access denied during a broad search; targeted reads succeeded and the inaccessible path was outside this task's scope.
- `Get-Content -Raw` / targeted line reads of the assigned state, acceptance, decisions, activation, Phase 2 plan, role prompt, architecture, README, pyproject, lock and handoff template: PASS for static evidence collection.
- `git status --short` and `git log -1`: PASS for preserving a heavily dirty user worktree and identifying current baseline commit `811b1e36199d424d83930f3381c7d71e537bc7d6`. No existing changes were modified.
- `Get-ChildItem` of agent/tests/upload/capture directories: PASS; only `.gitkeep` files were present in the owned implementation/test trees and runtime capture state directories.
- Project `.venv` availability/version command in owner 06's execution context: FAIL. The launcher reported that it could not create a process using the interpreter path recorded by the virtual environment, so Python/httpx/pytest runtime versions were not obtained in that attempt. This result establishes only the scoped command failure; it does not establish that the recorded base interpreter is missing. PM 01 subsequently reported that `Test-Path` for the interpreter recorded in `.venv/pyvenv.cfg` returned `True` and that an approved invocation of the same `.venv` Python successfully parsed and saved PM YAML in the same turn. Static lock inspection found `httpx==0.28.1` and `pytest==9.1.1`. Treat the differing outcomes as execution/permission-context evidence and recheck the runtime under the approved implementation context when `UPLOAD-001` is activated; this is not a model-capability issue and does not block read-only preparation.
- Test suites, services, network calls, real capture writes, queue mutation, Backend calls, migration and storage operations: NOT_RUN by explicit preparation scope. No unexecuted check is reported as PASS.

## Remaining risks and next conditions

- Architect 02 must resolve the readiness/durability, manifest canonicalization, claim/recovery, retry defaults and strict acknowledgment questions above in the reviewed contract.
- PM must accept this preparation and assign any shared files/dependencies before implementation.
- `UPLOAD-001` remains blocked until `ARCH-UPLOAD-001` and independent `REVIEW-ARCH-UPLOAD-001` are ACCEPTED/DONE, this preparation is accepted, file ownership is confirmed and PM explicitly promotes implementation READY.
- Actual AC-P2 verification requires separate-process crash tests and the real Backend/PostgreSQL/storage/Web path. The current empty trees and static proposal establish no product behavior.
- Persistent queue corruption and Windows sudden-power-loss durability may raise the later implementation difficulty if the approved contract requires guarantees beyond SQLite and same-volume atomic rename. Reassess then; no current upward reassignment is requested.
