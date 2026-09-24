# FRONTEND-UPLOAD-CHECK-001 / owner 04

## Result

Current Frontend source is runtime-compatible with displaying an unknown `source` string in Screenshot list/detail, but its TypeScript response contract is not compatible with Phase 2 agent records: `Screenshot` inherits the manual request type, so `source` is restricted to `"manual"` and `client_upload_id` is restricted to `null`. The detail screen also does not render `metadata_version`, `metadata`, or `client_upload_id`. A small, contract-dependent Frontend change is therefore required after ARCH-UPLOAD-001 and its independent review are accepted. No product change is justified before that gate.

## Task, gate, scope, and model

- Task: `FRONTEND-UPLOAD-CHECK-001`; owner `04`; status at inspection: `READY`.
- Goal: assess agent source, non-null client upload identity, metadata, and manual upload compatibility; provide the smallest change and regression plan.
- Dependency: Phase 1 is `ACCEPTED`; `FRONTEND-WEB-001` is `DONE`. Phase 2 AC-P2-01 through AC-P2-04 are currently `NOT_RUN`.
- Read scope: `.orchestration/PROJECT_STATE.yaml`, `TASKS.yaml`, `ACCEPTANCE.yaml`, `DECISIONS.md`, the Phase 2 activation handoff/plan, role 04 instructions, `frontend/`, `tests/frontend/`, and the existing Phase 1 architecture contract references.
- Write scope: this report and `.orchestration/handoffs/FRONTEND-UPLOAD-CHECK-001-04.md` only.
- Difficulty: 중. Reason: typed request/response compatibility and Web evidence require tracing contract consumption, while implementation remains bounded and evidence-gated.
- Requested model: `gpt-5.6-sol` / `medium`.
- Actual model: 실제 적용 미확인. The execution environment did not expose a verifiable model identifier.
- Contract revision: ARCH-UPLOAD-001 is being drafted; no accepted Phase 2 contract revision/hash was available during this assessment.

## Current evidence

### Type and client constraints

- `frontend/lib/types.ts:16` defines `ScreenshotUpload.source` as exactly `"manual"` and does not include `client_upload_id`.
- `frontend/lib/types.ts:17` defines `Screenshot extends Required<ScreenshotUpload>` and `client_upload_id: null`. Consequently, a correctly typed Phase 2 agent response cannot represent `source: "agent" | "automation"` or a non-null upload ID.
- The inheritance also couples the browser's manual write payload to the server's read model. Widening `ScreenshotUpload` directly would allow the manual browser code to send agent-only identity/source combinations, so request and response types should be separated.
- `frontend/lib/api.ts:83-88` is a manual browser multipart client. It sends exactly `file` plus JSON-string `metadata` and requires HTTP 201. This matches the accepted Phase 1 manual contract and should remain unchanged in behavior. The Frontend has no producer retry/replay client and does not need one for Phase 2 agent ingestion.
- `frontend/lib/api.ts:80-82` consumes list/detail as `Screenshot`; once the response type is corrected, no endpoint or request-flow change is needed for reading agent-created records.

### Display paths

- `frontend/components/screenshots.tsx:38` renders `item.source` as text in the list. It has no manual-only branch, so an agent/automation value received at runtime already appears without a component change.
- `frontend/components/screenshots.tsx:58-60` renders Source in detail, also without a manual-only branch.
- The same detail field list omits `metadata_version`, `metadata`, and `client_upload_id`. Therefore arbitrary capture metadata cannot currently satisfy a literal AC-P2-04 requirement that uploaded metadata appear in Web. Relational context, dimensions, timestamp, filename, and source do appear.
- There is no source filter in the UI. AC-P2-04 does not require one, and adding one during this compatibility change would be speculative.
- Empty/error behavior is already independent of source: list empty state, detail API error, image storage error, and expected-strings error use the existing generic paths.

### Existing regression coverage

- `frontend/tests/api.test.ts:28-35` protects the manual request's exact two multipart parts and browser-generated boundary behavior.
- `frontend/tests/components.test.tsx:18` has only a manual/null Screenshot fixture. Existing list/detail tests therefore do not exercise agent source, non-null ID, or capture metadata rendering.
- `frontend/tests/integration/contract.test.ts:22` requires the existing Screenshot field set, while `:50` explicitly verifies manual upload returns `client_upload_id === null`.
- These are current source observations. Historical Phase 1 PASS results were read only as gate/history and were not rerun or relabeled as current Phase 2 evidence.

## Minimal contract-dependent change list

Apply only after the Phase 2 contract revision is independently accepted and PM makes the implementation/verification work READY.

1. In `frontend/lib/types.ts`, introduce the exact accepted response enum, expected to be `ScreenshotSource = "manual" | "agent" | "automation"`. Replace the coupled inheritance with separate types:
   - `ManualScreenshotUpload`: current relational IDs, `source: "manual"`, optional version/metadata, and no client upload ID.
   - `Screenshot`: explicit response fields, `source: ScreenshotSource`, `client_upload_id: UUID | null`, required `metadata_version` and `metadata`.
