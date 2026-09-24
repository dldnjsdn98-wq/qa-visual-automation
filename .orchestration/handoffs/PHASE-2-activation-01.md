# PHASE 2 activation / PM 01 / 2026-09-13

Repository: C:\Dev\qa-visual-automation. Phase 1 ACCEPTED was rechecked from current PROJECT_STATE/TASKS/ACCEPTANCE/DECISIONS, PHASE-1-acceptance-01.md and designated R08-WEB-002-closure-08.md. All thirteen Web AC PASS; Backend/Frontend/Web Review/ENV DONE and ACCEPTED; R08-WEB-002 and ENV RESOLVED. Current runtime JSON is retained dated Reviewer evidence, not a PM rerun. Phase 1 tasks and acceptance remain unchanged.

Phase 2 is now IN_PROGRESS for contract and preparation. AC-P2-01..04 remain NOT_RUN. Current API source rejects Idempotency-Key and declares source manual/client_upload_id null; uploader-only work cannot meet server deduplication. agent/screenshot_upload and tests/upload contain only .gitkeep at inspection. Existing uncommitted/untracked changes are preserved.

## Sequence and activation gates

1. READY now: Architect contract, Backend preparation, Screenshot preparation, Frontend compatibility assessment, Reviewer root/preparation. Preparation writes only each role's own new Phase 2 evidence, not product/shared files.
2. Architect collects 03/06/04 findings, specifies executable examples/state transitions/failure boundaries and submits an exact revision READY_FOR_REVIEW. PM accepts sufficient preparation evidence and activates REVIEW-ARCH-UPLOAD-001; independent acceptance, not Author self-check, opens implementation.
3. On contract acceptance and confirmed ownership, PM promotes BACKEND-UPLOAD-001 and existing UPLOAD-001 together to READY and sends implementation instructions with Sol/high. Their implementations have no dependency on each other's completion; mocks/approved fixtures enable parallel work. Live integration requires both endpoints available. No speculative protocol implementation before that gate.
4. Frontend assessment may identify needed type/display changes (current types are manual/null while list/detail render source directly). PM adds FRONTEND-UPLOAD-001 only with concrete findings, approved contract, scope and model assessment. Do not reopen FRONTEND-WEB-001. Without necessary changes, retain verification-only work.
5. Once Backend/uploader submissions and any required Frontend changes are available, PM activates FRONTEND-UPLOAD-VERIFY-001 for actual Web evidence, then REVIEW-UPLOAD-001 from matching READY_FOR_REVIEW evidence. Add a required Frontend implementation dependency if one is allocated. Reviews/verification use submission-entry gates rather than creating a dependency cycle requiring prior implementation acceptance.
6. PM accepts Phase 2 only after all four required AC PASS, independent review ACCEPTED, all required tasks complete/accepted and no required issue. Phases 3+ remain untouched.

## File ownership and safe work

- PM 01 alone writes PROJECT_STATE.yaml, TASKS.yaml, ACCEPTANCE.yaml, DECISIONS.md, docs/phases/phase-2-upload.md and this PM handoff. Owners submit status proposals via own handoffs; no parallel YAML edits.
- Architect 02 owns new docs/architecture/phase-2-upload-contract.md and scoped existing architecture Phase 2 cross-references/model sections; preserve accepted Phase 1 behavior/history. Concrete shared schema files, if needed, are named and exclusively assigned before implementation. No product edits by Architect.
- Backend 03 owns backend/, tests/backend/ and new additive migration; do not rewrite deployed Phase 1 migration. pyproject.toml, lock files, alembic.ini, Compose/env examples and root README are shared: request exact file/rationale from PM before editing. No user DB reset/reseed, blind storage move or deletion.
- Screenshot 06 owns agent/screenshot_upload/ and tests/upload/, including the actual agent-to-Backend integration harness. Common agent CLI/entrypoints and dependencies require PM claim first; avoid unrelated agent restructuring.
- Frontend 04 owns frontend/, tests/frontend/ only when scoped implementation/verification is activated. It owns its Web evidence; coordinate service ports/test fixtures with 03/06. Other roles do not edit frontend files.
- Reviewer 08 owns separate named Phase 2 review evidence/handoffs and isolated validation artifacts. Do not overwrite Author evidence, prior Phase 1 reports, or fix product code.
- Before each write, inspect existing user changes and latest contents. Use exact current root/workdir; never operate on the old checkout. Preserve original QA data; synthetic fixtures and disposable DB/storage for failure tests. No Commit/Push.

