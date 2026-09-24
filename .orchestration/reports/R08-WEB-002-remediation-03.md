# R08-WEB-002 remediation submission / Backend 03

Date: 2026-09-12 KST. Owner disposition: READY_FOR_REVIEW requested. PM handoff REVIEW-WEB-001-rework-01.md governs; no finding/ENV/Phase acceptance is declared here. Branch/commit null/null.

## Change and regression

`backend/app/storage/local.py` now anchors relative paths at `parents[3]` (repository), rather than `parents[4]` (repository parent). Explicit absolute paths retain their behavior. `tests/backend/test_storage_root.py` exercises repository and outside cwd, actual module-root identity, default relative path and explicit absolute override. No API/schema/dependency changes.

New executed results, separate from historical 54/23/2 evidence:

| Command | Result |
| --- | --- |
| `.venv/Scripts/python.exe backend/tools/run_postgres_tests.py -q --tb=short --junitxml=.orchestration/reports/R08-WEB-002-backend.xml` | 55 PASS, two existing deprecation warnings, exit 0; isolated PostgreSQL cleaned up. This was before expanding the new one-case regression to two cwd cases. |
| `.venv/Scripts/python.exe -B -m pytest tests/backend/test_storage_root.py -q -p no:cacheprovider --basetemp=.pytest_cache/storage-root-final --junitxml=.orchestration/reports/R08-WEB-002-cwd.xml` | Final parametrized regression: 2 PASS, same warnings, exit 0. |
| `.venv/Scripts/python.exe tests/frontend/run_integration.py --isolated-postgres` | Actual TypeScript client/API/migration/upload integration: 2 PASS, exit 0; disposable DB removed. |

## Original preservation and actual path

Prior read-only inventory of `C:\Dev\storage\local` found exactly one file: `objects/41ee9635-80f5-4dfd-8c7f-25c4be181f47/383d49f8-1783-4910-a567-dcd15992c253.png`, 243 bytes. Matched its SHA-256 to retained manifest `ebfa933afb0bfbe51ae0e2eb059cb58b4dfd22b6fcb67048450257b78b194135`. Copied only this exact file to the same relative key under `C:\Dev\qa-visual-automation\storage\local`, no overwrite, no deletion or move, original retained. No DB row/key/ID changes or baseline reseed.

Initial sandbox copy failed on destination permissions; its trailing success text was not accepted as evidence. Retried with approved execution and terminating errors; source and destination hash checks succeeded. No unrelated outside-root data touched.

Instantiated the **actual LocalStorage adapter** with effective Settings and asserted root equals repository/storage/local. Printed `C:\Dev\qa-visual-automation\storage\local`. Queried all configured DB screenshot storage_key/file_hash rows read-only: one pre-upload row, every referenced object present at corrected root with matching SHA-256. This replaces earlier insufficient Settings-only path inference.

Existing qa-visual-automation-postgres-1 and named volume qa-visual-automation_postgres_data retained. Configured probe authenticated [1, qa_visual, qa_visual] at 127.0.0.1:5433, revision 0002_phase1_domain; app/Compose/container/dotenv password comparisons true, no relevant process overrides. No secrets printed or credentials changed.

## Configured Web upload and restarts

Started normal API/Web without DB/storage overrides. Corrected-path original verifier PASS before/after DB+API restart (API PID 9276 -> 3228): original screenshot ID, associations, filtered list/detail/content, original hash, exact `한국어 日本語 中文 العربية 😀 é` (last U+0065 U+0301) at both Expected endpoints, CORS/readiness.

Added uniquely labeled Build `storage-root-fix-20260912` (661e4f6c-b9e2-41c4-a878-edf54d290395) in the retained project to keep original verification filters unchanged. In the actual Web Upload form selected this Build and existing Locale/Category/Situation, selected synthetic PNG with browser chooser and clicked Upload. Detail displayed new screenshot `b55d0ba3-90d7-4e9b-b1d7-b30f5d50f77d`, manual source, 128 x 72, 243 bytes, correct context and empty Expected Strings for this new Build. This new Build intentionally has no string mapping; exact Unicode is verified against the preserved original Build.

New object exists under corrected repository root, SHA-256 matches the fixture; corresponding wrong legacy path is absent. Thus this is new publication evidence, not only a copied-object readback.

Restarted same DB and normal API again (PID 3228 -> 17796). Original verifier PASS again. Direct configured DB inventory now contains two referenced objects; both exist at actual adapter root and match DB hashes. New screenshot detail/content returned success and matching Build/hash. Web HTTP 200; browser filtered list after reload showed exactly the new Build's one screenshot with context, 128 x 72 and manual source. No duplicate original-baseline upload or baseline-manifest edit.

## Local/Compose alignment and limitations

Source-reviewed Compose backend uses absolute `/app/storage/local`, bound from `./storage/local`; corrected host default is the repository's same `storage/local`. This establishes configuration/path alignment and preserved transition inputs. Full Docker backend/Frontend image deployment was **not executed** in this correction; do not describe source-inspected mapping as a live container transition. Existing DB container was executed throughout. The historical evidence is preserved and qualified; successful old same-path readback did not prove correct old placement.

Original wrong-path file remains as a preserved copy; no automatic cleanup/migration of other installations is introduced. Other installations affected by the old default should stop writers, inventory DB-referenced keys, verify source hashes, copy without overwriting to intended root, validate all references, and only then restart on corrected configuration. No destructive cleanup is part of this submission.

Independent code/initial test review: R08-WEB-002-review-08.md. Final closure and AC07 recommendation requested from designated Reviewer 08 after this owner runtime evidence; PM owns READY_FOR_REVIEW and final state reconciliation. No commit/push or later-phase work.