2. In `frontend/lib/api.ts`, keep `upload()` typed to `ManualScreenshotUpload`, preserve the exact two-part multipart body, and continue requiring 201 for browser manual upload. Do not add agent retry/idempotency methods unless the accepted contract assigns browser producer behavior.
3. In `frontend/components/screenshots.tsx`, retain fallback text rendering for every source enum member. On detail, expose the accepted capture metadata and metadata version; render `client_upload_id` when non-null for traceability. Use a bounded structured display that preserves Unicode and nested JSON values. Do not interpret unknown metadata keys as trusted markup.
4. Do not add source filtering, replay controls, queue status, or browser retry UI for this task. Those behaviors are not required by the current Web acceptance criterion.

If the accepted contract narrows “metadata appear in Web” to only the already-rendered relational/core fields plus Source, item 3 may be reduced to no component change. That interpretation must be explicit because the response's `metadata` object is currently invisible.

## Regression and later verification plan

- Typecheck/build after implementation to prove agent response fixtures and the unchanged manual call both compile.
- Targeted API unit test: manual `upload()` still sends exactly `file` and `metadata`, sends `source: "manual"`, omits `client_upload_id`/idempotency headers, and accepts only the contract's manual success status.
- Targeted component tests:
  - list and detail display `agent` and `automation` through fallback-safe text;
  - detail displays non-null client upload ID and multilingual/nested metadata without dropping empty strings, combining sequences, or supplementary characters;
  - null client upload ID remains unobtrusive for manual records;
  - unknown future source received at runtime remains readable rather than blank or crashing, consistent with the existing future-enum fallback requirement.
- Contract/OpenAPI test after Backend implementation: Screenshot response source enum and nullable/non-null UUID shape match the accepted contract; manual upload remains 201 with null ID.
- `FRONTEND-UPLOAD-VERIFY-001`, only after Backend and uploader submissions plus PM activation: use an actual agent-to-Backend-to-Web synthetic flow to verify image bytes/hash, source, client upload ID, metadata, relational context, list/detail/content paths, and a separate manual upload regression. Fixtures cannot replace that evidence.

## Contract questions for PM / owner 02

1. Confirm the response enum spelling and meaning: `manual | agent | automation`, including whether an automation capture forwarded by the uploader remains `automation` rather than being rewritten to `agent`.
2. Confirm the invariant matrix: manual requests must omit `client_upload_id` and idempotency headers, while agent/automation requests require a non-null UUID; invalid pairings receive 422 rather than normalization or silent ignore.
3. Confirm where the agent ID lives on the wire. The existing endpoint has exactly two multipart parts, with ScreenshotUpload encoded in the `metadata` JSON part. State explicitly whether `client_upload_id` is a field in that JSON object and whether an idempotency header is required, optional, or forbidden.
4. Confirm manual response semantics remain 201 only, and 200 plus `Idempotency-Replayed: true` is possible only for ID-bearing agent/automation replays. This lets the existing browser `upload()` keep its strict 201 check.
5. Define the Web-visible metadata minimum for AC-P2-04: all `CaptureMetadata`, only reserved keys, or only core relational metadata. If arbitrary keys are required, confirm a bounded JSON representation is acceptable and whether `client_upload_id` must also be visible.
6. Confirm list/detail return one stable Screenshot schema for all sources, with `client_upload_id: UUID | null`, required `metadata_version`, required `metadata`, and no receipt/lease fields. Frontend should ignore additive response fields.
7. Confirm whether GET `source` filtering expands to all enum values. No UI filter is proposed, but the typed query/OpenAPI contract should be unambiguous.

## Commands, environment, results, and limits

- Environment: Windows PowerShell; working directory `C:\Dev\qa-visual-automation`; read-only product assessment.
- `rg --files .orchestration docs frontend tests/frontend | Sort-Object` — completed with the expected inventory; one existing reviewer temporary directory reported access denied and was irrelevant to this task.
- `Get-Content -Raw` on the assigned state, acceptance, decisions, activation, Phase 2 plan, role 04 prompt, and relevant Frontend files — completed.
- `rg -n` searches for `client_upload_id`, `source`, `metadata`, upload, Screenshot types, response consumption, display paths, and contract references — completed; findings are cited above.
- `git status --short` — completed. The worktree already contained extensive user/other-owner changes and untracked evidence. They were preserved and not modified by this assessment.
- Product tests, typecheck, build, API calls, database operations, migrations, and browser checks — `NOT_RUN`, because the assignment explicitly limits this task to source inspection and forbids suite reruns/speculative UI work. No unexecuted check is reported as PASS.

## Remaining risk and next condition

- The exact Phase 2 wire contract and Web-visible metadata definition are unresolved. Implementing before those answers risks widening the manual request improperly or testing the wrong replay status/header behavior.
- Next owners: PM `01` and Architect `02` resolve the questions in ARCH-UPLOAD-001; Reviewer `08` independently accepts the exact contract revision. PM may then allocate the evidenced minimal Frontend change, if required, and later activate `FRONTEND-UPLOAD-VERIFY-001` after Backend/uploader submissions.
- Status of this preparation artifact: complete assessment, ready for PM/Architect consultation. It is not implementation, AC-P2-04 PASS, independent review, or Phase 2 acceptance.
