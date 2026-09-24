# 2026-09-13 final update — ACCEPTED

Designated affected-scope re-review is complete: **R08-WEB-002 RESOLVED, ENV full closure ACCEPTED, AC07 PASS recommended, REVIEW-WEB-001 ACCEPTED**. Actual configured root, preserved original/new references and hashes, exact metadata/Unicode and final cwd regression were independently verified. See [final closure](R08-WEB-002-closure-08.md) and [PM handoff](../handoffs/R08-WEB-002-closure-08.md). Prior limits and failures below remain historical; current all-AC PASS recommendation and closure supersede their pending/FAIL dispositions. PM owns final state updates.

---

# Historical REVIEW-WEB-001 — Independent Reviewer 08

Review window: 2026-09-08 through 2026-09-12 KST. Root: current repository. Implementation owners: 03 Backend / 04 Frontend. Branch/commit created by Reviewer: null/null. Baseline HEAD inspected: `811b1e36199d424d83930f3381c7d71e537bc7d6`; submissions include uncommitted and untracked files, so HEAD alone is not the reviewed artifact.

## Disposition

**Late working-tree update, 2026-09-12 12:22 KST:** `local.py:11` now uses `parents[3]`. The relative-root arithmetic is corrected in the working tree. This arrived after the source audits below; their path evidence describes the preceding submitted version. No corresponding completed preservation/retest handoff was found at this cutoff. R08-WEB-002 remains OPEN **pending verification of the correction and existing-object preservation**, not because the current line still says `parents[4]`. Earlier 54-test evidence predates this product change and does not validate it.

**CHANGES_REQUESTED — R08-WEB-002, MAJOR product storage-root defect, correction verification pending.** The reviewed submission stored default uploads outside the repository; the late arithmetic correction above still needs preservation/retest evidence. The original environment's authenticated DB/readiness/restart readback has successful evidence, but that readback preserved the image in the wrong directory. ENV-P1-DB-001's preliminary environment-only acceptance is qualified/superseded pending corrected storage-root and preservation verification. Previous product tests remain PASS in their actual test environments. Open findings: CRITICAL 0 / MAJOR 1 product issue / MINOR 0. R08-WEB-001 documentation correction is RESOLVED. No Architecture rewrite or Frontend product rework is requested.

Read the current role prompt, PROJECT_STATE/TASKS/ACCEPTANCE/DECISIONS, PM activation handoff, both owner reports and handoffs, approved architecture contracts, implementation and test sources. ARCH-001 revision 2 remains accepted, AC-ARCH-01 PASS and R08-ARCH-001 RESOLVED. This review does not reopen that issue or promote later phases.

Final Task/AC/Phase changes are PM-owned under `handoffs/REVIEW-WEB-001-01.md`. This report records the actual independent review and recommendations; the YAML READY/null/NOT_RUN values are not a claim that this review never ran. PM must reconcile them against this evidence.

## Independently executed evidence

Commands below run from repository root unless noted. Results are Reviewer executions, separate from owner submissions.

