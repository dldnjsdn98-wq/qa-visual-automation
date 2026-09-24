# 2026-09-12 consolidated disposition note

The scoped Frontend assessment below remains valid. Its environment-closure inference and statement that the README finding is still open are superseded by [the final review](REVIEW-WEB-001-08.md): R08-WEB-002 is a Backend storage-root MAJOR blocker; full ENV closure is withheld; R08-WEB-001 documentation is RESOLVED. No new Frontend product fix is required. Preserve all dated execution attribution below.

# REVIEW-WEB-001 — scoped independent frontend re-review / 08

Date: 2026-09-11 KST. Difficulty: 상. Repository: `C:\Dev\qa-visual-automation`. Reviewed working tree, including submitted uncommitted/untracked files; HEAD remains `811b1e36199d424d83930f3381c7d71e537bc7d6` and is not the complete submission boundary.

## Disposition

**ACCEPTED — Phase 1 frontend scope. No new blocking frontend finding.** Retain the earlier independent regression evidence and recognize the subsequent independent ENV-P1-DB-001 acceptance. The former environment blocker no longer justifies withholding this frontend recommendation. The existing MINOR root README finding remains separately assigned by the parent; this report does not claim it is fixed.

Recommend that the parent close the frontend portion of the earlier CHANGES_REQUESTED disposition and use the AC recommendations below when reconciling the overall web review. This report does not itself accept the Backend submission, change any AC/Task/Phase state, or activate later phases. Overall REVIEW-WEB-001 acceptance remains the parent's combined decision. A new complete independent browser run is not claimed or imposed as an additional gate: existing owner browser evidence, prior independent automated checks, current static review and independently accepted configured-environment readback are explicitly distinguished below.

## Evidence chronology and reuse decision

1. `FRONTEND-WEB-001-04.md` (2026-09-07) and `../handoffs/frontend.md`: owner 04 submitted 23 frontend tests, typecheck, production build, two real PostgreSQL/FastAPI/TypeScript-client integration tests and a desktop browser critical flow. Its default-DB failure was a limitation at that time.
2. `REVIEW-WEB-001-08.md` (2026-09-08–09): the prior independent reviewer separately executed 54 Backend tests, 23 frontend tests, typecheck, production build and two integration tests, all PASS. Its final CHANGES_REQUESTED concerned required environment closure; the only additional finding was MINOR stale root README guidance. Its incomplete browser attempt did not earn full-flow PASS and the transient missing test project did not establish product data loss.
3. `ENV-P1-DB-001-03.md` and `ENV-P1-DB-001-08.md` (2026-09-09, subsequent closure): owner 03 documented configured migration/head, prior normal Web upload/filter/detail/Expected Strings and controlled restart/readback. The independent ENV reviewer reproduced authenticated configured DB/head and read-only persistence verification, then **ACCEPTED environment closure only**. The prior failures remain historical; successful later checks do not establish their original root cause.
4. This review (2026-09-11) directly read those reports, the 90-file source manifest, frontend implementation/tests and approved revision-2 API contract; compared current source hashes; and inspected the changed persistence verifier. No test, build, integration runner, browser, live-service or DB probe was executed in this turn, following the user's direction to reuse unchanged independent evidence.

### Current read-only SHA-256 comparison

Compared every entry in `REVIEW-WEB-001-08-source-manifest.json` using `Get-FileHash -Algorithm SHA256` against its recorded `sha256`:

| Scope | Result |
| --- | --- |
| Complete manifest | 90 files present; 89 identical; one changed |
| Frontend entries | All 22 identical, including app/components/client/types/navigation, tests, package.json, Next/Vitest/TypeScript config and Dockerfile |
| Architecture contract/specification/fixtures | All seven identical |
| API runtime, schemas, generated OpenAPI/examples and previously inventoried Backend tests | Identical |
| Frontend integration runner | Identical |
| Sole mismatch | `backend/tools/verify_default_persistence.py`; verification-tool correction already covered by the later ENV review |

Manifest file SHA-256: `ecb69dc71258186b7f2ea8114ad641cdb654bfc77a7027034cc5bfe6caa56ae4`.