## Contract decisions required from Architect

Specify wire schema/version and source values; ID scope and generation/persistence; client_upload_id versus Idempotency-Key handling (supported/rejected/mismatch/validation explicitly, no silently ignored header); server-derived and optional validated client hash; request limits/Unicode; response identity/hash/context fields sufficient for acknowledgment; status/header/error matrix including first create, completed replay, payload conflict, active processing and transient failures.

Define fingerprint over exact intended payload semantics, not file hash alone: Project and all scoped IDs/source/metadata version/content/filename policy plus server-computed byte hash; canonical JSON ordering/numbers/null/defaults/Unicode normalization policy and fingerprint version. Include examples for equal semantic replay, same ID/different bytes, same bytes/different context, and unrelated IDs with identical hash.

Specify persistent receipt uniqueness, lifetime (initial design no automatic expiry), screenshot/reference retention/deletion interactions; reservation validation order; authoritative lease clock/expiry/renewal/takeover; monotonic attempt fencing and per-attempt object ownership. Atomic Screenshot+completed receipt commit, ambiguous commit recovery, stale writer finalize/cleanup denial and reconciliation rules must hold at every reserve/stage/publish/insert/commit/response boundary.

Specify producer image+versioned manifest readiness publication only when both durable; partial writes, manifest validation/corruption, process restart, worker exclusivity/claim recovery, persisted attempt/backoff/jitter/Retry-After and terminal failure retention. Define matching server acknowledgment and crash-safe pending->uploaded/failed transitions. Filename/hash/metadata changes must not silently reuse one immutable upload identity.

## Required verification matrix (planned, NOT_RUN)

| AC | Required reproducible scenarios | Main evidence owners |
| --- | --- | --- |
| AC-P2-01 | Offline and process restart retain queue and original bytes; image-only/manifest-only/truncated/temp/unready items never submitted; crash during readiness/state transition and restart recover safely | 06; independent 08 |
| AC-P2-02 | Persist attempt/backoff across restart; deterministic clock/jitter tests, retryable vs terminal errors, Retry-After, exhausted retries logged with original preserved; mismatched/malformed acknowledgment never marks uploaded | 06 with 03 API errors; 08 |
| AC-P2-03 | Server commit then response loss and same-request resend; same ID/same payload returns same resource; same ID/different bytes or metadata conflicts; same bytes/different IDs not collapsed; concurrent connections, lease takeover/fencing, interrupted publication/commit and both process restarts; receipt migration/retention and exact object ownership | 03 + 06 integration; 08 |
| AC-P2-04 | Actual agent->Backend/PostgreSQL/storage->Web list/detail/image/source/metadata; server receipt must match before local completion; original bytes/hash and multilingual metadata preserved; existing manual upload and prior originals remain readable | 06 + 03; 04 Web; 08 |

Risk-based commands must be selected after source changes, using project .venv and current test harnesses. Backend baseline runner is backend/tools/run_postgres_tests.py; upload tests will live under tests/upload; Frontend existing actual client runner is tests/frontend/run_integration.py --isolated-postgres. These are planned starting points, not executed Phase 2 results. Check current command options before execution. Record exact command/cwd/runtime/DB isolation, timestamps, result artifacts and NOT_RUN reasons. A mocked client cannot prove durable server uniqueness or actual Web display. Fresh/additive migration tests preserve old fixture IDs/hash/Unicode. Never run destructive downgrade/reset against user data. Coordinate service lifecycles and stop only owned processes.

## Models, reassessment and routing

Assignments below are per work unit. Requested model/effort is supplied through supported task settings during dispatch; successful message delivery alone does not prove actual execution model. Until confirmed by execution metadata/owner, record actual model unverified. Later implementation/review requests must use their listed effort rather than inheriting a preparation setting.
Reassess unexpected dependencies/contracts, unreproduced bugs, new persistent-data risk or two evidenced failed corrections for the same cause. Distinguish environment/permission/auth errors from model capability. Request upward reassignment with evidence at a safe boundary; no forced interruption solely for policy.

