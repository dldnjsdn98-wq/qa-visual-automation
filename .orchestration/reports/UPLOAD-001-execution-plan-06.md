# UPLOAD-001 execution plan / owner 06

Date: 2026-09-25 KST  
Task: `UPLOAD-001` / Screenshot Upload Agent  
Status: execution plan complete; product implementation remains `BLOCKED`  
Contract basis: `P2-UPLOAD-v1`, document revision 1, submitted SHA-256 `ab53b327517e6fd24bbff4b08c56a4d64f6dbda1a25f34a436e575858854ea4d`

## Status and evidence boundary

This report integrates the previously completed preparation and three bounded read-only support results. It does not reopen Phase 1, repeat the full contract audit, or claim contract/product acceptance.

- Current repository state keeps `UPLOAD-001` BLOCKED behind `ARCH-UPLOAD-001`, independent `REVIEW-ARCH-UPLOAD-001`, accepted preparation, exact file claims and PM READY promotion.
- AC-P2-01 through AC-P2-04 remain `NOT_RUN`.
- Per PM's 2026-09-25 instruction, the prior Reviewer disposition is an origin-binding `MAJOR` / `CHANGES_REQUESTED`, with the formal review artifact still being filed. At the last targeted repository read, `REVIEW-ARCH-UPLOAD-001-08.md` was not yet present. Therefore the exact final finding text and corrected contract revision/hash remain pending; revision 1 is planning input, not an implementation authorization.
- Expected origin-fix impact is limited to uploader spool/config/acknowledgment/CLI behavior on current evidence. This plan infers no Backend API, manual upload or persistent DB change from that finding.
- No product source, tests, captures, environment, PM YAML/DECISIONS, shared file, mobile proposal, Commit or Push was changed. The only task write is this report.

Difficulty is **상** because crash recovery, response-loss replay, strict acknowledgment and local original retention can cause false success or data loss. Requested parent/task model is `gpt-5.6-sol` / `high`; actual applied parent model is unverified.

## Recovered parallel support

| Work unit | Difficulty and reason | Requested model | Result / actual model |
| --- | --- | --- | --- |
| Producer, manifest, spool, OS lock, atomic state and crash barriers | 상: filesystem crash boundaries and restart recovery protect originals | `gpt-5.6-sol` / `high` | Completed read-only by subagent Bohr; actual model unverified |
| Client, retry, strict ack, moves/requeue and deterministic tests | 상: ambiguous responses and incorrect ack can create false success | `gpt-5.6-sol` / `high` | Completed read-only by subagent Raman; actual model unverified |
| Packaging, CLI, httpx/JCS, agent lock and shared-file claim | 중: bounded dependency/packaging design, no installation mutation | `gpt-5.6-sol` / `medium` | Initial run failed with 429; resumed subagent Beauvoir completed read-only. Actual model unverified. The 429 was an execution rate limit, not product failure or model-capability evidence |

The parent reviewed and reconciled all three results. In particular, the dependency result's proposed lean agent lock conflicts with the current root package's mandatory Backend dependencies if `pip check` is required; that unresolved packaging choice is explicitly retained below rather than silently accepted.

## Revision 1 implementation baseline

The previous SQLite proposal is superseded and must not be implemented. Revision 1 uses:

- immutable `original.png|jpg`, `manifest.json` and marker-last `ready.json`;
- atomic per-item `state.json` as progress authority and `initialized.json` as initialization evidence;
- directory scan as the queue index, with no queue database, local lease or local claim token;
- one OS-managed exclusive lock handle for the entire spool process lifetime;
- durable `ACKED` before pending-to-uploaded movement, then durable `UPLOADED`;
- durable `FAILED` before pending-to-failed movement;
- explicit retry epoch persisted as `PENDING` before failed-to-pending requeue;
- retained original, manifest, state and bounded diagnostics on terminal failure or exhaustion.

## Planned module boundaries after gate approval

All paths below remain prospective until independent contract acceptance, corrected origin contract, PM READY and exact file claims.