Verifier old SHA-256: `92233840ed4f201b1aa2881139293d4faed35a60436803359c9d394036b2d5ad`; current: `7177572b2f82f252a8f8a2015910a419c58400af3ff1797c9520e101fdee56fb`. Current source confirms verify mode checks saved/list/detail screenshot ID equality and does not write the manifest; seed and baseline writes remain separate explicit modes. This helper is not imported by frontend runtime or its regression suites. No helper mode was run here.

Inventory cross-check under frontend, Backend, architecture and frontend test-runner directories found these non-generated files outside the old manifest: `frontend/package-lock.json`, `frontend/.dockerignore`, `backend/requirements.lock`, and `tests/frontend/.gitkeep`. Thus the 90-file comparison is not represented as a complete dependency/environment fingerprint. Frontend lockfile and dockerignore have no working-tree change relative to HEAD; their file timestamps precede the prior independent runs. Current frontend lockfile SHA-256 is `052ff56ee2fdf803215cb0b7d347d76535f44c71b9a57aad509ed6ee70eb6d77`. Backend requirements.lock likewise predates those runs but is untracked; no prior hash is available in this manifest. Installed dependencies, generated build files and current service availability were not revalidated.

The old manifest itself was an end-of-review snapshot, not a retroactive hash capture at test execution. Preserve that qualification. In combination with the prior review's source-timing account and unchanged relevant code/config/tests, no evidence warrants repeating suites for this frontend re-review. The historical PASS results remain attributed to the prior reviewer, not relabeled as new executions.

| Retained prior independent execution | Result / scope |
| --- | --- |
| `npm.cmd test` in frontend | PASS, 23 tests in two files: 13 client cases (including parameterization), 10 component cases |
| `npm.cmd run typecheck` in frontend | PASS, `tsc --noEmit` |
| `npm.cmd run build` in frontend | PASS, Next.js 16.3.4 production webpack compilation/typecheck/static generation/traces |
| `.\.venv\Scripts\python.exe tests/frontend/run_integration.py --isolated-postgres` | PASS, two actual client/API/OpenAPI/PostgreSQL integration tests; disposable DB/storage, not default deployment certification |
| Prior Backend suite | PASS, 54 tests; contextual API/CRUD/scope evidence, not a new Backend review in this report |

## Critical-path inspection and concrete conclusions

