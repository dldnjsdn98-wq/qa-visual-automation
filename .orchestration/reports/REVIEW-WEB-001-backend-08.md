# REVIEW-WEB-001 — Independent Backend closure review / 08

Date: 2026-09-12 KST. Repository: `C:\Dev\qa-visual-automation`. Scope: Phase 1 Backend integrity, concurrency, storage, Unicode and acceptance evidence. Branch/commit created: null/null. Only this report is written; no state, product, prior evidence, database or storage edits.

## Disposition

**CHANGES_REQUESTED — R08-WEB-002 remains OPEN, MAJOR.** The current local adapter resolves default relative storage outside the repository. This review independently confirms the existing finding rather than assigning a duplicate issue. Findings within this scope: CRITICAL 0; unresolved MAJOR 1. No additional major integrity, concurrency or Unicode defect was established by the inspected implementation and retained evidence. This is not Backend or whole-Phase acceptance.

Preserve the independent **54 Backend / 23 Frontend / 2 integration / typecheck and build PASS** in [REVIEW-WEB-001-08.md](REVIEW-WEB-001-08.md). Preserve [ENV-P1-DB-001-08.md](ENV-P1-DB-001-08.md)'s ACCEPTED environment disposition and successful authentication/readiness/readback evidence as attributed historical results. That report is dated September 9; the main review explicitly records the later September 11 storage discovery and qualifies its storage-placement conclusion. Successful same-path retention does not establish correct placement or host/Compose equivalence. No renewed authentication failure is alleged.

Current PM state and the earlier [evidence audit](REVIEW-WEB-001-evidence-08.md) treat ENV as closed. Neither supersedes the reproducible product defect below. PM must consolidate the evidence without erasing successful checks or interpreting empty state blockers as proof that R08-WEB-002 is resolved. State reconciliation remains outside this report's write scope.

## Evidence identity and attribution

Read the reviewer role, activation handoff, state/decisions/acceptance, Phase 1 requirements, approved storage/API/domain contracts, Backend owner report, main independent review, ENV review, and relevant implementation/test sources. Architecture revision 2 acceptance is not reopened.

- Recomputed SHA-256 for all 90 paths in [the source manifest](REVIEW-WEB-001-08-source-manifest.json): **89 match; only `backend/tools/verify_default_persistence.py` differs**. Enumerating `backend/app`, `backend/migrations`, `backend/tools` and `tests/backend` with `rg --files` found no additional visible files outside that manifest. This inventory is limited to those directories and normal ignore rules.
- Inspected the changed helper: verify mode requires saved/list/detail screenshot identity and does not write the manifest; baseline mode is separate and refuses an existing screenshot ID. The resolved verifier finding is not reopened. Its readback still does not assert the physical storage root or perform a restart.
- Parsed [retained independent Windows JUnit](reviewer-backend-windows.xml): **54 tests, 0 failures, 0 errors, 0 skipped**, timestamp `2026-09-08T21:21:54.883460+09:00`. These are prior Reviewer executions, not new tests in this continuation. The 90-file snapshot was taken later than that run and cannot retroactively prove its exact execution bytes.
- Frontend 23 tests, typecheck/build and two real TypeScript-client/FastAPI/PostgreSQL integration tests remain prior independent narrative evidence. Backend owner Windows/Linux tests and clean-install checks remain owner evidence. No redundant suite or build was run.
- ENV independent verification of authenticated DB identity, current head, readiness, image hash, associations and multilingual Expected Strings remains prior independent evidence. Migration application, normal creation/upload flow and controlled DB/API restart remain **Owner 03 executions**. The interrupted independent browser creation/upload flow is not relabeled PASS.

## R08-WEB-002 — incorrect default storage root

Owner: 03 Backend; PM 01 coordinates preservation and final reconciliation. Severity: **MAJOR product defect**, blocking Backend closure and storage-dependent configured upload acceptance.

References: `backend/app/storage/local.py:11,18`; `backend/app/config.py:14`; `backend/README.md:24`; `.env.example:6`; `docker-compose.yml:27,31`; `docs/architecture/data-flow.md:29`.

The contract and runbook require `STORAGE_ROOT=storage/local` relative to the project root. `LocalStorage` instead sets `ROOT = Path(__file__).resolve().parents[4]` and joins the supplied path to it. For this source location, parent index 3 is `C:\Dev\qa-visual-automation`; index 4 is `C:\Dev`. Thus a default host upload writes under `C:\Dev\storage\local`, outside the documented repository storage directory. An absolute storage override bypasses this erroneous prefix. Compose explicitly uses `/app/storage/local` bound to `./storage/local`, so host defaults and Compose address different physical stores. Switching to Compose or correcting the prefix alone can leave existing DB references without readable content (503); repository-storage backup can omit the originals. No actual deletion or completed switch was observed or performed.

