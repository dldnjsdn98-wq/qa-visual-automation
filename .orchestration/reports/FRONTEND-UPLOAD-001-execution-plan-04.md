# FRONTEND-UPLOAD-001 execution plan / owner 04

Date: 2026-09-20 KST  
Status: `BLOCKED` planning only. No product implementation or test execution is authorized until `REVIEW-ARCH-UPLOAD-001` returns `ACCEPTED` for the exact contract revision and PM explicitly promotes this task to `READY` with file ownership.

## Authority and current gate

- Current authority: `P2-UPLOAD-v1`, document revision 1, plus `.orchestration/handoffs/REVIEW-ARCH-UPLOAD-001-01.md` and the current `PROJECT_STATE.yaml`, `TASKS.yaml`, and `ACCEPTANCE.yaml`.
- Submitted contract hashes were re-read and re-measured for this plan:
  - `docs/architecture/phase-2-upload-contract.md` — `ab53b327517e6fd24bbff4b08c56a4d64f6dbda1a25f34a436e575858854ea4d`
  - `docs/architecture/api-contract.md` — `f494bfbfec6de2742312e1bc22e5aec7f93a714e37171965580e14ea81aa7443`
  - `docs/architecture/data-flow.md` — `d11a9ae800c9b8f5edd6ecb88c3e71638b918993abbd47798ac4fe7a6db02b18`
  - `docs/architecture/domain-model.md` — `6365a75c80b3ed8fc7b812d1b79100dca7239552dfeea6eaf563ffc23c7d1065`
- `ARCH-UPLOAD-001` is `READY_FOR_REVIEW`; `REVIEW-ARCH-UPLOAD-001` is `READY` with no result yet. `FRONTEND-UPLOAD-001` and `FRONTEND-UPLOAD-VERIFY-001` remain `BLOCKED`.
- Phase 1 remains `ACCEPTED/DONE`. AC-P2-01 through AC-P2-04 remain `NOT_RUN`; this plan is not implementation evidence or AC-P2-04 PASS.
- The earlier compatibility report remains the preparation evidence. It was not rerun or rewritten. This document converts its findings into an exact revision-1 execution plan.
- Historical `429` events are execution limits, not model-capability or product defects.

## Task, scope, difficulty, and model

- Task: `FRONTEND-UPLOAD-001` / owner `04`.
- Goal: separate the browser manual request type from the expanded Screenshot read model, then display the full bounded capture metadata contract safely while preserving the accepted manual flow.
- Difficulty: `중`. The change is bounded, but type separation, complete nested JSON rendering, Unicode preservation, and regression boundaries must agree with the independently accepted contract.
- Requested parent model: `gpt-5.6-sol / medium`; actual application: `실제 적용 미확인`.
- Planned product write set after activation:
  1. `frontend/lib/types.ts`
  2. `frontend/lib/api.ts`
  3. `frontend/components/screenshots.tsx`
  4. `frontend/app/globals.css`
  5. `frontend/tests/api.test.ts`
  6. `frontend/tests/components.test.tsx`
- Deferred actual-contract/Web verification file: `frontend/tests/integration/contract.test.ts`, exercised through `tests/frontend/run_integration.py` only when Backend/uploader submissions and PM's `FRONTEND-UPLOAD-VERIFY-001` entry gate are satisfied.
- Explicit exclusions: Backend, agent/uploader, shared configuration, source-filter UI, queue state, retry/replay controls, receipt/lease UI, browser agent-upload API, migration, YAML/DECISIONS, other owners' reports, Commit/Push.

The listed Frontend files already include user/other-work changes in the current dirty worktree (`api.ts` and `api.test.ts` modified; component and integration tests currently untracked). Before implementation, re-read and diff each target, confirm PM ownership, and patch only the allocated lines. Never replace whole files or normalize unrelated text.

## Subagent decomposition and integration ownership

Two read-only independent units were used as requested. Neither edited files nor ran tests. Parent owner 04 retains integration, validation, and evidence responsibility.

1. Manual request / expanded response types and API regression
   - Agent: `01a0bec9-642a-7982-b497-b37497e77815` (Plato).
   - Difficulty: `하`, because the contract and localized fix are explicit.
   - Requested model: `gpt-5.6-terra / high`; actual application: `실제 적용 미확인`.
   - Output incorporated: decouple the request/read types; keep manual FormData two-part and strict 201; widen only the read model; add targeted API/type assertions.