| File under `agent/screenshot_upload/` | Responsibility and public boundary |
| --- | --- |
| `durable_fs.py` | Local/same-volume checks; regular-file and symlink/reparse rejection; atomic create/replace/no-overwrite rename; file flush and supported directory sync. It does not interpret queue JSON. |
| `manifest.py` | Closed `ManifestV1`, request and file-fact models; strict UTF-8/JSON with duplicate-key, Unicode and binary64-domain validation; UUID/filename normalization; manifest/ready/directory binding. |
| `image.py` | Full bounded PNG/JPEG inspection and exact hash/size/MIME/dimensions verification without re-encoding. |
| `marker.py` | Closed `ReadyMarkerV1` and `InitializedMarkerV1`; exact manifest-byte digest and identity validation. No state transitions. |
| `producer.py` | UUID item allocation and original -> manifest -> ready marker-last publication; producer-only completion of its known unfinished intent. |
| `lock.py` | Nonblocking OS exclusive handle at `captures/.upload-agent.lock`; Windows/POSIX adapter. Existence or age never proves ownership. Lock failure exits before scan, mutation or HTTP. |
| `state.py` | Immutable `QueueStateV1`/`AckRecordV1`; pure transition functions and invariants for revision/count/epoch/times/error/ack. No filesystem, clock or HTTP access. |
| `state_store.py` | Size-bounded parse/load; first initialization; atomic state replacement with expected revision; initialized-marker repair without state reset. |
| `spool.py` | Scan pending/uploaded/failed; detect duplicate UUIDs/collisions/outside-root paths; no-overwrite directory moves; quarantine/report. No HTTP/retry policy. |
| `recovery.py` | Under-lock location x state reconciliation; revalidate ack against immutable intent; never infer success from physical location alone. |
| `canonical.py` | One approved RFC 8785/JCS adapter used for metadata equality and shared vectors; it does not replace duplicate-key/token-domain validation. |
| `retry.py` | Transport/status classification, equal jitter, Retry-After delta/date parsing, injected wall/monotonic clocks and RNG. |
| `client.py` | Bounded two-part multipart POST, timeout/response-size bounds and redirect prohibition; returns typed transport result and never writes queue state. |
| `ack.py` | Strict 201/create or 200/replay validation across headers, URLs, IDs, context, metadata and file facts; returns only a validated `AckRecordV1`. |
| `requeue.py` | Explicit unchanged-intent retry epoch transition and validation; corrected payload always requires a new UUID. |
| `worker.py` | Revalidate intent -> durable IN_FLIGHT -> HTTP -> durable retry/FAILED/ACKED orchestration using injected collaborators. |
| `faults.py` | Named crash-barrier interface; production no-op and test child-process termination implementation. |
| `config.py` | Paths, approved origin binding abstraction, timeouts and safe logging configuration. Precise origin persistence is deferred to corrected contract. |
| `__main__.py` | Uploader-local `python -m agent.screenshot_upload` commands for run/status and approved explicit requeue/origin migration only. No common `agent/__main__.py`. |

`queue.py`, SQLite files and local worker leases are explicitly excluded.

## Atomic order and recovery authority

### Producer marker-last publication

1. Exclusively create `pending/<uuid>` on the validated local spool volume.
2. Write `original.tmp`; flush/fsync/close; no-overwrite rename to `original.png|jpg`; sync the item directory where supported.
3. Inspect final original and derive authoritative file facts.
4. Write `manifest.json.tmp`; flush/fsync/close; no-overwrite rename to `manifest.json`; sync directory.
5. Hash the exact manifest bytes. Write the closed `ready.json.tmp`; flush/fsync/close; rename to `ready.json` last; sync directory.
6. Producer relinquishes all immutable files. Uploader never infers readiness from age or stable size.

The supported guarantee is process termination/restart on a local filesystem with same-volume atomic rename and file flush. Windows sudden-power-loss durability is not claimed where directory flush is unavailable.

### Queue initialization and state replacement

1. Validate ready, manifest, original and all bindings before initialization.
2. Persist `PENDING` revision 1 to a same-directory state temp, flush/fsync/close, atomically replace `state.json`, then sync directory.
3. Persist and rename `initialized.json` only after state is durable; sync directory.
4. Do not send until both files validate.

For later transitions, write temp -> flush/fsync/close -> atomic replace `state.json` -> sync directory. A pre-replace crash leaves the previous valid state authoritative. A partial temp never resets attempts or ack. Valid state with a missing initialized marker repairs only the marker. Initialized evidence with missing/corrupt/mismatched state is quarantined, not reconstructed as fresh PENDING.

### Completion, failure and requeue