Existing app tasks verified: 02=2.Software; 03=3 BACKEND ENGINEER; 06=6 Screenshot; 04=4 fronte. Reviewer is existing task 리뷰 (01a06d9e-1f60-74e0-b8f2-c5af626c0f32), whose latest content confirms role08 but cwd is the old New project 2 directory. First dispatch is root/role/preparation only: explicitly read current root, confirm safe current-root work/access and report restrictions before any artifact writes. Do not treat its old Prototype findings as this repository's current blockers. Do not create or hand off tasks automatically.

## ARCH-UPLOAD-001 / 02

- Status: READY; dependencies: PHASE 1 ACCEPTED.
- Goal: Specify versioned request/response and producer/queue protocol, server receipt schema/state machine and recovery boundaries; preserve manual upload semantics.
- Scope: docs/architecture/phase-2-upload-contract.md; scoped Phase 2 cross-references in api-contract.md/data-flow.md/domain-model.md; own report/handoff.
- Entry: Phase 1 acceptance verified; execute only assigned contract/preparation scope.
- Completion: Explicit ID scope, fingerprint fields/canonicalization/version, validation ordering, 201/200/replay/409/Retry-After and header policy; receipt retention, transaction/lease clock/renewal/fencing, object ownership and crash matrix; consult 03/06/04 preparation and resolve open decisions before submission.
- Verification: Static cross-document/examples consistency and trace every required failure scenario; record contract revision and hashes; READY_FOR_REVIEW requires concrete reviewable contract, not architecture-only product PASS.
- Difficulty: 최상; Cross-process receipt, fingerprint, lease/fencing and crash boundaries affect core persistent identity contracts.
- Requested model: gpt-6-astra / medium. Actual: unverified.
- Deliverables: .orchestration/reports/ARCH-UPLOAD-001-02.md and .orchestration/handoffs/ARCH-UPLOAD-001-02.md. Include Task ID, scope/changed files, contract revision, commands/environment/results/limits, requested vs actual model, blockers and next owner/entry condition.

## PREP-BACKEND-UPLOAD-001 / 03

- Status: READY; dependencies: PHASE 1 ACCEPTED.
- Goal: Map current router/schema/storage/transaction/reconciliation and propose safe receipt migration and fault-test seams for Architect.
- Scope: Read-only backend/, tests/backend/, migration/config inspection; write only own Phase 2 report/handoff.
- Entry: Phase 1 acceptance verified; execute only assigned contract/preparation scope.
- Completion: Current versus proposed behavior, exact file ownership, preservation/migration risks and contract questions supplied to PM/02.
- Verification: Source references and safe runtime availability/version checks only as needed; no migrations, product edits, storage mutation or suite reruns.
- Difficulty: 중; Read-only mapping of existing implementation and additive migration/test seams; no data changes.
- Requested model: gpt-5.6-sol / medium. Actual: unverified.
- Deliverables: .orchestration/reports/PREP-BACKEND-UPLOAD-001-03.md and .orchestration/handoffs/PREP-BACKEND-UPLOAD-001-03.md. Include Task ID, scope/changed files, contract revision, commands/environment/results/limits, requested vs actual model, blockers and next owner/entry condition.

## PREP-UPLOAD-001 / 06

- Status: READY; dependencies: PHASE 1 ACCEPTED.
- Goal: Inventory agent/CLI/dependencies and design reproducible queue crash/failure cases and module boundaries for contract consultation.
- Scope: Read-only agent/, tests/upload/, capture conventions; own report/handoff only.
- Entry: Phase 1 acceptance verified; execute only assigned contract/preparation scope.
- Completion: Producer readiness marker/partial file/restart/retry/ack questions, dependency request and owned modules supplied to PM/02.
- Verification: Source inventory and proposed deterministic failure matrix; no contract-dependent queue/network implementation or real captures modifications.
- Difficulty: 중; Bounded inventory and test design before protocol decisions; no persistence implementation yet.
- Requested model: gpt-5.6-sol / medium. Actual: unverified.
- Deliverables: .orchestration/reports/PREP-UPLOAD-001-06.md and .orchestration/handoffs/PREP-UPLOAD-001-06.md. Include Task ID, scope/changed files, contract revision, commands/environment/results/limits, requested vs actual model, blockers and next owner/entry condition.