2. Safe nested Unicode metadata display and component regression
   - Agent: `01a0bec9-6513-7002-8ee9-9440c1dc5c89` (Sartre).
   - Difficulty: `중`, because complete nested JSON display must preserve values and prevent markup interpretation.
   - Requested model: `gpt-5.6-sol / medium`; actual application: `실제 적용 미확인`.
   - Output incorporated: conditional client ID, always-visible metadata version, complete deterministic JSON text, injection regression, and manual/automation display cases.

## Exact implementation plan

### 1. `frontend/lib/types.ts`

- Rename or replace the current request-facing `ScreenshotUpload` with an explicit `ManualScreenshotUpload`.
- Keep its allowed fields exactly: `build_id`, `locale_id`, `category_id`, `situation_id`, `source: "manual"`, optional `metadata_version: 1`, and optional `metadata`.
- Do not add `client_upload_id`, `upload_protocol_version`, `expected_file_hash`, or any idempotency-header representation to the browser request type.
- Add `ScreenshotSource = "manual" | "agent" | "automation"` for the response.
- Remove `Screenshot extends Required<ScreenshotUpload>`. Declare the read model independently with all existing fields plus:
  - `source: ScreenshotSource`
  - `metadata_version: 1`
  - `metadata: CaptureMetadata`
  - `client_upload_id: UUID | null`
- Preserve the JSON domain: unknown object keys, nested arrays/objects, empty strings, `null`, booleans, and numbers remain representable. Do not normalize Unicode. Optional reserved metadata keys may be absent; values actually returned over JSON cannot be `undefined`.
- Keep response handling tolerant of additive unknown response fields at runtime. Do not add a closed runtime decoder in this scoped task.

### 2. `frontend/lib/api.ts`

- Import and use `ManualScreenshotUpload` for `ApiClient.upload()` input; return the expanded `Screenshot`.
- Keep the method behavior unchanged:
  - `FormData` contains exactly `file` and `metadata`.
  - Browser supplies the multipart boundary; no manual `Content-Type` header.
  - Metadata remains a JSON string part.
  - Expected status remains exactly 201.
  - No `Idempotency-Key`, automatic retry, agent protocol field, or alternate 200 success path is added to the manual browser method.
- Keep list/detail clients as `Page<Screenshot>` and `Screenshot`; they need no new endpoint or producer behavior.

### 3. `frontend/components/screenshots.tsx`

- Keep list and detail Source rendering as direct safe React text. It already provides a readable fallback for every returned string and must not map an unknown future value to blank.
- Add `Metadata Version` to the detail facts for every Screenshot.
- Add `Client Upload ID` only when `client_upload_id !== null`. Manual records must not show a blank or literal-null identity row.
- Add a `Capture Metadata` detail section rendered through `<pre><code>` as a React text child. Never use `dangerouslySetInnerHTML`, an HTML parser, or Markdown rendering.
- Use a small pure recursive formatter local to this component or a narrowly named helper:
  - preserve array order;
  - sort object keys with a deterministic ordinal comparator (`a < b ? -1 : a > b ? 1 : 0`), avoiding locale-dependent ordering;
  - preserve scalar values exactly, including `""`, `null`, supplementary characters, and combining sequences;
  - serialize with `JSON.stringify(..., null, 2)`;
  - do not truncate, redact, normalize, or flatten the already server-bounded object.
- The contract bounds CaptureMetadata to 16 KiB, depth 5, and 100 keys, so a complete non-virtualized detail rendering is acceptable. The frontend does not claim to enforce those server bounds.

### 4. `frontend/app/globals.css`

- Add one narrowly scoped `.metadata-json` rule for complete readable text, limited to layout properties such as `max-width: 100%`, `overflow: auto`, and `white-space: pre`.
- Do not introduce line clamping, maximum-height clipping, hidden overflow, syntax-highlight HTML, or global `<pre>` changes.

## Exact regression specification

### `frontend/tests/api.test.ts`

Extend the existing multipart test rather than duplicating the preparation suite:

1. Assert manual upload FormData keys remain exactly `file`, `metadata` in that order.
2. Assert parsed metadata contains the relational IDs and `source: "manual"`; it contains none of `client_upload_id`, `upload_protocol_version`, or `expected_file_hash`.
3. Assert request headers remain `undefined`, proving no manual boundary or `Idempotency-Key` was introduced.
4. Add a manual-success-status regression: a 200 response to `ApiClient.upload()` rejects with `CONTRACT_ERROR`, while 201 remains accepted.
5. Add compile-time fixtures used by the repository typecheck:
   - an `agent` Screenshot with non-null UUID and nested metadata satisfies `Screenshot`;
   - an `automation` Screenshot satisfies `Screenshot`;
   - an agent source or client/protocol/hash field on `ManualScreenshotUpload` is rejected with focused `@ts-expect-error` assertions.