| Area / source | Review conclusion and evidence boundary |
| --- | --- |
| Upload — `frontend/components/screenshots.tsx:9`, `frontend/lib/api.ts:83` | Requires file and Build/Locale/Category/Situation; project is scoped in the path. Client checks PNG/JPEG MIME, nonempty/20 MiB size and filename/metadata Unicode. Sends exactly file plus JSON-string metadata with manual source and browser-owned multipart boundary; requires HTTP 201 before detail navigation. Server remains authoritative for image decoding, full request limits and scoped relationships. Existing client/component tests and real PNG integration support this path; actual chooser/button evidence is owner browser evidence. |
| Ambiguous upload — `frontend/components/screenshots.tsx:12`, `frontend/lib/api.ts:47` | Network failure, 5xx and contract errors retain the selected file, show possible-commit/list-inspection guidance and disable ordinary resubmission until manual acknowledgement or file change. No automatic retry. Busy fieldset prevents ordinary repeat clicks; completion after navigation does not force a stale detail route because the component tracks mount state. Existing tests exercise 503 guidance, one attempted request, wrong success status and successful navigation. This is manual guidance, not idempotency or proof that users inspected the list. |
| Filters/navigation — `frontend/lib/navigation.ts:10`, `frontend/components/workspace.tsx:27`, `frontend/components/screenshots.tsx:33` | Project changes clear all dependent selections; Category clears Situation. All selected screenshot filters combine in one scoped request. Workspace page key remounts on scope/filter changes, resetting list offset and in-progress forms. Hash URLs preserve selected context and detail ID. Lookup catalogs page at 100; screenshots at 50. No implicit locale/build fallback. Existing tests cover scoped URL construction, Project reset and navigation round-trip; Category reset is also present in prior owner browser evidence. |
| Stale reads — `frontend/components/common.tsx:6` | Identity includes request key and reload generation; old data is hidden immediately on identity change, effect cleanup aborts, and completion only updates when its signal is not aborted. A dedicated existing deferred-response component test checks late old-scope responses cannot replace new data. |
| Detail/content — `frontend/components/screenshots.tsx:41`, `frontend/components/screenshots.tsx:53` | Displays Project, Build, Locale, Category, Situation, manual Source, UTC upload time, dimensions/bytes and screenshot ID from returned metadata, using labels with ID fallback. Detail, Expected Strings and image have independent requests/error/reload states. Binary original fetch and original link resolve to Backend origin; foreign-origin content URLs are rejected. Blob URLs are revoked on cleanup; decode failure offers reload. Existing component test directly exercises storage failure while metadata/expectations remain visible. Separate detail-error, expected-error and image-decode-error branches were statically inspected; those are not three independently exercised failure tests. |
| Expected Strings — `frontend/components/common.tsx:62`, `frontend/components/strings.tsx:9`, `frontend/lib/api.ts:77` | Uses screenshot's stored context through screenshot expected endpoint, not current top-level filters. Displays API order/position, stable String ID, text/status and missing count; labels current catalog rather than upload-time snapshot. Null/missing, present empty and multilingual text are distinct; `pre-wrap` preserves displayed whitespace. Mapping replacement is explicit and confirmed, ordered, capped at 1,000, rejects duplicates and allows clearing. Situation preview requires Build/Locale. Real integration verifies ordered missing/empty/present, both resolver endpoints and current-catalog changes after translation PATCH/DELETE. Mapping editor confirmation is source plus owner browser evidence, not a dedicated component test. |
| CRUD/Unicode/errors — `frontend/components/catalog.tsx:19`, `frontend/lib/api.ts:6`, `frontend/components/common.tsx:35` | Generic editor retains inputs on rejection, blocks immutable identity edits, sends only changed mutable PATCH fields and permits explicit description null plus empty translation. Client rejects NUL/residual surrogates recursively with safe invalid-key container paths and counts supplementary scalars correctly; it does not normalize outgoing accepted JSON text. HTTP error envelope/code/field paths/request ID and restrictive-delete explanation remain visible; DELETE 204 bypasses JSON parsing. Existing component/client cases cover these semantics; exact CRLF/tab transport is client/integration evidence, not a claim about native textarea editing of every line-ending form. |

Client request/response types and methods match the approved contract's resource fields, scoped CRUD, mutable/nullability rules, screenshot multipart/status/content semantics, AND filters and current Expected Strings model. The unchanged generated OpenAPI and existing integration schema assertions reinforce that comparison. No confirmed Phase 1 frontend/API mismatch was found in the reviewed paths. Page-local free-text collection search is explicitly labeled; exact String ID search is server-filtered, and Situation search covers the complete capped mapping. These are documented limits, not missing full-text API functionality.

## Findings and previous blocker disposition

- **ENV-P1-DB-001: RESOLVED for this recommendation by subsequent independent acceptance.** `ENV-P1-DB-001-08.md` records configured authenticated DB/head and retained screenshot/metadata/bytes/exact multilingual expectations/CORS verification. Migration application, restart execution and normal Web-form observations remain attributed to owner 03. This scoped report recognizes that closure; it does not reproduce it or assert services are running today.
- **R08-WEB-001: MINOR, nonblocking, separately assigned; not closed here.** At inspection `README.md:3`, `README.md:5`, `README.md:38` and `README.md:110` still describe Bootstrap-only/no CRUD/upload/frontend behavior tests, contrary to current implementation and package scripts. The parent is assigning the fix separately. Verify that separate documentation change against current scripts/runbooks and retain historical evidence as historical; no product suite rerun is required solely for that correction.
- **New frontend defects: none confirmed requiring changes.** No product or shared-state fix is proposed in this report. Retained coverage limitations below are not silently promoted to additional required blockers.

## Covered ACs and parent recommendations