## FRONTEND-UPLOAD-CHECK-001 / 04

- Status: READY; dependencies: PHASE 1 ACCEPTED.
- Goal: Assess agent source, non-null client_upload_id, metadata and manual upload compatibility; recommend exact necessary changes or no-change conclusion.
- Scope: Read-only frontend/ and tests/frontend/; own report/handoff only.
- Entry: Phase 1 acceptance verified; execute only assigned contract/preparation scope.
- Completion: Identify current types restricted to manual/null and source rendering; give minimal change list, regression plan and contract questions to PM/02.
- Verification: Inspect response consumption and display paths; no speculative UI work, product writes or old test results relabeled as current.
- Difficulty: 중; Typed client/UI compatibility requires source tracing; implementation need is evidence-gated.
- Requested model: gpt-5.6-sol / medium. Actual: unverified.
- Deliverables: .orchestration/reports/FRONTEND-UPLOAD-CHECK-001-04.md and .orchestration/handoffs/FRONTEND-UPLOAD-CHECK-001-04.md. Include Task ID, scope/changed files, contract revision, commands/environment/results/limits, requested vs actual model, blockers and next owner/entry condition.

## REVIEW-UPLOAD-PREP-001 / 08

- Status: READY; dependencies: PHASE 1 ACCEPTED.
- Goal: Verify safe read/write workflow for current root and role, read current gates, prepare independent contract/implementation acceptance matrix.
- Scope: Read-only current repository; own new Phase 2 report/handoff only after safe-root confirmation. Never edit old repository.
- Entry: Phase 1 acceptance verified; execute only assigned contract/preparation scope.
- Completion: Report actual cwd/current root access, current role, requested versus actual model and review readiness; verify current Phase 1 records supersede old prototype history.
- Verification: Read current files through absolute root or explicit workdir; report permission/tool blockers without bypass. No product tests or acceptance before submission.
- Difficulty: 중; Existing reviewer task has old cwd; bounded root verification and evidence-map preparation, not final review.
- Requested model: gpt-5.6-sol / medium. Actual: unverified.
- Deliverables: .orchestration/reports/REVIEW-UPLOAD-PREP-001-08.md and .orchestration/handoffs/REVIEW-UPLOAD-PREP-001-08.md. Include Task ID, scope/changed files, contract revision, commands/environment/results/limits, requested vs actual model, blockers and next owner/entry condition.

## REVIEW-ARCH-UPLOAD-001 / 08

- Status: BLOCKED; dependencies: ARCH-UPLOAD-001.
- Goal: Review submitted contract independently; require actionable resolution of ambiguity before implementation activation.
- Scope: Own Phase 2 contract-review report/handoff only; no owner contract or product fixes.
- Entry: ARCH-UPLOAD-001 READY_FOR_REVIEW with exact revised contract/handoff; REVIEW-UPLOAD-PREP-001 root confirmed; PM activates independent review.
- Completion: Return ACCEPTED or CHANGES_REQUESTED with exact revision/hash, issues and scenario matrix; no required unresolved issue.
- Verification: Reproduce/static-check request examples, fingerprint distinctions including same hash/different metadata, lease takeover/stale fencing, ambiguous commit, receipt retention and partial queue/ack crash cases.
- Difficulty: 상; Independent analysis of persistent concurrency, crash recovery and protocol compatibility.
- Requested model: gpt-5.6-sol / high. Actual: unverified.
- Deliverables: .orchestration/reports/REVIEW-ARCH-UPLOAD-001-08.md and .orchestration/handoffs/REVIEW-ARCH-UPLOAD-001-08.md. Include Task ID, scope/changed files, contract revision, commands/environment/results/limits, requested vs actual model, blockers and next owner/entry condition.

## BACKEND-UPLOAD-001 / 03

