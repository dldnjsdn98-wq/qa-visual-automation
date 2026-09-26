# FRONTEND-OCR-001 / owner 04

Date: 2026-09-25 KST.  
Submission status: `READY_FOR_REVIEW` requested. This is owner implementation evidence, not independent acceptance or an AC-P3 PASS claim.

## Result

Implemented the Frontend slice of the accepted P3-OCR-v1 contract at exact SHA-256 `46940dd1dd7775422213b2ba422b63650f4e83740e034cf29dc83f23970acb82`.

Screenshot Detail now provides profile selection and explicit run creation, stores one exact pending request and `client_run_id` in screenshot-scoped session storage, and reuses that request after transport, 5xx, or contract-ambiguous outcomes. New and replay responses accept 202 and 200 and expose `Location`, `Retry-After`, and `Idempotency-Replayed`.

Run history, the latest completed run, and a deep-linked selected run are separate. The selected visible active run polls after two seconds, honors response `Retry-After`, backs off 5/10/20/30 seconds after read failures, and aborts on hidden state, run change, and unmount. Processing state, durable processing errors, and verification quality are rendered separately.

The result view separates current Expected Strings from the immutable run snapshot; shows snapshot/configuration identity, source hash, summaries, paged expected/region/item tables, and raw OCR text. Confidence zero, null score, empty text, missing values, empty pages, and unknown enum values have explicit displays. The mandatory original-raster-v1 coordinate table is present. Overlay rendering is deliberately omitted with a visible EXIF/orientation notice because browser-to-raw-raster orientation mapping has not been proven.

Existing Phase 2 upload/list/detail/source/metadata behavior was preserved.

## Authority, scope, difficulty, and models

- Activation: `.orchestration/handoffs/PHASE-3-implementation-01.md`; PM status at start: `FRONTEND-OCR-001 READY`.
- Contract: `docs/architecture/phase-3-ocr-contract.md`, SHA-256 above; independent review report SHA-256 `c9b723eca12e2f4df254e910c47fbf6104647301af9728c55d287760a5a268da`.
- Acceptance scope: Frontend contribution to AC-P3-01..04. All remain `NOT_RUN` pending matching Backend03/OCR05 readiness, actual integration, and independent review.
- Parent difficulty/model: medium; requested Codex Sol/medium; actual model identity `unverified`.
- Subtask A (types/API/contracts): requested Sol/medium; actual model `unverified`.
- Subtask B (navigation/workspace): requested Sol/medium; actual model `unverified`.
- No commit, push, deployment, database reset, data deletion, security change, or IP check was performed.

## Changed files and final SHA-256

- `frontend/lib/types.ts` — `9b2168f035a08edaacb82dd6c47b1127eadac565249b4cbc08735b5bcc052757`
- `frontend/lib/api.ts` — `d6ef85996af23b93736d4fbfd09117ef24a6e3f2011edfbe17a80d65b0d356e5`
- `frontend/lib/navigation.ts` — `0d61220c5919007f218ac9d2200c6009aaa1f119370e9e14e2ef591b9e2c345c`
- `frontend/components/screenshots.tsx` — `2f0dcddbf0be66eb8394219bee0a666d7727dacbf0b388f54f413dea41f203d4`
- `frontend/components/workspace.tsx` — `19f48b3aeb0c3197548060242f1e408370428044445f2845fdc88b4aa9be3413`
- `frontend/app/globals.css` — `4a9f5dc22b65a12f8a8465cce9818032c2b98ee63f6099f9359a76a21211fad8`
- `frontend/tests/api.test.ts` — `13950786ee324f9dc18d998d6dc97ba8c27273363b17838aace9bfb2f0842199`
- `frontend/tests/components.test.tsx` — `6ff19229ebf3c8ee0b036afeca4a1b8fbd3ce78ec30e606cf0b6906268a727db`
- `frontend/tests/integration/contract.test.ts` — `72d9cf2522e27490c84dc3d53e4097ff10f2ec99c325d7204355e8d1084dd46b`
- `tests/frontend/run_integration.py` — `f2b05ca8219deedd6087d39d5d81e0e2fc4f1237486812c85703ea01e8e0acec`

The integration harness adds `--verify-ocr-web` without changing `--verify-upload-web`. It refuses OCR Web preparation unless the isolated Backend exposes the profile endpoint and at least one AVAILABLE profile. It records product acceptance as NOT_RUN until an operator completes the real lifecycle.

## Verification

Environment: Windows PowerShell, `C:\Dev\qa-visual-automation`; Next.js 16.3.6.

1. `npm test -- --configLoader runner` in `frontend`
   - Final: `PASS`, 2 files, 37 tests.
   - One intermediate assertion used a singular query for four valid zero cells; the assertion was narrowed to the explicit plural condition and the suite passed.
2. `npx tsc --noEmit --incremental false` in `frontend`
   - Final: `PASS`, exit 0.
   - The ordinary incremental command initially hit EPERM on the pre-existing locked `tsconfig.tsbuildinfo`; disabling incremental output verified the same source typecheck.
3. Production build
   - Direct `npm run build` was blocked by EPERM on the pre-existing locked `frontend/.next/trace-build`.
   - Final isolated source-copy command used the same source, package metadata, node_modules, Next.js 16.3.6 and `--webpack`: `PASS`; compile, TypeScript, page generation, optimization, and trace collection completed. The temporary directory was removed after exact path verification.
4. `.pytest_cache\agent-clean-win\Scripts\python.exe -m py_compile tests/frontend/run_integration.py`
   - `PASS`, exit 0. The repository `.venv` launcher was stale and the bare `python` command was unavailable; neither is reported as a product failure.
5. Scoped `git diff --check`
   - `PASS`, exit 0. Only LF-to-CRLF working-copy notices were emitted.

## NOT_RUN and remaining limits

- Actual Backend + OCR worker + Web lifecycle, real profile/model, PostgreSQL persistence, run polling, result pages, and rerun lineage: `NOT_RUN`; Backend03 and OCR05 matching readiness is not yet available.
- `frontend/tests/integration/contract.test.ts` against the actual Phase 3 OpenAPI: `NOT_RUN` for the same dependency gate.
- AC-P3-01, AC-P3-02, AC-P3-03, AC-P3-04: all `NOT_RUN`.
- Browser visual/orientation validation: `NOT_RUN`. The UI therefore does not draw an overlay and says why.
- Reviewer08 review: pending. Owner does not self-accept.

Next action: PM01 records this owner submission as `READY_FOR_REVIEW`. Actual `--verify-ocr-web` execution waits for matching Backend03/OCR05 readiness; Reviewer08 reviews only after PM coordination.