| Command / check | Result | Environment and limits |
| --- | --- | --- |
| `.\.venv\Scripts\python.exe --version` | PASS, Python 3.12.10 | Project runtime; initial restricted launch failure resolved with approved execution. |
| `.\.venv\Scripts\python.exe backend/tools/run_postgres_tests.py -q --tb=short --junitxml=.orchestration/reports/reviewer-backend-windows.xml` | PASS, 54 tests, 0 failures/errors/skips, 2 warnings | Windows, real isolated PostgreSQL; XML timestamp 2026-09-08 21:21:54 KST, suite time 5.338 s. Disposable DB/container resources; not the configured persistent deployment. |
| `npm.cmd test` from `frontend/` | PASS, 23 tests / 2 files | Component and ApiClient behavior. Initial cache EPERM resolved by approved execution. |
| `npm.cmd run typecheck` from `frontend/` | PASS | TypeScript check; no product edits by Reviewer. |
| `npm.cmd run build` from `frontend/` | PASS | Next.js 16.3.4 production compilation, type checking, static generation/traces completed, exit 0. |
| `.\.venv\Scripts\python.exe tests/frontend/run_integration.py --isolated-postgres` | PASS, 2 tests | Actual TypeScript ApiClient, FastAPI, Alembic and temporary PostgreSQL/storage; no mocked API or SQLite. Runner completed cleanup. |
| Configured DB read-only `SELECT 1,current_database(),current_user`; configured app TestClient `/ready` on 09-08 | BLOCKED: OperationalError; HTTP 503 | Target 127.0.0.1:5433, DB/user qa_visual. Sanitized exception did not independently prove the authentication root cause. |
| Same configured read-only SELECT and live API `/ready` during early 09-09 continuation | PASS: `(1,qa_visual,qa_visual)`; live HTTP 200 | Evidence of a working connection at that time, not full closure or restart durability. |
| Same configured read-only SELECT and configured TestClient `/ready` at 2026-09-09 23:29 KST | BLOCKED: OperationalError / SQLSTATE unavailable; HTTP 503 | No listeners found at 3001/8001/5433 in that inspection. Browser navigation to 3001 returned connection refused. Do not label this an authenticated-password rejection. |

Read-only DB probe imports `backend.app.config.get_settings`, `backend.app.db.engine`, opens a connection, executes `SET TRANSACTION READ ONLY` and the SELECT above. It prints only host/port/database/user and exception class/SQLSTATE. The readiness probe uses the normal `backend.app.main.app` without session/storage overrides. No secrets, full environment dump, credential changes, user DB migrations, downgrades or volume resets were performed by Reviewer.

The two integration tests assert generated OpenAPI routes/fields/PATCH nullability/multipart, create all catalogs, preserve CJK/emoji/combining marks/CRLF/tabs, distinguish missing from empty translations, replace ordered expectations, upload original PNG bytes, filter/read detail/content/expectations, observe restrictive deletion and 422 field errors/request IDs, and verify CORS. Component tests add loading/empty/error states, stale-response suppression, dependent filter reset and ambiguous-upload guidance. These support product behavior only within their actual test environments.

## Scope and submission changes inspected

- Backend: scoped relationships and restrictive deletion; StringKey identity and per-build/locale StringEntry uniqueness; current-catalog Expected Strings with ordered missing/empty semantics; strict recursive Unicode validation and pre-sanitization multipart filename validation; closed request/query contracts and safe errors; storage staging/no-overwrite publication/compensation/ambiguous commit and exclusive reconciliation; additive domain migration/model parity; READ COMMITTED writes and serialized expectation replacements with consistent reads.
- Frontend: one typed Backend-origin client, status/error/request-ID handling, multipart boundary owned by browser, preserved Unicode and explicit PATCH omission/null, scoped filters/pagination and stale-response protection, metadata/expected/content independent error states, manual retry after ambiguous upload failure.
- Existing submitted changes relative to HEAD (including catalog/expected mapping transaction behavior, multipart validation, OpenAPI/schema fields and screenshot indexes) were included in the 54-test and integration executions. Git diff is not an exact owner revision boundary because the workspace is shared.
- Since that suite timestamp, two Backend diagnostic helpers were inspected: `backend/tools/check_default_environment.py` and `backend/tools/verify_default_persistence.py`. The later ENV-P1-DB-001-03 report/handoff arrived on 09-09. The verifier was corrected to require the original screenshot ID and avoid manifest writes in verify mode; separate baseline mode refuses overwrite. Reviewer independently ran the corrected verifier successfully with unchanged baseline hash. That resolved verifier issue is not a remaining blocker.
- `REVIEW-WEB-001-08-source-manifest.json` records 90 source/test/architecture hashes from 09-09, not a retroactive proof of the exact bytes used in earlier runs. On 09-11, 89 still match; only the persistence verifier differs, with the correction above. No runtime/frontend source delta was found. The newly discovered storage-root bug was present in the tested submission; tests using absolute temporary storage paths do not cover it.
- Checked source/config/docs for prior OneDrive absolute references. No matching old absolute path found in that search; only a historical sentence in the Frontend handoff mentions OneDrive. Old root was not accessed. Ignore rules cover credentials, local images/storage, virtual environments and build/dependency outputs. No new hardcoded machine executable/root path was introduced.