- Status: BLOCKED; dependencies: PHASE 1 ACCEPTED, ARCH-UPLOAD-001, REVIEW-ARCH-UPLOAD-001, PREP-BACKEND-UPLOAD-001.
- Goal: Implement approved agent API, durable receipt/fingerprint/lease fencing and transaction-safe Screenshot completion while preserving manual uploads.
- Scope: backend/, tests/backend/; backend migrations sole owner 03; dependencies/shared config require PM file claim first.
- Entry: Contract task and independent contract review ACCEPTED/DONE with evidence, own preparation accepted, file ownership confirmed; PM promotes Backend and uploader together without making either wait for the other implementation.
- Completion: Real PostgreSQL first/replay/conflict/concurrent/restart/response-loss cases pass; additive migration preserves existing IDs/originals/Unicode; receipt lifetime and reconciliation cannot delete a winner object.
- Verification: Fresh plus additive migration in disposable/backup-safe environments; fault injection at reserve/publish/commit/response/takeover, multi-connection concurrency, affected manual/storage/Unicode regressions and actual agent integration.
- Difficulty: 상; Persistent data, additive migration, concurrent reservations and fenced recovery require high-risk implementation checks.
- Requested model: gpt-5.6-sol / high. Actual: unverified.
- Deliverables: .orchestration/reports/BACKEND-UPLOAD-001-03.md and .orchestration/handoffs/BACKEND-UPLOAD-001-03.md. Include Task ID, scope/changed files, contract revision, commands/environment/results/limits, requested vs actual model, blockers and next owner/entry condition.

## UPLOAD-001 / 06

- Status: BLOCKED; dependencies: PHASE 1 ACCEPTED, ARCH-UPLOAD-001, REVIEW-ARCH-UPLOAD-001, PREP-UPLOAD-001.
- Goal: Implement approved versioned durable producer queue, persisted retry/backoff/failure states and matching-receipt acknowledgment.
- Scope: agent/screenshot_upload/, tests/upload/ (including actual Backend-agent integration harness owned by 06); common CLI/dependency edits only after PM file claim.
- Entry: Contract task and independent contract review ACCEPTED/DONE with evidence, own preparation accepted, file ownership confirmed; PM promotes Backend and uploader together without making either wait for the other implementation.
- Completion: Originals survive offline/crash/terminal failure; incomplete image/manifest never ready; stable request identity/payload across retries; uploaded transition only after matching server response; restart-safe local transitions and real API/Web flow evidence.
- Verification: Deterministic clock/network/crash injection, separate-process restart, partial writes, retry exhaustion, mismatched/malformed success rejection, lost success/replay against actual PostgreSQL Backend and original hash/Unicode readback.
- Difficulty: 상; Durable queue, crash recovery, ambiguous server responses and acknowledgment transitions risk original loss.
- Requested model: gpt-5.6-sol / high. Actual: unverified.
- Deliverables: .orchestration/reports/UPLOAD-001-06.md and .orchestration/handoffs/UPLOAD-001-06.md. Include Task ID, scope/changed files, contract revision, commands/environment/results/limits, requested vs actual model, blockers and next owner/entry condition.

## FRONTEND-UPLOAD-VERIFY-001 / 04

- Status: BLOCKED; dependencies: BACKEND-UPLOAD-001, UPLOAD-001, FRONTEND-UPLOAD-CHECK-001.
- Goal: Verify actual agent upload list/detail/image/source/metadata and existing manual flow after submissions.
- Scope: frontend/tests/, tests/frontend/ verification only after file coordination; own evidence; product edits require separate PM allocation.
- Entry: Backend and uploader READY_FOR_REVIEW with actual integration evidence and compatibility assessment accepted; PM activates verification.
- Completion: Actual agent upload and multilingual metadata visible in Web; manual upload and originals preserved; any required UI/types fix separately submitted and independently reviewed.
- Verification: Actual Backend-agent-Web synthetic flow, detail/image hash/source/metadata and manual smoke; targeted behavior/typecheck/build only when changes justify; do not substitute fixtures for real integration.
- Difficulty: 중; Focused actual Web/API compatibility checks within existing UI; implementation allocated only for an evidenced gap.
- Requested model: gpt-5.6-sol / medium. Actual: unverified.
- Deliverables: .orchestration/reports/FRONTEND-UPLOAD-VERIFY-001-04.md and .orchestration/handoffs/FRONTEND-UPLOAD-VERIFY-001-04.md. Include Task ID, scope/changed files, contract revision, commands/environment/results/limits, requested vs actual model, blockers and next owner/entry condition.

