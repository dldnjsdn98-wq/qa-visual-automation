# ARCH-OCR runtime clarification / Architect02

- Date: 2026-09-25 KST
- Request: P3-RUNTIME-001 bounded read-only interpretation
- Contract: `docs/architecture/phase-3-ocr-contract.md`, accepted revision 2, SHA-256 `478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44`
- Input: `.orchestration/reports/BACKEND-OCR-001-runtime-reproducibility-addendum-03.md`, SHA-256 `aef7bea1af2d8c57938736be4ad8b95e6a7c4dc23e30d210ec314ce8c2274d18`
- Result: existing contract interpretation; no revision 3 and no product-code change by Architect02
- Difficulty / requested model: high / Sol high; actual model unverified
- Branch / commit: null / null

## Questions and binding interpretation

### Does 250 ms direct-child RSS sampling satisfy the accepted 2 GiB budget?

No, not as complete conformance evidence for an `AVAILABLE` profile.

The implementation in `backend/app/workers/ocr.py:220-232` samples only the direct adapter child PID and raises `ENGINE_RESOURCE_LIMIT` when one observation is greater than `RSS_LIMIT_BYTES`. `tests/backend/test_ocr_runner.py:232-239` proves that this monitor reacts to a sampled over-limit value. The real-runtime test at `tests/backend/test_ocr_runtime_integration.py:25-28` proves the configured constants and a successful run; it does not prove continuous enforcement of the limit.

This is a useful diagnostic and fail-closed path. It can miss a peak shorter than the polling interval, does not account for descendants, and treats one successful observation as sufficient before accepting output. It therefore cannot establish that the child remained within 2 GiB throughout the attempt.

The accepted contract sets the required behavior, not merely a configuration value:

- Section 10.2 says the parent terminates a child exceeding 2 GiB with `ENGINE_RESOURCE_LIMIT` and says a profile remains `UNAVAILABLE` when the target OS cannot enforce or observe the bound.
- Section 3 requires the parent to supervise and terminate/join its owned child and to prevent uncontrolled publication after loss of control.

The existing sampled-RSS test remains valid evidence for the sampled monitor only. It must not be cited as proof that the revision-2 resource budget is fully enforced.

### Are descendant accounting and cgroup/Windows Job Object hard caps required?

The contract does not require those APIs by name. It requires an outcome: the accepted runtime must enforce or reliably observe the 2 GiB child-memory bound and terminate the supervised workload when the bound is exceeded.

A periodic direct-PID sampler alone cannot provide that outcome because short peaks may occur between samples. An OS-enforced hard limit, or another mechanism with equivalent continuous enforcement, is therefore required before the affected profile may be `AVAILABLE`. Linux cgroup v2 containment and a Windows Job Object are the normal practical implementations, but a different mechanism is acceptable if platform tests demonstrate an equal or stronger bound without host-wide security or OS changes.

Descendant-tree accounting is conditional on the qualified workload:

- If qualification proves that the adapter child and all selected native libraries create no descendant processes during startup, inference, verification, timeout and error paths, enforcing the direct process is sufficient. Threads remain part of that process and its RSS.
- If descendants can be created, or their absence is not proven, the containment boundary must include the full descendant tree. Ignoring descendant memory would let the supervised workload evade the budget.

The hard-limit metric may be stricter than RSS, such as a process-tree/container memory charge capped at or below 2 GiB. A looser or incomparable metric is insufficient without evidence that it bounds RSS. The existing direct-PID sampler may remain as telemetry and an early error signal, but it cannot be the sole qualification mechanism.

Minimum Backend03 action for the resource issue:

1. Put the adapter workload into a platform containment boundary before it executes untrusted/native OCR work.
2. Enforce a memory limit at or below 2 GiB for the direct process, and for its descendants unless no-descendant behavior is independently proven.
3. On limit breach, prevent result publication/finalization, terminate and reap or quarantine the complete contained workload, and persist `ENGINE_RESOURCE_LIMIT` under the current fence.
4. Add Windows and Linux tests for sustained and short-lived over-limit allocation, descendant allocation or proven descendant absence, termination, no result write and profile `UNAVAILABLE` when containment cannot be established.
5. Retain actual platform/runtime evidence. A mocked RSS value proves classification only.