### Targeted read-only confirmation in this continuation

Used PowerShell `Resolve-Path` and `System.IO.Directory.GetParent` to enumerate parent indices 0–4 from the source path; used `Test-Path -LiteralPath` and `Get-FileHash -Algorithm SHA256` for only the exact synthetic object identified by the retained records manifest. Did not instantiate `LocalStorage` (its constructor creates directories), import the application, query the DB, or run a maintenance/verifier command.

Object key: `objects/41ee9635-80f5-4dfd-8c7f-25c4be181f47/383d49f8-1783-4910-a567-dcd15992c253.png`.

| Check | Newly observed result |
| --- | --- |
| Exact object under `C:\Dev\storage\local` | PRESENT; SHA-256 `ebfa933afb0bfbe51ae0e2eb059cb58b4dfd22b6fcb67048450257b78b194135`, matching the saved fixture hash |
| Same object under `C:\Dev\qa-visual-automation\storage\local` | ABSENT |
| `ENV-P1-DB-001-records.json` hash | `0ab5f214eac550f4da5924a550d49f3c9cf3b16aebc9b0ba02c421cf5ef8ad5b`, matching prior ENV evidence |
| Current `backend/app/storage/local.py` hash | `e8ab863b195914321fb34b47500914ef993af3d15cf49083aaf7553e4bc92a69`, unchanged from source manifest |

This proves the present source-path error and exact fixture placement, not the current running API configuration or a fresh restart. Prior suite success is consistent: `tests/backend/conftest.py:50`, `test_migrations_storage.py:55` and `tests/frontend/run_integration.py:55` supply absolute temporary storage roots, masking relative-root behavior.

### Required correction and closure evidence

Correct repository-relative resolution while retaining absolute-path support. Add a focused regression for default/relative roots, including invocation from a different working directory, and show consistency with the configured Compose mount. Coordinate preservation of existing objects before adopting the corrected root: retain original IDs, relative keys and hashes; do not replace the DB, reseed, overwrite a conflicting destination or delete the old store to obtain PASS. Submit a preservation account and corrected configured readback of the same original screenshot, metadata and Expected Strings across an ordinary restart using the same DB and intended storage. Independently verify the corrected physical path as well as API content/hash. Run affected storage checks; unchanged CRUD/Frontend suites need not be repeated solely for this fix. None of these corrective actions was performed by this reviewer.

## Critical implementation assessment

| Area | Inspection and retained evidence | Assessment / exact boundary |
| --- | --- | --- |
| Scoped integrity and deletion | Catalog/strings/screenshot models, migration `0002_phase1_domain`, repositories and services use project-scoped lookups, composite RESTRICT FKs and scoped unique constraints. Screenshot's triple FK enforces Category/Situation membership. Retained CRUD, relationship and direct cross-project SQL rejection tests pass. | No additional major defect found. Runtime reference checks are backed by DB constraints if a concurrent deletion occurs. Direct SQL tests sample constraints; they are not every possible FK race. |
| Transactions and concurrency | Write services choose READ COMMITTED before reads; expected replacement locks Build, validates all keys, deletes/inserts in one transaction and commits through the service. Read engine uses REPEATABLE READ; page/count and expected resolution share consistent reads. Retained duplicate-build test returns 201/409; competing replacement test returns complete lists with an unmixed final list. | No additional major defect found. Tests exercise two competing writers, not exhaustive schedules, sustained load or optimistic lost-update prevention. The contract does not require general PATCH version checks. |
| String identity and expectations | Immutable StringKey identity; unique project/build/key/locale entries; ordered mapping uniqueness; one shared resolver LEFT JOINs by Build/Locale and reports current catalog. Retained invalid replacement preserves old mapping; empty text remains present while missing text is null. | Backend behavior supported. No upload-time catalog snapshot is claimed or required in Phase 1. |
| Unicode and closed boundaries | Strict UTF-8/JSON, recursive NUL/residual-surrogate validation including object keys; original multipart disposition validated before library/path sanitization; schema scalar limits and PostgreSQL UTF8/char_length bound; rejected values excluded from error payloads. Retained API tests cover CJK, combining marks, CRLF/tab, supplementary emoji at 10,000 scalars, empty text, literal escape strings and rejected create/PATCH/nested metadata/filename cases. | No additional major defect found. Existing StringEntry values stay unchanged after invalid PATCH; invalid metadata never publishes. This is not exhaustive Unicode fuzzing. Locale identifiers are intentionally canonicalized; translation text is preserved. |
| Upload and compensation | Request/part/file limits, PNG/JPEG signature and full decode/dimension checks, original-byte hash, fsynced staging and atomic no-overwrite hard-link publication. References revalidated before insert; known precommit/constraint failure compensates; ambiguous commit retains object and attempts fresh-session lookup. Retained fault tests cover publication failure, rollback and actually-committed/not-committed ambiguous outcomes. | Protocol supported apart from R08-WEB-002. Publication failures can retain orphans for maintenance. No general retry/idempotency guarantee is claimed in Phase 1. |
| Content and reconciliation | Scoped DB lookup before file read; absent/unreadable referenced content returns 503. Reconciliation requires declared stopped writers, primary DB, full inventories, 24-hour age and a fresh reference check before exact-key deletion; reports missing/hash-mismatched objects. Retained no-overwrite/traversal, dry-run/apply and DB-failure/no-deletion tests pass. | Operator must actually stop/drain writers; flag is an assertion, not an enforced distributed lock. Content reads check length, not SHA-256 on each GET; reconciliation performs hash validation. Windows lacks portable directory fsync; malicious concurrent local filesystem changes and host power-loss guarantees are outside the established evidence. |
| Migrations | Additive domain migration matches scoped model constraints/indexes. Retained fresh PostgreSQL migration, downgrade to baseline/re-upgrade and metadata parity tests pass; configured head was independently observed in ENV. | Fresh-schema criterion supported. No default DB migration/downgrade or new parity run performed here. |