- Success: validate response -> persist `ACKED` with full ack -> no-overwrite `pending` to `uploaded` rename and parent sync -> persist `UPLOADED`.
- Terminal/exhausted: persist `FAILED` with safe diagnostic -> no-overwrite `pending` to `failed` rename. Preserve the original indefinitely.
- Explicit unchanged-intent retry: increment `retry_epoch`, reset only `epoch_attempt_count`, persist `PENDING` while still under failed -> no-overwrite `failed` to `pending` rename. Lifetime count, UUID, manifest digest and diagnostics remain.

## Retry and strict acknowledgment

HTTP defaults from revision 1: connect 5 seconds; read/write/pool 30 seconds each; overall attempt deadline 120 seconds; bounded response body 128 KiB; redirects disabled.

Each retry epoch permits 8 HTTP attempts including the first. For attempt `n`, `B=min(300,2^(n-1))` seconds and equal jitter is uniformly selected from `[B/2,B]`. The selected UTC deadline is persisted before waiting; monotonic time is used within a run. Valid `Retry-After` delta/date is a minimum and is not capped at 300 seconds. Invalid/overflow values fall back to local backoff with a safe diagnostic.

Retryable outcomes:

- DNS/connect/timeout/disconnect/unknown response loss;
- 408, 429 and 5xx;
- only 409 `UPLOAD_IN_PROGRESS`;
- malformed or mismatched nominal success as `PROTOCOL_ACK_MISMATCH`, within the same epoch limit.

Terminal outcomes include 3xx `ENDPOINT_REDIRECT`, 409 `IDEMPOTENCY_CONFLICT`, 425 and other non-retryable 4xx. Attempt 8 exhaustion becomes `FAILED/RETRY_EXHAUSTED`. Nothing rotates the UUID or deletes the original.

Only these success pairs may produce an ack:

- 201 plus `Idempotency-Replayed:false`;
- 200 plus `Idempotency-Replayed:true`.

`ack.py` must compare project/client ID, all scoped IDs, source, sanitized filename, metadata version and complete JCS-equivalent metadata, hash, byte count, MIME and dimensions. It must also validate server screenshot UUID, UTC uploaded time, exact relative content URL, matching Location and valid X-Request-ID. Known fields are strict; unknown additive response fields may be ignored. Status or hash alone never authorizes `ACKED`.

## Test and crash-barrier layout after activation

| Test path | Deterministic coverage / named barriers | Contract trace |
| --- | --- | --- |
| `tests/upload/unit/test_manifest.py` | Closed schema, duplicate keys, UTF-8/NUL/surrogate, binary64 domain, UUID/filename/digest/image binding | F02-F04, F23 |
| `tests/upload/unit/test_canonical.py` | UTF-16 key order, U+1F600/U+E000, 1/1.0/1e0, -0, safe integer, null/missing, arrays, exact combining Unicode | F23 |
| `tests/upload/unit/test_state.py` | Legal graph, revision monotonicity, lifetime/epoch counts, ack/error invariants | F16-F20 |
| `tests/upload/unit/test_state_store.py` | Temp/replace/sync, partial temp, old-valid state, initialized repair/quarantine, full disk/permission | F19-F20 |
| `tests/upload/unit/test_retry.py` | Classifications, attempt 1..8, equal-jitter boundaries, Retry-After delta/date/minimum, overflow, clock jumps | F17 |
| `tests/upload/unit/test_ack.py` | Correct create/replay plus every wrong/missing status, header, ID, hash, context, metadata, Location and request ID | F18, F23 |
| `tests/upload/unit/test_client.py` | Exact multipart, timeout, disconnect, 128 KiB response bound and no redirects | F13, F17-F18 |
| `tests/upload/unit/test_spool.py` | No-overwrite moves, collisions, duplicate roots, cross-volume/symlink/reparse/path escape rejection | F02, F19-F20 |
| `tests/upload/unit/test_requeue.py` | Epoch increment, lifetime preservation, changed-intent rejection | F17, F19-F20 |
| `tests/upload/process/test_producer_crash.py` | `producer.original.temp_fsynced/renamed/dir_synced`, same triplet for manifest and ready | F02-F03 |
| `tests/upload/process/test_state_crash.py` | `state.<transition>.temp_fsynced/replaced/dir_synced`, `initialized.temp_fsynced/renamed/dir_synced` | F16, F19-F20 |
| `tests/upload/process/test_process_lock.py` | Second agent exits before mutation/HTTP; forced owner termination releases OS handle | F16 |
| `tests/upload/process/test_worker_crash.py` | `worker.in_flight.durable`, `before_http`, `request_sent`, `response_received`, `ack_validated` | F01, F13, F16-F19 |
| `tests/upload/process/test_restart_reconciliation.py` | `pending_to_uploaded`, `pending_to_failed`, `failed_to_pending` renamed/parents-synced barriers and complete location x state matrix | F19-F20 |
| `tests/upload/integration/test_backend_response_loss.py` | Actual PostgreSQL Backend commit then dropped response; both processes restart; one Screenshot and 200 replay/matching local ack | F05, F13 |
| `tests/upload/integration/test_backend_conflict.py` | Same ID changed payload/context conflict; distinct IDs/same hash remain distinct | F06-F07 |
| `tests/upload/integration/test_agent_web_readback.py` | Agent->Backend/DB/storage->Web source/full metadata/Unicode/original hash plus unchanged manual 201 smoke | F22, F24 |