This is implementation work under the already accepted resource rule. It does not require revision 3 unless Backend03/PM wants to weaken the 2 GiB guarantee or redefine the measured subject.

### What does the 300-second deadline allow for cleanup?

The 300 seconds is one absolute productive-attempt budget beginning immediately after claim. Section 10.2 explicitly includes source read/verify/decode, model startup, OCR and matching. Section 3 says the whole attempt is bounded and requires termination/join of the owned child. A storage reader or OCR child does not receive a new budget after an earlier phase completes.

At the deadline:

- productive execution stops;
- no lease renewal, stage advance, result acceptance or finalization may rely on work completed after the deadline;
- cancellation/termination starts immediately;
- late local output is discarded and fencing remains authoritative.

The contract does allow a narrowly defined containment/reaping tail after the productive deadline. Section 3 explicitly states that failed stop/liveness keeps resources quarantined locally and prevents uncontrolled child publication. Operating-system termination and reaping are not guaranteed to complete at the same clock tick as the deadline. This is not a general `300s + cleanup allowance`, does not extend the attempt, and cannot authorize continued storage/OCR/matching work.

The current `_stop()` at `backend/app/workers/ocr.py:119-126` can add two fixed five-second joins, and `_execute()` can add a receiver join at lines 269-273. Those fixed waits cannot be counted as productive time or used to claim that the whole supervised workload always terminates within 300 seconds. Backend03's proposal to use the same absolute deadline, spend only its remaining time on graceful joins, and move immediately to kill/quarantine at expiry is consistent with revision 2.

Minimum Backend03 action for the deadline issue:

1. Keep the absolute deadline established at claim; source reading and every later phase share it.
2. Run potentially blocking source open/read/close in a terminable supervised process or equivalent cancellable boundary.
3. Pass the remaining absolute budget into every join/stop operation; do not append fixed waits to the productive attempt.
4. At expiry, hard-stop the contained workload immediately, discard output and stop renewing. Any bounded post-deadline reap/quarantine tail is containment only and must be measured separately.
5. If the workload cannot be terminated, keep it quarantined with no DB/storage publication authority and do not claim normal attempt completion. Recovery proceeds through lease expiry and fencing.
6. Test permanently blocked source read, deadline during each stage, partial IPC, termination failure, no finalize/write after deadline, and total productive elapsed time from claim.

The source-read and extra-join defects identified by Backend03 are product conformance gaps. PM has activated a bounded Backend03 correction. They do not require a contract change because revision 2 already defines the intended behavior.

### Does the 300-second budget require the database server to finish COMMIT before the local deadline?

No. Revision 2 does not impose a strict “the server may not finish a previously issued COMMIT after local second 300” rule.

The contract deliberately separates productive computation from authoritative database settlement:

- Section 10.2 enumerates source read/verify/decode, model startup, OCR and matching as work that must fit the 300-second attempt budget.
- Section 3 requires finalization to lock the job, validate the still-current unexpired generation/token fence, validate complete output, and commit results plus `SUCCEEDED` atomically.
- Section 3 explicitly says expiry during a short, already validated finalization commit cannot permit concurrent takeover.
- Sections 3 and 10.2 require ambiguous finalization to be resolved by a fresh locked primary read. A confirmed committed result is accepted; a live same fence with no results permits only the contract's bounded same-output retry; stale/expired/other-terminal state discards local output. Unresolved uncertainty causes no mutation.

These provisions would be contradictory if crossing the caller's local 300-second clock automatically invalidated a server transaction that had already acquired the lock and validated the DB-clock lease/fence. The authoritative validity test is the server-side lock plus fresh DB time before the commit, not whether the client receives the COMMIT acknowledgement before its local timer expires. `BEFORE_COMMIT` checking reduces late starts but cannot close the acknowledgement race and is not required to do so.

The allowed cases are:

1. A complete output is ready and finalization begins before the productive deadline. The transaction locks and validates a live fence. If PostgreSQL commits it and the reply arrives after the local deadline, the committed success remains valid.
2. The caller loses or times out waiting for the acknowledgement. It invalidates that connection and performs the contract's fresh-primary recovery. Recovery may occur after the productive deadline because it resolves existing durable state; it is not OCR/matching work and must not create a fresh run identity.
3. Recovery proves committed success: return/record that existing result. This is observation of the prior commit, not a new mutation.
4. Recovery proves rollback while the same fence is still live. The contract generally permits a bounded same-output retry, but after the productive deadline the runner must not start or retry finalization. It discards the output and may record timeout failure only under the separate safe-failure rule below.
5. Recovery cannot resolve, the fence is stale/expired, or another terminal state exists: quarantine/suspend the runner, issue no fail/finalize/renew/new claim mutation, and leave lease/reaper recovery authoritative.

Therefore strict prevention of every post-deadline server COMMIT would be a new and materially different requirement. It would need a separate exact contract revision and independent review; it is not part of P3-RUNTIME-001.

### May the supervised child own DB mutation authority?

No. Revision 2 is explicit:

- Section 3 says the parent runner supplies verified bytes/snapshot/profile, owns the heartbeat and all commits, and the Worker05 adapter has no direct DB/storage mutation.
- The timeout rule says an uncontrolled child cannot publish because the child has no DB write authority.
- Section 10.3 says the adapter has no DB credentials or commit methods and the parent owns source access, integrity, supervision, output validation and server IDs/timestamps.

The current Backend03 draft observed during this clarification (`backend/app/workers/ocr.py` SHA-256 `638f29322859a68add9530337f3135364938a34be2543161c67d1d5674cd70c4`) starts `_attempt_child`, constructs DB sessions inside it, and lets it renew, stage, finalize and fail. That arrangement conflicts with the accepted contract even if killing the process also kills its heartbeat thread. This is a draft owned by Backend03 and was preserved; Architect02 made no product edit.

The compliant boundary is:

- parent: claim, renew, stage, finalize, fail, ambiguity recovery and every DB connection/mutation;
- supervised child: bounded immutable input DTO, source read/decode/OCR/matching as approved by the parent, bounded IPC output, and no DB credentials or mutation API;
- parent: validate complete IPC output, stop/confirm child state, then perform the applicable short fenced mutation.

A separately supervised source-reader helper may receive a serializable storage specification, but it must not become a general attempt process with DB write authority. Immutable metadata/snapshot/profile should be resolved by the Backend parent into the bounded DTO; the OCR/matcher adapter never rereads current catalog.

Moving DB mutation back to the parent is required conformance work. It does not require revision 3. If Backend03 wants the attempt child to retain heartbeat/stage/finalize/fail authority, that is a narrow but material contract change requiring an exact revision and independent review before adoption.

### How may parent-owned synchronous DB work cross the productive deadline?

Parent ownership does not mean a synchronous driver call may block supervision of the child. The parent must preserve these independent facts:

1. The adapter/source workload can be stopped at the absolute deadline.
2. At most one short fenced DB operation is in flight for a given mutation identity.
3. The outcome of an issued mutation is either confirmed or treated as uncertain; uncertainty never triggers a compensating guess.

A parent-owned DB operation may run in a dedicated parent thread or other parent-controlled execution boundary so the supervisor can still terminate the adapter child. The DB execution boundary need not be forcibly killed at second 300. Database lock/statement/idle transaction limits remain 5/10/10 seconds under section 10.2, and connection invalidation plus fresh-primary recovery handles lost acknowledgement. If a network wait or driver thread survives the local deadline, the runner quarantines itself from new claims and mutations until the operation settles or authoritative recovery is possible.

After the productive deadline:

- stop child work and heartbeat renewal immediately;
- do not issue stage, finalize, retry-finalize, renew or a new claim;
- allow an already issued fenced transaction to settle, then classify it through its durable state;
- allow fresh-primary locked recovery reads needed to classify that prior transaction;
- never issue `fail(ENGINE_TIMEOUT)` while another mutation outcome is uncertain;
- if the child is confirmed stopped, no mutation is in flight or uncertain, and the same fence remains live, one short fenced `fail(ENGINE_TIMEOUT)` is allowed as attempt bookkeeping. It is not productive work. If that failure commit becomes uncertain, apply the same recovery rule and issue no second mutation;
- if the lease has expired, do not revive or fail it from the stale owner; leave it to locked reaper/takeover.

The preferred implementation reserves time before 300 seconds for child stop and the fenced failure mutation. A small containment/recovery tail may exceed the productive deadline as already described, but it cannot extend OCR/matching or authorize additional result publication. The fact that a parent DB thread cannot be guaranteed to terminate locally by second 300 is therefore not itself a contract violation; allowing that thread to keep issuing operations, allowing the adapter child to retain DB credentials, or starting a new mutation under uncertainty would be violations.

Minimum implementation boundary remains narrow but may extend beyond the runner file where needed:

- runner/supervision changes to keep adapters DB-free and stop them independently;
- verification-job service or DB execution wrapper changes only as needed to expose one-operation completion/uncertainty, enforce existing 5/10/10-second server timeouts, invalidate an uncertain connection and perform existing fresh-primary recovery;
- focused tests proving parent/child authority separation, no post-deadline useful work, valid already-issued commit recovery, no compensating fail under uncertainty, sequential timeout fail only after confirmed stop, and no new claim while quarantined.

No public API, schema or accepted contract change follows from these corrections. A strict no-late-server-COMMIT rule, child DB-write ownership, or a compensating mutation while outcome is uncertain would require a new exact contract revision and independent review.

## Scope and evidence

Read-only checks performed in `C:\Dev\qa-visual-automation`:

- Verified canonical contract SHA-256 `478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44`.
- Read the complete Backend03 runtime reproducibility addendum and verified SHA-256 `aef7bea1af2d8c57938736be4ad8b95e6a7c4dc23e30d210ec314ce8c2274d18`.
- Inspected contract sections 3 and 10.2 and focused source/tests for deadlines, process stopping, RSS monitoring, mutation ownership and ambiguous commit recovery.
- The initial source read saw accepted Backend evidence at `backend/app/workers/ocr.py` SHA-256 `f76b975aed52b07e34b554bf63f6059889f396ea6f0ece08db350bb9d7499839`. Backend03 then placed an untracked correction draft in the shared tree while this clarification was active. It was read only and preserved: runner `638f29322859a68add9530337f3135364938a34be2543161c67d1d5674cd70c4`, source loader `b685fc61cedbe4d10e81cc88e93341987c5af39f6f5bac6a3a97d5a59cc26a6f`, verification service `c11130c1580db0cd454d66bb3ac86cbeb4a734413d36f9ea7144202658f58fb5`, runner tests `72d42ff5704d31b1193a71bb5fb7ea1d24de32561a7c9c9d4b75ed5cf88feeda`.
- The previously inspected runtime integration test remains `fc7436eb3b23af8018c52465f727acecd13282fb9ebe971119683934501dbc58`.

No test was rerun. No runtime, Docker, DB, package, model, service, security or host-OS change was made. Existing Backend03 results remain owner evidence with the limits documented above. AC-P3-01 through AC-P3-04 were not re-evaluated. The broad report search encountered the known access-denied historical temporary directories; it was not repeated or bypassed, and the requested canonical addendum was readable directly.

## Handoff decision

Backend03 should implement the already activated P3-RUNTIME-001 correction using the minimum conditions above and submit focused Windows/Linux evidence. PM may keep revision 2 unchanged. A revision 3 and independent contract review are required only if the implementation proposes to relax the 300-second productive deadline, permit sampled-only memory compliance, exclude unproven descendants, increase the 2 GiB limit, move DB write authority into the adapter child, require strict cancellation of an already issued server COMMIT at second 300, or redefine the resource subject/metric in a way that is not demonstrably stricter.
