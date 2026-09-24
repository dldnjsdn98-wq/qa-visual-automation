# FRONTEND-WEB-001 — verification evidence

Owner 04 / 2026-09-07. Repository root: current project (`../..` from this file). Architecture revision 2 retained. Independent Frontend review pending.

## Executed final checks

| Command / check | Result | Evidence |
| --- | --- | --- |
| `npm.cmd test` from frontend | PASS | 23 tests, 2 files; final run 23:06 KST, exit 0 |
| `npm.cmd run typecheck` from frontend | PASS | `tsc --noEmit`, exit 0 after final build |
| `npm.cmd run build` from frontend | PASS | Next.js 16.3.4 webpack; compilation, TypeScript, static generation and build traces complete; exit 0 |
| `.\.venv\Scripts\python.exe tests/frontend/run_integration.py --isolated-postgres` from root | PASS | 2 real integration tests, exit 0; actual PostgreSQL 17, repository Alembic config/migrations, actual FastAPI app and TypeScript ApiClient; unique test DB/container cleaned up |
| Browser critical flow | PASS | Real production Frontend on 3001 → actual isolated Backend on 8001; details below |
| Default configured PostgreSQL `SELECT 1` | FAIL / environment | Password authentication failed for user qa_visual on 127.0.0.1:5433; no credentials changed |
| Default persistent deployment full flow | NOT_RUN | Shared DB authentication issue; isolated integration does not certify this deployment |
| Docker Frontend image build, mobile visual QA, exhaustive accessibility audit | NOT_RUN | Local Next production build and desktop browser were verified; these additional checks were not executed |
| Backend owner suite / AC-WEB-11 and AC-WEB-12 acceptance | NOT_RUN by owner 04 | Backend owns its own suite, concurrency/storage/migration evidence and review |

Unit/client tests cover Unicode scalar counting and exact JSON text, NUL/unpaired surrogate rejection before fetch, safe nested-key error paths, invalid query Unicode, PATCH omission/null/empty text, 204, FormData file+JSON metadata without Content-Type override, error/request ID, scoped AND filters/content origin, no automatic retry and wrong-success-status handling, selection/deep-link transitions.

Component tests cover server field errors/input retention, description clearing, empty translation/10,000 supplementary scalars, missing vs empty expectations, loading/empty/delete conflict, stale response suppression, Project filter resets, ambiguous upload guidance, successful-upload navigation and independent detail/expected/content failure states. File-submit component assertions invoke the form submission event; actual file chooser and button click were independently exercised in the browser.

Real integration checks generated OpenAPI route/method/status inventory, key response fields, PATCH nullability and multipart schema. The real client creates Project/Build/Locale/Category/Situation/StringKeys/translations, performs PATCH and 204 DELETE, assigns ordered expectations, preserves CJK/emoji/combining sequences/CRLF/tabs, distinguishes empty/missing, uploads a synthetic PNG, filters screenshots, retrieves detail/expected/original bytes, verifies restrictive deletion and server field errors/request IDs, and checks CORS preflight. No mock services or SQLite replace production API/DB behavior in this suite.

## Browser evidence

In-app browser, desktop viewport, built production application, actual isolated PostgreSQL-backed API. Created synthetic project `browser-qa` with Korean/emoji name; created Build 1.0, ja-JP Locale, Tutorial Category, Welcome Situation. Registered welcome key and Japanese/Korean/emoji/combining text with a newline, assigned it through the confirmation-based Expected mapping editor, selected a synthetic 640×360 PNG through the native file chooser, and clicked Upload. Detail navigation succeeded and showed the original image, all required metadata, Backend-origin original link and current Expected Strings. Visual screenshot inspection found readable metadata/image layout; captured browser error logs were empty. Returned to list, opened detail, used browser Back, and verified Category change clears Situation while the remaining filters/list work.

All browser data lived in the test DB/storage. No real QA/game images were used. Browser tab and owned test servers were closed; runner reported removal of its isolated database and removes its uniquely named container.

## Earlier failures and limits

- Credit-limit auto-review rejections interrupted some tool batches before edits/execution. Missing files were checked on resume; rejected batches were not treated as applied or PASS.
- Restricted execution initially denied npm registry/cache, Python and Docker access. Approved execution enabled installation and tests; no machine Node/npm paths were recorded in product files.
- First test setup accessed window in Node tests; fixed environment guard. File input component simulations did not trigger native required validation in jsdom; form event boundary tests plus real browser chooser/click verified the behavior. A deferred-loader timing test was corrected with the final synchronous-start/async-catch hook. Only final results above are PASS.
- Initial alembic.ini had duplicate path_separator and failed parsing. This was subsequently fixed in the shared repository by another role. Frontend did not change it; final integration uses the real current root config successfully.
- Default local PostgreSQL authentication failure remains independently reproducible; isolated integration uses fresh generated test credentials and does not change the shared database.

## Scope and acceptance

No observed Frontend/Backend mismatch in the exercised revision-2 routes, models and semantics. This is evidence for owner 04's AC-WEB-01..10 and AC-WEB-13 contributions, not an independent acceptance decision. ACCEPTANCE.yaml is unchanged. Phase 1 still requires Backend evidence and Reviewer acceptance. Large metadata selectors load complete paginated catalogs; free-text collection search is current-page-only and labeled, exact String ID search spans pages, and Situation resolution is capped at the approved 1,000 mappings. OCR/quality statuses, automation and later-phase editors are absent.