Test support belongs under `tests/upload/support/`: injected fake wall/monotonic clocks, deterministic RNG, scripted transport, same-volume synthetic spool factory and child-process crash runner. Crash tests use only temporary synthetic captures and fresh processes; no sleeps, real QA captures or global ambiguous commit monkeypatches.

## Parallel implementation batches after approval

The following write sets are disjoint so PM may assign them in parallel after the gate opens:

1. **Producer/spool/state work unit — 상 / Sol high requested.** Owns `durable_fs.py`, `manifest.py`, `image.py`, `marker.py`, `producer.py`, `lock.py`, `state.py`, `state_store.py`, `spool.py`, `recovery.py`, `faults.py` and their unit/process tests.
2. **Client/retry/ack/worker work unit — 상 / Sol high requested.** Owns `canonical.py`, `client.py`, `retry.py`, `ack.py`, `requeue.py`, `worker.py` and corresponding unit/process tests. It codes against reviewed interfaces from work unit 1 and does not edit those files.
3. **Packaging/integration work unit — 중 for packaging, 상 for actual integration.** Owns `config.py`, `__main__.py`, approved agent lock/input files and `tests/upload/integration/`; shared `pyproject.toml`/README remain separate single-writer claims. Actual Backend/PostgreSQL/Web tests start only after matching Backend/Frontend submissions exist.

The role-06 parent reviews merged interfaces, runs risk-selected checks, records exact environment/results and owns final `UPLOAD-001` report/handoff. Requested models do not prove actual application; every subtask must report requested and observable actual values separately.

## Dependency and shared-file claim proposal

### `pyproject.toml`

PM must appoint exactly one writer after owner 03 and 06 agree on JCS and packaging. Owner 06 requests only:

- package discovery expanded from `backend*` to include `agent*`;
- an `agent` optional dependency group containing `httpx>=0.28,<1` and the approved JCS package range;
- preservation of every Backend build/dependency setting;
- no console script and no common `agent/__main__.py`.

The exact patch is pending the single-writer claim and corrected contract. Current `httpx==0.28.1` in `backend/requirements.lock` is Backend/test evidence, not authority for the agent runtime version.

### JCS choice with owner 03

Candidate packages are `rfc8785` and `jcs`; neither package/version is selected by this report. Owner 03 and 06 must run the same F23 vectors on Python 3.12 Windows/Linux and compare exact canonical bytes/hash, UTF-16 key ordering, binary64/-0/safe-integer behavior, exact Unicode, errors, licensing and reproducible wheels. A repository-local tested equivalent is a fallback only if neither candidate satisfies the contract; custom numeric serialization is higher risk.

JCS serialization does not detect duplicate input keys or preserve raw numeric token facts, so strict parser validation remains separate in both Backend and agent.

### Agent lock

Requested exact owner/path after PM claim: owner 06, `agent/screenshot_upload/requirements.lock`. Optional input file `requirements.in` requires a separate exact-path claim.

The lock must pin hashes for Python 3.12 Windows/Linux, approved httpx/JCS and test dependencies, and contain no machine paths. It must not copy or append Backend's lock. Backend owner 03 maintains its own JCS/Backend lock path.

Packaging limitation still to resolve: root `pyproject.toml` currently declares Backend libraries as mandatory project dependencies. Therefore a lean agent-only lock followed by `pip install --no-deps .` cannot also pass `pip check` unless those base dependencies are present. PM/03/06 must choose one of:

1. Phase 2 minimal/unified distribution: agent lock resolves the current root base dependencies plus agent/test additions. This is larger but preserves metadata and clean `pip check`.
2. A separately approved packaging split making Backend and agent dependencies independent. This is broader shared-file scope and must not be inferred from the current claim.

This unresolved dependency packaging validation does not block submission of this execution plan; it blocks lock generation and clean-install acceptance after implementation activation.

Candidate future clean-install sequence, NOT_RUN:

```text
python3.12 -m venv <isolated-agent-env>
<env-python> -m pip install --require-hashes -r agent/screenshot_upload/requirements.lock
<env-python> -m pip install --no-deps --no-build-isolation .
<env-python> -m pip check
<env-python> -m agent.screenshot_upload --help
<env-python> -m pytest tests/upload -q
```

Run on Windows and Linux from clean isolated environments, then inspect wheel/package contents for `agent.screenshot_upload`. Exact executable paths and temp roots must remain environment-local and must not be committed.

### Other shared claims

| Path | Requested owner/scope | Gate |
| --- | --- | --- |
| `README.md` uploader section | One PM-assigned writer; document only implemented CLI, recovery, paths and durability limits | Behavior implemented and verified; exact PM claim |
| `agent/__main__.py` | No claim | Must remain unchanged; uploader-local CLI selected |
| `backend/requirements.lock` | Owner 03 only | Backend implementation claim |
| `docs/architecture/mobile-platform-support-proposal.md` | Separate mobile task only | Never edited by owner 06 |

## Origin-binding MAJOR / change-risk boundary

Revision 1 says Backend origin is bound when the spool initializes and destination changes require explicit migration, but its closed `state.json`/`initialized.json` schemas do not identify where that binding is durably authoritative. Per PM, Reviewer has classified this as MAJOR/CHANGES_REQUESTED and formal evidence is being filed.

Until a corrected contract revision is independently accepted:

- do not finalize origin CLI flags, environment-variable precedence, persisted schema or migration command;
- do not generate state/initialized fixtures that assume revision 1's incomplete binding;
- keep `config.py` behind a provisional `ResolvedOrigin`/`SpoolBinding` interface and keep `ack.py` independent of storage location;
- reserve tests for same-origin restart, changed configured origin fail-closed before HTTP, explicit migration preserving UUID/state/ack, and response/Location validation against the approved bound origin;
- expect changes in role-06 spool/config/ack/CLI modules only unless the filed review finding demonstrates a broader contract impact;
- infer no API/manual/DB change from current evidence.

If Architect 02 submits revision 2, owner 06 must replace the hash/revision basis and adjust only affected plan rows before implementation. No silent workaround is permitted.

## Verification performed and not performed

Current read-only checks from `C:\Dev\qa-visual-automation`:

- Read current owner prompt and targeted orchestration/task/acceptance/review-activation evidence: PASS for gate/status inventory.
- Read revision 1 sections 7-10, previous preparation and Backend preparation: PASS for execution-plan inputs.
- SHA-256 of `docs/architecture/phase-2-upload-contract.md`: PASS, matches submitted revision 1 hash above at inspection.
- Recovered two completed support results and resumed the dependency support after its initial 429; all three results integrated. 429 classified as execution limitation.
- `UPLOAD-001-execution-plan-06.md` did not previously exist; this is a new owner-06 report.

NOT_RUN by explicit pre-gate scope: Python/package installation, JCS candidate evaluation, test suites, product/queue code, captures, HTTP, Backend/PostgreSQL/storage/Web, migrations, service operations, clean install and mobile work. No NOT_RUN item is reported as PASS.

## Remaining gates and handoff

1. Reviewer08 files exact origin-binding MAJOR/CHANGES_REQUESTED evidence and reviewed hashes.
2. Architect02 submits a corrected revision; Reviewer08 independently returns ACCEPTED on the exact revision.
3. PM accepts preparation, confirms owner03/06 dependency choice, grants exact `pyproject.toml`, agent lock and later README claims, and promotes `UPLOAD-001` READY.
4. Owner06 rechecks contract hash, origin schema, file ownership and runtime context, then executes the three disjoint implementation batches above.

Until all conditions hold, `UPLOAD-001` remains BLOCKED, AC-P2-01..04 remain NOT_RUN and this report is planning evidence only.