### `frontend/tests/components.test.tsx`

Retain the current manual fixture and existing error/expected-string behavior. Add focused detail cases:

1. Agent fixture: Source=`agent`, non-null Client Upload ID, Metadata Version=`1`, and complete Capture Metadata are visible.
2. Complete nested value fixture contains:
   - unknown nested object keys;
   - an ordered array;
   - empty string `""` and `null`;
   - supplementary scalar `😀`;
   - combining sequence `e\u0301` without normalization;
   - text resembling markup, e.g. `<img data-testid="metadata-injection" src=x>`.
3. Assert the `<pre>` text equals an independently written deterministic pretty-JSON string, including the empty string/null and nested ordering.
4. Assert the markup-looking value remains text and `querySelector('[data-testid="metadata-injection"]')` is null.
5. Manual fixture: Source=`manual`, Metadata Version=`1`, `{}` is visible, and no Client Upload ID row is present.
6. Automation fixture: Source=`automation` is visible through the same direct rendering path.
7. Preserve existing detail behavior: relationship labels, expected strings, and image-storage failure remain independently visible.

### Deferred `FRONTEND-UPLOAD-VERIFY-001` contract/Web checks

After Backend and uploader are READY_FOR_REVIEW and PM activates verification:

- Update/assert OpenAPI `Screenshot.source` enum is exactly manual/agent/automation and `client_upload_id` is UUID-or-null.
- Assert the upload request remains exactly the two multipart fields and the manual real flow returns source manual/client ID null under 201 semantics.
- Run an actual synthetic agent-to-Backend-to-Web flow and verify image bytes/hash, list/detail source, non-null client ID, metadata version, full nested Unicode metadata, relational context, and content route.
- Run a separate manual browser/API smoke to prove the original flow and originals remain preserved.
- Do not substitute component fixtures for this actual integration evidence.

## Planned validation after activation

Run from `C:\Dev\qa-visual-automation` and record environment, command, exit code, and output attribution:

1. Targeted unit/component regression:
   - `npm.cmd --prefix frontend run test -- tests/api.test.ts tests/components.test.tsx`
2. Type contract:
   - `npm.cmd --prefix frontend run typecheck`
3. Production build:
   - `npm.cmd --prefix frontend run build`
4. Review only the scoped diff and whitespace:
   - `git diff --check -- frontend/lib/types.ts frontend/lib/api.ts frontend/components/screenshots.tsx frontend/app/globals.css frontend/tests/api.test.ts frontend/tests/components.test.tsx`
5. Later, only under the actual verification gate and isolated Backend/PostgreSQL harness:
   - `.venv\Scripts\python.exe tests\frontend\run_integration.py`

Do not report a command as PASS unless it is actually run against the final scoped files. If a required command fails, distinguish code failure from environment/permission/execution-limit failure. The earlier 429 history is not evidence about this implementation.

## Current commands and results for this planning task

- `Get-Content -Encoding UTF8 -Raw` on current state/task/acceptance, role 04 prompt, review activation, revision-1 contract, owner report/handoff, and existing compatibility artifacts — completed as read-only inspection.
- `Get-FileHash -Algorithm SHA256` on the four submitted architecture files — completed; all hashes match the review activation handoff.
- `rg` and line-numbered reads of the current Frontend type, API, component, tests, and package scripts — completed as source inspection.
- Two read-only subagents — completed; outputs integrated above.
- Product edits, targeted tests, integration tests, typecheck, build, browser/API/DB/migration checks — `NOT_RUN` because implementation remains contract-review/PM gated.
- Commit/Push — `NOT_RUN` and unauthorized.

## Completion and handoff conditions

Implementation may start only when all are true:

1. Reviewer 08 accepts these exact revision-1 hashes, or a later exact revision explicitly supersedes them.
2. PM records `ARCH-UPLOAD-001` and `REVIEW-ARCH-UPLOAD-001` accepted/done and explicitly promotes `FRONTEND-UPLOAD-001` to READY.
3. PM confirms the listed Frontend file ownership against the then-current dirty worktree.

Implementation submission is `READY_FOR_REVIEW` only after the scoped changes and required targeted/typecheck/build evidence are complete with no mandatory failure. It is distinct from Reviewer acceptance, `FRONTEND-UPLOAD-VERIFY-001`, AC-P2-04 PASS, and Phase 2 acceptance. Any contract revision, unexpected cross-module dependency, or two evidence-based failures for the same cause triggers difficulty/model reassessment before further attempts.