## REVIEW-UPLOAD-001 / 08

- Status: BLOCKED; dependencies: BACKEND-UPLOAD-001, UPLOAD-001, FRONTEND-UPLOAD-VERIFY-001.
- Goal: Independently judge AC-P2-01 through 04 and manual/storage/Unicode regression from final matching submissions.
- Scope: Own reports/handoffs and isolated validation artifacts; no owner code changes; PM owns state/acceptance.
- Entry: All referenced implementations/verification and any added required Frontend fix READY_FOR_REVIEW with final evidence (or already accepted); Reviewer root confirmed; PM activates.
- Completion: AC matrix with executions versus Owner evidence, required issues resolved and ACCEPTED or CHANGES_REQUESTED; Phase acceptance remains PM-only.
- Verification: Risk-selected independent replay/conflict/concurrency/recovery/queue restart and actual Web evidence; inspect migration/data preservation and source fingerprints; no mandatory failure or unknown blocker marked complete.
- Difficulty: 상; Cross-service persistence and recovery assertions need independent fault/concurrency and end-to-end evidence.
- Requested model: gpt-5.6-sol / high. Actual: unverified.
- Deliverables: .orchestration/reports/REVIEW-UPLOAD-001-08.md and .orchestration/handoffs/REVIEW-UPLOAD-001-08.md. Include Task ID, scope/changed files, contract revision, commands/environment/results/limits, requested vs actual model, blockers and next owner/entry condition.

## Actual dispatch / 2026-09-13

All five READY assignments were successfully delivered to their existing tasks with explicit requested model/effort. No new task was created. A bounded wait snapshot showed all app tasks active; only Backend preparation had a fresh inProgress turn in that snapshot. Other latest-turn fields still contained historical results and are not used as new completion evidence. Actual runtime model remains unverified.

- ARCH-UPLOAD-001 -> 2.Software (01a06f38-6916-7d00-998d-649ed5482d43): DELIVERED; APP_ACTIVE; new task execution not yet confirmed.
- PREP-BACKEND-UPLOAD-001 -> 3 BACKEND ENGINEER (01a06f50-21ad-7d41-9c55-676bf7d3d4fd): DELIVERED; IN_PROGRESS_CONFIRMED.
- PREP-UPLOAD-001 -> 6 Screenshot (01a07128-2c2d-71a1-a66e-ab654305170b): DELIVERED; APP_ACTIVE; new task execution not yet confirmed.
- FRONTEND-UPLOAD-CHECK-001 -> 4 fronte (01a070d8-d6fd-7773-bb3b-64813e89e1d8): DELIVERED; APP_ACTIVE; new task execution not yet confirmed.
- REVIEW-UPLOAD-PREP-001 -> 리뷰 (01a06d9e-1f60-74e0-b8f2-c5af626c0f32): DELIVERED; APP_ACTIVE; new task execution not yet confirmed.

Delivery is not completion or independent acceptance. Reviewer current-root access confirmation is still awaited; contract-dependent implementation remains BLOCKED.


## Preparation follow-up / 2026-09-13

FRONTEND-UPLOAD-CHECK-001 and PREP-BACKEND-UPLOAD-001 completed and accepted by PM as consultation only. FRONTEND-UPLOAD-001 is now required/BLOCKED, Sol/medium requested for later activation, from the concrete type compatibility finding. Implementation and Web metadata decisions await contract approval. See PHASE-2-frontend-backend-prep-01.md; later verification/review dependencies updated.


PREP-UPLOAD-001 now complete as well; all three producer/consumer preparation reports delivered to Architect. Consult PHASE-2-frontend-backend-prep-01.md addendum and PROJECT_STATE pending shared file requests. No implementation activation.