## AC coverage recommendation for parent consolidation

These recommendations describe Backend contribution; they do not edit acceptance state or certify whole browser criteria.

| AC | Evidence and recommendation |
| --- | --- |
| AC-WEB-01 Project CRUD | Supported by retained `test_project_crud`, restrictive relationships and actual-client integration; no new Backend blocker. |
| AC-WEB-02 Build CRUD | Supported by scoped CRUD, immutable label, restrictive deletion and concurrent duplicate 201/409; no new Backend blocker. |
| AC-WEB-03 Locale management | Supported by scoped CRUD, locale validation/canonical uniqueness and Unicode names. |
| AC-WEB-04 Category management | Supported by scoped CRUD, cross-project validation and restrictive relationships. |
| AC-WEB-05 Situation management | Supported by scoped CRUD, category association and database composite FK enforcement. |
| AC-WEB-06 Multilingual String IDs | Supported by real PostgreSQL exact-text/empty/missing/create/PATCH/uniqueness evidence and current implementation. |
| AC-WEB-07 Manual upload | Isolated API/client behavior PASS retained; **configured storage closure BLOCKED by R08-WEB-002**. |
| AC-WEB-08 Screenshot metadata | Response/scoping/hash/dimensions evidence supported; final durable original-content acceptance remains conditional on R08-WEB-002 correction and preservation. |
| AC-WEB-09 Expected Strings display | Backend ordered/current/empty/missing semantics and prior configured text readback supported. UI acceptance belongs to the Frontend/parent review; storage-root correction must preserve the same screenshot's associations/readback. |
| AC-WEB-10 Filters | Retained AND, scope, time interval and pagination tests plus real client/ENV readback support Backend behavior. ENV's one fixture is not an exhaustive matrix. |
| AC-WEB-11 Fresh migrations | PASS recommendation for the literal fresh-schema criterion from retained independent PostgreSQL roundtrip/parity evidence. Storage defect does not invalidate schema reproduction. |
| AC-WEB-12 Backend tests PASS | PASS recommendation for the literal test criterion: retained independent 54/54 Windows real PostgreSQL result. This is not defect-free certification. |
| AC-WEB-13 Frontend build/behavior | Prior independent 23 tests, typecheck/build and 2 integration PASS preserved; no new Frontend execution or whole-UI acceptance by this Backend review. |

## Work limits and handback

New work consisted of source/evidence inspection, manifest comparison, JUnit parsing and exact-path/hash reads. No pytest/npm/build, application import, live DB/API/browser probe, migration, service restart, seed/baseline, storage reconciliation or filesystem mutation outside this report was executed. An initial combined PowerShell read command failed to parse a brace-style path expression; corrected reads succeeded. That tooling error is neither product failure nor test evidence.

This is a bounded independent closure review, not proof that no possible defect exists. Linux/container/clean-install executions remain attributed to their original owners; sustained concurrency, fuzzing, abrupt power loss and exhaustive security/UI/accessibility verification are not newly certified. Later phases are excluded. Documentation issue R08-WEB-001 remains outside this Backend closure assignment; no disposition on another reviewer's documentation work is inferred.

Hand back R08-WEB-002 to Backend 03 for correction/preservation evidence, then Reviewer 08 for targeted closure and PM 01 for consolidation. Do not accept Backend/Phase 1 merely because ENV is marked ACCEPTED or prior suites passed. No commit or push.
