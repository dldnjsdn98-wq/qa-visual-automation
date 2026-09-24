# R08-WEB-002 / ENV-P1-DB-001 designated independent closure

Date: 2026-09-13 KST. Reviewer 08. Activation: `handoffs/R08-WEB-002-rereview-01.md` and PM confirmation. Root: current repository. Product/config/credentials changes by Reviewer: none. Branch/commit: null/null.

## Final disposition

**ACCEPTED. R08-WEB-002 RESOLVED; ENV-P1-DB-001 full closure ACCEPTED; AC-WEB-07 PASS recommended. REVIEW-WEB-001 REVIEW: ACCEPTED.** No unresolved CRITICAL/MAJOR remains from this review. R08-WEB-001 stays RESOLVED. Other twelve Web AC recommendations remain PASS from the prior review; no unrelated work was reopened. PM owns final Task/AC/Phase YAML reconciliation and subsequent phase scheduling.

This is the designated final affected-scope review of Backend's revised submission, superseding the prior CHANGES_REQUESTED/conditional closure conclusions. Their failures, discoveries, partial successes and source attribution remain historical evidence.

## Submitted change examined

Inputs: `R08-WEB-002-remediation-03.md` report/handoff; earlier conditional `R08-WEB-002-review-08.md`; final `local.py`, `test_storage_root.py`, Owner XML outputs and PM activation.

LocalStorage uses `parents[3]`, anchoring relative roots to the repository while retaining explicit absolute overrides. No API/schema/dependency change. Final regression tests cover repository and outside working directories and absolute roots; suppressing mkdir keeps those assertions focused on resolution. The earlier 55-test suite ran before the final two-case parametrization; final two-case results are separately attributed below. No claim of a 55-test run containing both final cases is made.

## Independently executed by designated Reviewer

| Command/check | Result and scope |
| --- | --- |
| `.\.venv\Scripts\python.exe -B -m pytest tests/backend/test_storage_root.py -q -p no:cacheprovider --basetemp=.pytest_cache/reviewer-root-recheck --junitxml=.orchestration/reports/R08-WEB-002-recheck-08.xml` | 2 PASS, 2 existing deprecation warnings. Both final cwd cases and absolute-root behavior. |
| `.\.venv\Scripts\python.exe -B backend/tools/check_default_environment.py` | PASS during initial re-review: configured authenticated `[1,qa_visual,qa_visual]`, existing DB volume, head `0002_phase1_domain`, no relevant process overrides; password comparisons only, no secret values. |
| `.\.venv\Scripts\python.exe -B backend/tools/verify_default_persistence.py verify` | PASS during initial re-review: original identity/context/hash, exact Unicode, both Expected Strings endpoints, readiness and CORS. |
| `.\.venv\Scripts\python.exe -B .orchestration/reports/check_r08_web002_closure.py` against a freshly started normal API using configured DB/storage | PASS at 2026-09-13 07:32:33 UTC. Actual adapter root, all DB-reference hashes, original preservation, new-root-only publication and original/new API readback. Structured output: `R08-WEB-002-recheck-08.json`. |

The final probe asserts the **actual instantiated LocalStorage.root**, not only Settings text. Effective default equals `storage/local`; resolved root equals `C:\Dev\qa-visual-automation\storage\local`. It reads all configured screenshot rows in a read-only transaction: **2 references**, both physically present via the adapter and matching DB size/hash. It checks original/new API detail identities and every Project/Build/Locale/Category/Situation association, original bytes, dimensions 128x72, 243 bytes and manual source.

- Original screenshot: `383d49f8-1783-4910-a567-dcd15992c253`. Preserved old-location copy still has the expected hash; corrected-location object and API content match.
- New Web-upload screenshot: `b55d0ba3-90d7-4e9b-b1d7-b30f5d50f77d`, Build `661e4f6c-b9e2-41c4-a878-edf54d290395`. Object is present at corrected root and absent at the legacy root. New Build has an empty Expected Strings mapping by design.
- Both images SHA-256: `ebfa933afb0bfbe51ae0e2eb059cb58b4dfd22b6fcb67048450257b78b194135`.
- Original text exactly `한국어 日本語 中文 العربية 😀 é`, final sequence U+0065 U+0301; no missing translation. No baseline re-seed or rewrite. Baseline hash before/after: `0ab5f214eac550f4da5924a550d49f3c9cf3b16aebc9b0ba02c421cf5ef8ad5b`.

On the resumed day, Docker was stopped, causing a ConnectionTimeout before verification. Reviewer started Docker Desktop and the existing PostgreSQL container with its existing volume. A temporary Reviewer-owned normal uvicorn API ran on the free loopback port 8001 without DB/storage dependency overrides; bounded HTTP readiness polling preceded the probe. Its exact owned process tree was stopped afterwards; PostgreSQL/Desktop remain running. No other owner's process was stopped and no database, volume or credential was reset. A first probe revision incorrectly wrote `current_user()` rather than SQL `current_user`; that Reviewer-tool syntax error was corrected and is not a product defect or PASS. The final exit-0 result alone is the complete probe PASS.

## Owner evidence retained and corroborated

Owner supplied 55 Backend tests PASS, final cwd 2 PASS and real ApiClient integration 2 PASS after correction. Reviewer inspected the suite metadata and final test source; only the focused two cases were rerun in this designated closure. Prior independent 54/23/2 and build/typecheck remain dated pre-correction evidence, not substituted for the new checks.

Owner's exact-copy preservation retained the old source, changed no DB keys/IDs, did not overwrite destination data, and reported the actual configured adapter root and all references. Owner performed the new browser chooser/form upload, then ordinary same-DB/API restarts and original/new readback. These actions remain **Owner executions**. The designated Reviewer independently confirmed their resulting original/new objects, unchanged baseline, corrected physical root and live API behavior after starting the same existing DB and a fresh normal API. This combination satisfies the requested preservation/publication/restart evidence without relabeling Owner browser/restart actions as Reviewer actions.

A Sol high independent evidence audit found no remaining mandatory gap after the primary runtime checks above. Primary Reviewer owns the final acceptance.

## Limits and closure rationale

Compose explicitly uses `/app/storage/local` bound from repository `./storage/local`; the corrected host default resolves to that same host tree. This is source-inspected mapping alignment. **A live Docker Backend/Frontend container transition was NOT_RUN** and is not claimed. The PM re-review accepted source-mapping evidence with this attribution; no new mandatory container transition gate is invented.

No new full independent browser creation/upload flow, Linux suite, Frontend rebuild or unrelated phase tests were run in this closure: API/schema/UI/dependencies did not change, Owner supplied affected integration evidence, and independent focused resolution plus actual configured publication/readback addresses the defect. Other installations must follow the documented stop-writers/inventory/hash/copy-without-overwrite/validate procedure; this review certifies this repository's original/new references, not an unexecuted automatic migration elsewhere. The old copy is intentionally retained, not a cleanup defect.

The original failure mechanism is corrected, old references remain readable, new writes target the correct root, and the same configured data survives restarts with exact identity/hash/text. Required R08-WEB-002 and ENV conditions are satisfied. PM should close both issues, change AC07 to PASS, reconcile Web review/implementation completion and apply the Phase 1 gate using all thirteen PASS criteria and this ACCEPTED result. No Commit/Push or later-phase task is activated by Reviewer.