## Browser evidence boundary

Reviewer started an isolated browser QA session and observed Dashboard/Projects, project selection and Upload form. A seeded test project later returned RESOURCE_NOT_FOUND and the API project list was empty. The continuation crossed process/environment changes; the original session handles were no longer available. This observation is inconclusive and is **not** reported as product data loss. The browser flow was not completed and earns no independent full-flow PASS.

During the early 09-09 continuation, the actual normal web Projects screen displayed the owner's synthetic `env-p1-db-7c0c2f92` record. At 23:29, the normal page could not be opened (connection refused). After Owner restored/restarted services, Reviewer independently opened the default Web, selected Project/Build/Locale/Category/Situation filters, opened the original screenshot detail and verified the metadata, Backend-origin original link, rendered image (complete, natural size 128x72), TITLE_GREETING and exact multilingual Expected Strings. Visual inspection found the image/metadata/table readable. This is a completed default read-side browser check, not a new independent browser creation/upload run. Owner 04's full desktop browser flow and Owner 03's default browser upload remain explicitly owner evidence.

## Later configured-environment evidence and correction

Owner `ENV-P1-DB-001-03.md` records additive upgrade/current head and an ordinary DB/API restart with unchanged container/volume, retained original record IDs/hash and no reseeding. Reviewer independently reran `.\.venv\Scripts\python.exe -B backend/tools/check_default_environment.py` and `.\.venv\Scripts\python.exe -B backend/tools/verify_default_persistence.py verify`: PASS. A separate read-only DB/source-head comparison and HTTP reads corroborated the original catalog, all filters, detail, image hash and both Expected Strings routes. These were configured PostgreSQL/storage reads, not isolated test DB results. Migration application and controlled restart were Owner executions; Reviewer did not stop the Owner's API. See `ENV-P1-DB-001-08.md` for attributed commands and hashes.

On 09-11, the highest-difficulty review found that the reports' claim of repository-relative storage was incorrect. Exact-path read-only checks find the original synthetic image under `C:\Dev\storage\local`, matching the recorded SHA-256, and absent at the contracted repository storage path. Thus DB authentication/readiness and observed same-path restart retention remain valid PASS evidence; correct storage placement and host/Compose consistency do not. Do not erase the successful checks or repeat the old authentication diagnosis as current fact. Full environment closure requires the R08-WEB-002 correction/preservation checks.

Difficulty allocation on 09-11: highest/high subagent checked storage, data integrity, scoped transactions and Unicode; medium subagent checked typed client/API/UI behavior and AC coverage; low/lowest subagent checked evidence, manifest drift, README lines and state authority. Primary Reviewer independently reproduced the storage path calculation and exact fixture presence, reconciled conflicting preliminary conclusions, and owns this final disposition.

## AC recommendations for PM

PASS below evaluates each criterion using the independent tests, inspected Owner submissions and later configured-environment evidence with the attribution above. The storage-root defect directly fails AC-WEB-07; it does not invalidate unrelated passing behaviors. Phase acceptance still requires every required AC PASS, required issue closure and independent review ACCEPTED.