PASS recommendations below combine current source inspection with attributed prior executed evidence. They do not say every operation has been clicked in a new browser session. AC-WEB-01..10 are recommended PASS for the frontend contribution; the parent must combine the Backend review and already accepted ENV evidence for complete criterion disposition.

| AC | Recommendation | Covered evidence |
| --- | --- | --- |
| AC-WEB-01 Project CRUD | PASS — frontend contribution | Generic create/edit/delete/list, explicit selection, PATCH/null/error retention; prior client integration and Backend CRUD evidence |
| AC-WEB-02 Build CRUD | PASS — frontend contribution | Scoped generic CRUD; immutable label/description-only PATCH; real client create/list and restrictive delete; prior Backend scoped CRUD |
| AC-WEB-03 Locale management | PASS — frontend contribution | Scoped editor/list/delete, immutable code and mutable name; real API canonicalization; prior Backend scoped CRUD |
| AC-WEB-04 Category management | PASS — frontend contribution | Scoped CRUD and Category-to-Situation selection reset; prior client/API and owner browser evidence |
| AC-WEB-05 Situation management | PASS — frontend contribution | Category association, immutable category/slug, mutable name/description, scoped CRUD and mapping workflow |
| AC-WEB-06 String ID multilingual management | PASS — frontend contribution | Stable StringKey registration; Build/Locale translation editor; scalar validation; empty/missing distinction; exact client/API Unicode readback and PATCH/DELETE |
| AC-WEB-07 Manual screenshot upload | PASS — frontend contribution | FormData/client/component and actual isolated API tests; owner 04 desktop chooser-to-detail flow; owner 03 default Web upload plus independently accepted ENV readback |
| AC-WEB-08 Screenshot metadata | PASS — frontend contribution | List/detail rendering of required metadata; schema/integration assertions and independent configured metadata/content readback recorded in ENV review |
| AC-WEB-09 Expected Strings display | PASS — frontend contribution | Ordered current-catalog display, empty/missing/multilingual component test, both real API resolvers and translation-change behavior; owner browser display and independent configured readback |
| AC-WEB-10 Project/Build/Locale/Situation filters | PASS — frontend contribution | Scoped AND queries, dependent resets, remount pagination reset and stale-read suppression; prior client/component/API tests, owner browser filtering and independent configured filtered-list readback |
| AC-WEB-11 Fresh migrations | Outside this frontend disposition | Prior independent migration/integration and subsequent ENV head evidence remain available to parent/Backend review |
| AC-WEB-12 Backend tests PASS | Retain prior independent PASS; outside new frontend certification | 54-test independent execution in original full report; not rerun here |
| AC-WEB-13 Frontend build/behavior tests PASS | PASS — retain prior independent result | 23/23, typecheck, production build and two integration tests; unchanged frontend source/config/tests verified here |

## Browser attribution, remaining gaps and write boundary

Owner 04's isolated desktop browser exercise covers catalog creation, multilingual string/mapping setup, native synthetic-file selection, Upload click, image/metadata/current expectations, list/detail/Back and Category reset; readable layout and empty captured error logs are owner observations. Owner 03's default browser exercise used API-seeded synthetic catalogs followed by actual Web selection/upload/detail/Expected Strings/filtering; do not describe that as default browser CRUD for every catalog.

The original full independent review saw only partial isolated browser screens and a normal Projects read, with interrupted/unavailable-service attempts; no independent full browser PASS follows from those observations. The subsequent independent ENV reviewer repeated API/DB readback, not browser clicks or restart. This review used no browser, took no screenshots and did not check current availability.

Unexecuted here and not certified by carried-forward evidence: clean dependency reinstall/current installed-package identity, new production build, Docker frontend image build, mobile visual QA, exhaustive accessibility, all CRUD/error combinations through a real browser, and later phases. Existing component upload assertions submit the form directly and do not replace native chooser/constraint-validation evidence. These limits are retained without reopening the accepted ENV issue or inventing a new gate.

Only `.orchestration/reports/REVIEW-WEB-001-frontend-08.md` was written by this task. No product/shared-state/owner-report/old-manifest edits, tests generating cache/build output, service start/restart, database/storage mutation, migration, commit or push.
