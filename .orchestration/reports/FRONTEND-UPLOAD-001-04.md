# FRONTEND-UPLOAD-001 / owner 04

Date: 2026-09-25 KST.  
Submission status: `READY_FOR_REVIEW` requested. This is owner implementation evidence, not independent acceptance, AC-P2-04 PASS, or Phase 2 acceptance.

## Result

Implemented the accepted P2-UPLOAD-v1 revision 2 Frontend slice. Browser manual upload input is now separated from the expanded Screenshot response model. Manual FormData remains exactly `file` plus `metadata`, browser-owned multipart boundary, and HTTP 201 only. Screenshot list/detail reads now represent `manual | agent | automation` and `client_upload_id: UUID | null`.

Screenshot detail displays `metadata_version`, a non-null client upload ID, and the complete server-bounded CaptureMetadata object as deterministic formatted JSON text. Nested unknown keys, arrays, empty strings, nulls, supplementary Unicode, and combining sequences are preserved. Markup-looking metadata remains React text; no raw HTML path was added.

No source filter, browser retry, receipt/lease view, queue UI, agent upload API, or replay UI was added.

## Authority, task, difficulty, and models

- Task: `FRONTEND-UPLOAD-001`; owner `04`; PM status at start: `READY`.
- Activation: `.orchestration/handoffs/PHASE-2-implementation-20260925-01.md`.
- Contract: P2-UPLOAD-v1 revision 2, independently accepted; R08-P2-ARCH-001 resolved. Revision 2 changed uploader origin binding and did not alter the accepted Frontend contract.
- Acceptance scope: AC-P2-04 implementation contribution. AC-P2-04 remains `NOT_RUN` pending actual Backend/uploader/Web verification and independent review.
- Parent difficulty: `중`; bounded typed client and safe nested metadata display with contract regressions.
- Requested parent model: `gpt-5.6-sol / medium`; actual model: `실제 적용 미확인`.
- Subtask A, types/API/tests: `하`, requested `gpt-5.6-terra / high`, actual model `실제 적용 미확인`.
- Subtask B, component/style/tests: `중`, requested `gpt-5.6-sol / medium`, actual model `실제 적용 미확인`.
- Both subagents encountered patch-context/encoding mismatch and returned with no changes or test results. This was a tooling/context issue, not a model-capability or product finding. Parent owner applied and verified the scoped patches.

## Changed files

- `frontend/lib/types.ts`
  - Added manual-only `ManualScreenshotUpload`.
  - Added `ScreenshotSource = "manual" | "agent" | "automation"`.
  - Decoupled `Screenshot` from the write type and made response metadata/version and UUID-or-null client identity explicit.
- `frontend/lib/api.ts`
  - `ApiClient.upload()` now accepts `ManualScreenshotUpload`; multipart and strict 201 behavior remain unchanged.
  - Preserved the pre-existing query Unicode validation change.
- `frontend/components/screenshots.tsx`
  - Added deterministic recursive metadata formatting with ordinal object-key sort and preserved array/scalar values.
  - Added conditional Client Upload ID, Metadata Version, and safe complete Capture Metadata detail display.
- `frontend/app/globals.css`
  - Added narrowly scoped complete/scrollable metadata JSON styles without truncation.
- `frontend/tests/api.test.ts`
  - Added manual multipart field exclusion, strict 201/200 rejection, expanded response, and compile-time write/read separation regressions.
  - Preserved the pre-existing query Unicode test.
- `frontend/tests/components.test.tsx`
  - Added agent/automation/manual detail cases, nested Unicode/empty/null/array/unknown-key display, markup injection safety, and null-ID omission.

The PM-claimed product write set was respected. PM YAML, contract files, mobile proposal, Backend/uploader/shared config, and other-owner artifacts were not modified. Branch/commit: null/null. No Commit/Push or IP check.

## Verification

Environment: Windows PowerShell, `C:\Dev\qa-visual-automation`; Node `v24.19.0`; npm `11.17.0`.

1. `npm.cmd --prefix frontend run test -- tests/api.test.ts tests/components.test.tsx`
   - Initial sandbox run: `FAIL` before test startup with EPERM writing `frontend/node_modules/.vite-temp`; classified as filesystem sandbox restriction, not product failure.
   - Approved rerun: tests executed; 25 passed and one component assertion failed because `getByText("1")` matched Metadata Version and an Expected Strings table position. Rendering was correct.
   - Assertion narrowed to the `Metadata Version` row.
   - Final rerun after the final non-null condition: `PASS`, 2 files, 26 tests.
2. `npm.cmd --prefix frontend run typecheck`
   - Final result: `PASS`, exit 0 (`tsc --noEmit`).
3. `npm.cmd --prefix frontend run build`
   - Final result: `PASS`, exit 0; Next.js 16.3.4 production build compiled, TypeScript completed, and 3 static pages generated.
4. `git diff --check --` on tracked scoped files
   - `PASS`, exit 0. Git emitted only existing LF-to-CRLF working-copy notices; no whitespace error.

Historical Phase 1 results were not relabeled as current evidence. The failed assertion and pre-start EPERM are retained above and are not reported as product PASS.

## NOT_RUN and remaining risks

- Actual agent→Backend→PostgreSQL/storage→Web flow: `NOT_RUN`; `FRONTEND-UPLOAD-VERIFY-001` remains separately gated until matching Backend/uploader submissions and PM activation.
- Real OpenAPI response enum/nullability and actual non-null client ID/metadata readback: `NOT_RUN` for the same gate.
- Browser visual inspection: `NOT_RUN`; targeted DOM behavior, typecheck, and production build cover this implementation submission, while actual Web evidence belongs to the later verification task.
- Independent implementation review: pending. Owner does not self-accept.

Next owner/action: PM 01 records this owner submission as `READY_FOR_REVIEW` without setting AC-P2-04 PASS. After Backend and uploader matching submissions, PM activates `FRONTEND-UPLOAD-VERIFY-001` for actual synthetic end-to-end Web evidence; designated Reviewer 08 later decides implementation acceptance.