| AC | Independent evidence | Recommended status / remaining condition |
| --- | --- | --- |
| AC-WEB-01 Project CRUD | Backend `test_project_crud`, actual ApiClient integration; default browser catalog read | PASS. |
| AC-WEB-02 Build CRUD | Parametrized scoped CRUD, duplicate concurrency, actual client creation/restrictive deletion; default record readback | PASS. |
| AC-WEB-03 Locale management | Scoped CRUD, canonicalization/validation, actual client locale; default record readback | PASS. |
| AC-WEB-04 Category management | Scoped CRUD/relationships and real client; default record readback | PASS. |
| AC-WEB-05 Situation management | Scoped CRUD/category relationship and real client; default record readback | PASS. |
| AC-WEB-06 String ID multilingual management | Unicode accepted/rejected cases, unique scope, real client exact text/empty/missing; configured exact text readback | PASS. |
| AC-WEB-07 Manual upload | Isolated PNG/JPEG/FormData tests PASS, but actual default original resides outside contracted root | **FAIL — R08-WEB-002**, required Backend correction and preservation/root regression. |
| AC-WEB-08 Screenshot metadata | Full response fields, scope/MIME/dimensions/hash and invalid metadata tests; configured detail/browser metadata | PASS for metadata accuracy; file-placement defect tracked in AC07. |
| AC-WEB-09 Expected Strings display | Ordered current catalog/missing/empty tests, shared endpoints, configured API and browser display | PASS. |
| AC-WEB-10 Filters | AND/time/scope validation, client routing and resets; configured browser combined filters | PASS. |
| AC-WEB-11 Fresh domain migrations | Independent fresh migration/model roundtrip and integration migrations; Owner default additive upgrade and independent current/source head match | PASS. User DB was not downgraded. |
| AC-WEB-12 Backend tests PASS | Independent 54/54 Windows real PostgreSQL suite | PASS for test criterion. Linux 54/54 remains Owner evidence, not rerun. |
| AC-WEB-13 Frontend build/behavior PASS | Independent 23/23, typecheck and production build, 2 real client tests | PASS for build/behavior criterion; broader deployment approval remains withheld. |

## Issues and requests

### R08-WEB-002 — default relative storage resolves outside the repository

- Severity: **MAJOR**, status OPEN, required product fix. Task: BACKEND-WEB-001 / REVIEW-WEB-001. Owner: 03 Backend; PM 01 coordinates data preservation and resubmission.
- File: `backend/app/storage/local.py:11` and `:18`. Contract: `docs/architecture/data-flow.md:29`, `backend/README.md:24`; deployment comparison: `docker-compose.yml` Backend storage environment/mount.
- Problem: `Path(__file__).resolve().parents[4]` resolves to `C:\Dev`, so default `storage/local` becomes `C:\Dev\storage\local`. The contracted repository-relative location is `C:\Dev\qa-visual-automation\storage\local`. Compose instead explicitly uses `/app/storage/local` bound to repository `./storage/local`; the two documented startup modes do not read the same objects.
- Observed evidence: the original synthetic object `objects/41ee9635-80f5-4dfd-8c7f-25c4be181f47/383d49f8-1783-4910-a567-dcd15992c253.png` exists under the outside-repository root, SHA-256 `ebfa933afb0bfbe51ae0e2eb059cb58b4dfd22b6fcb67048450257b78b194135`, and does not exist under the contracted repository root. This was checked by exact path only; no scan/move/delete of user images.
- Reproduction/confirmation: enumerate `Path('backend/app/storage/local.py').resolve().parents` from the repository (index 3 is the repository, index 4 its parent), then compare the line-18 join with the required root. Primary Reviewer independently reproduced the parent calculation with PowerShell `Get-Item` parent enumeration and used `Test-Path -LiteralPath` on the two exact synthetic paths; the integrity reviewer also verified the outside fixture hash. Instantiating LocalStorage is unnecessary for this read-only reproduction.
- Impact: default local uploads leave the documented storage tree and may be omitted when that tree is backed up or moved. A local-to-Compose switch with the same DB is expected to make original content unavailable because the mount lacks the referenced object. **That mode-switch HTTP failure was inferred from the verified paths/configuration, not executed.** Existing original-byte/readback tests do not establish correct placement.
- Coverage gap: `tests/backend/conftest.py:50` and `tests/backend/test_migrations_storage.py:55` pass absolute temporary roots, bypassing the bad relative anchor. Their PASS results remain valid but miss this default configuration.
- Required correction: resolve relative storage against the repository root without machine-path hardcoding and retain explicit absolute-root behavior. First identify/preserve existing misplaced objects and provide a safe migration or compatibility procedure; changing the anchor alone must not break existing DB references. Do not blindly move/delete/overwrite outside-root data. Correct the environment evidence's storage-location claim.
- Revalidation: add a meaningful relative/default-root regression from more than one working directory and retain absolute override coverage; rerun affected Backend storage/upload tests and actual API integration. Verify actual configured adapter root, original IDs/bytes/hash and Unicode before/after the documented preservation procedure and ordinary restart. Verify local/Compose storage alignment or an explicit supported transition procedure. Resubmit READY_FOR_REVIEW with changed-file scope and sanitized evidence.

