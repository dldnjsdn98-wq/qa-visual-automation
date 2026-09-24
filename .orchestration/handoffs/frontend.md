# Frontend handoff — FRONTEND-WEB-001

- Task / owner: FRONTEND-WEB-001 / 04 QA Frontend Engineer.
- Status: READY_FOR_REVIEW under the user's explicit instruction; review result null. Architecture revision 2 DONE/ACCEPTED, AC-ARCH-01 PASS and PM activation retained. Phase 1 remains IN_PROGRESS.
- Changed scope: frontend/app/page.tsx and globals.css; frontend/components/{workspace,common,catalog,strings,screenshots}.tsx; frontend/lib/{api,types,navigation}.ts; frontend/package.json and package-lock.json; frontend/vitest.config.mts; frontend/tests/; frontend/Dockerfile and README.md; tests/frontend/run_integration.py; own reports/handoffs and own Task record. Backend and architecture contracts unchanged by owner 04.
- Branch / commit: main; no new commit by Frontend. Existing Role-10 checkpoint `811b1e36199d424d83930f3381c7d71e537bc7d6` contains partial work only; final changes remain uncommitted.

## Implemented screens and API use

Dashboard, Projects, Builds, Locales, Categories, Situations, Strings (Translations / String Keys / Expected settings), Screenshot Upload, Screenshots and Screenshot Detail. Bookmarkable hash navigation preserves Project/filter context and supports browser Back. Existing Next.js/TypeScript skeleton retained.

One typed API client uses configurable NEXT_PUBLIC_API_BASE_URL (default loopback port 8001). Consumes `/api/v1/projects` and scoped `builds`, `locales`, `categories`, `situations`, `string-keys`, `strings` CRUD; Build/Situation `expected-string-keys` GET/PUT and `expected-strings` GET; Screenshot POST/list/detail/content/expected-strings GET. Upload uses exactly file + JSON-string metadata FormData with browser boundary, source manual and 201-only success. Detail shows image, Project, Build, Locale, Category, Situation, Source, UTC upload time and current-catalog Expected Strings.

PATCH emits only changed mutable fields, with explicit nullable description clearing. Unicode scalar validation/counting preserves valid text, whitespace and empty translations. Missing translations stay distinct. Server field paths and request IDs are shown, inputs remain after errors, restrictive deletes are explained, 204 has no JSON parse. Project/Category changes clear dependent selections; filter changes reset page state and stale requests cannot replace current results. Upload timeouts/503 never trigger automatic retry.

## Tests / build

- PASS: `npm.cmd test` — 23 tests.
- PASS: `npm.cmd run typecheck`.
- PASS: `npm.cmd run build` — final production build, exit 0.
- PASS: `.\.venv\Scripts\python.exe tests/frontend/run_integration.py --isolated-postgres` — 2 actual OpenAPI/PostgreSQL/FastAPI/TypeScript-client integration tests.
- PASS: desktop browser critical create/catalog/string/mapping/upload/list/detail/back/filter flow and visual detail inspection; no browser console errors observed.
- Exact commands, coverage, prior failures and NOT_RUN limits: [verification report](../reports/FRONTEND-WEB-001-04.md).

## Contract issues / limitations / next owner

- No observed mismatch in exercised approved revision-2 API routes, field names, PATCH semantics, multipart, content URLs or Expected Strings. Generated OpenAPI was verified against client expectations; no unilateral contract workaround was made.
- **Environment issue remains:** default configured PostgreSQL rejects qa_visual password authentication at 127.0.0.1:5433. Real integration/browser QA passed on isolated test databases. Backend/PM must resolve shared deployment credentials before accepting the default persistent deployment; Frontend has not changed them.
- Earlier duplicate path_separator in alembic.ini is now resolved in the shared repository; final tests use the real config. No owner-04 edit to that file.
- Page-local text search is labeled; exact String ID search is server-filtered across pages. Very large metadata catalogs may benefit from future server-backed searchable selectors. Filter changes reset forms to prevent writes in stale scope. No full-text API, historical expectations, screenshot deletion, OCR or Phase 2 UI added.
- NOT_RUN: Docker Frontend image build, mobile visual QA, exhaustive accessibility audit and Backend owner's full suite. No PASS is claimed for these.
- Acceptance contribution: AC-WEB-01..10 and AC-WEB-13 evidence submitted; no ACCEPTANCE.yaml PASS or Phase acceptance set by owner 04. AC-WEB-11/12 stay Backend-owned for evidence.
- Next owner: 01 PM coordinates shared deployment issue and Reviewer 08 after both web tasks are READY_FOR_REVIEW. Reviewer approval is required before acceptance or later-phase UI work.

Root sync: current repository state/history/handoffs were used; four architecture hashes match approved Reviewer fingerprints. No previous OneDrive absolute references found in searched source/config/docs; old workspace was not accessed after migration instruction.