### ENV-P1-DB-001 — successful DB evidence retained; full closure withheld

- Classification: existing required **environment** completion issue, owner 03 / PM 01; not a duplicate MAJOR product finding. New mandatory product work is tracked solely as R08-WEB-002 above.
- DB authentication, configured readiness, migration head and same-path restart readback have successful Owner/Reviewer evidence in the dated reports. The original password failure is historical; its root cause remains unproven. The corrected verifier's original-ID/baseline handling is resolved.
- The preliminary `ENV-P1-DB-001-08.md` environment acceptance did not verify the actual resolved storage root. Its full-closure recommendation is superseded by the new path evidence, while its dated PASS observations remain valid.
- PM should keep full ENV closure pending R08-WEB-002 preservation/root verification, and update current wording so it does not still assert an unresolved authentication failure. After Backend correction, Reviewer checks actual root and existing-record readback/restart before final closure. No reset/reseed/credential change is requested.

### R08-WEB-001 — stale root execution/status guidance — RESOLVED

- Severity: MINOR, nonblocking documentation defect; **RESOLVED on 2026-09-12**. Task: REVIEW-WEB-001; owner PM 01 coordinating Backend 03 / Frontend 04. The following describes the original issue. Current corrected README and `REVIEW-WEB-001-docs-08.md` were inspected: implemented Phase 1 scope, current migrations/test scripts, owner runbook links and historical Bootstrap boundaries are corrected. No further README edit by this final review.
- File: `README.md:3`, `README.md:87`, `README.md:110`, `README.md:112`, `README.md:179`, `README.md:184`.
- Original problem/evidence: root README called the app Bootstrap-only, said CRUD/upload and frontend tests did not exist, and described only the empty baseline and three Backend tests. Current migration, package scripts, implementation and independent results contradicted those present-tense statements. These descriptions have now been corrected; original line references above identify the reviewed old version.
- Confirmation: compare root README's opening/Migration/Tests/Planned sections with `backend/README.md`, `frontend/README.md`, `frontend/package.json`, the domain migration and Reviewer results above.
- Recommended correction: label dated Bootstrap evidence as historical, update current scope/test/migration descriptions and link owner runbooks. Preserve the distinction between passing isolated tests and pending default deployment acceptance. No optional refactor or architecture redesign required.
- Recheck: documentation review against actual scripts/runbooks; this MINOR issue alone does not block acceptance or require a new full test run.

## Not executed / not certified

- A new complete independent default browser creation/upload flow was not executed; Owner's original default upload is attributed above. Independent default filter/detail/image/Expected Strings and post-restart API readback did execute and PASS. Correct-root preservation and local/Compose transition after the requested fix are NOT_RUN because no fix has been submitted.
- Default user-DB additive migration was not run by Reviewer; destructive downgrade/reset intentionally not part of user-environment verification. Fresh migration roundtrip was tested only in disposable DBs.
- Linux/container backend suite, clean dependency reinstall and Docker frontend image build: owner evidence where supplied, not independently rerun; Windows/backend regression and local frontend build were directly executed.
- Mobile/exhaustive accessibility, load/performance, power-loss hardware guarantees and Phases 2–7: not executed; not invented Phase 1 blockers.
- No product-code fix, architecture edit, owner report overwrite, credential change, Commit or Push by Reviewer. Only own review evidence/report/handoff and the review index are edited.
