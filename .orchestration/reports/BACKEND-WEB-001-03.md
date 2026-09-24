# Backend implementation evidence — 2026-09-07

Task BACKEND-WEB-001 / owner 03. Approved ARCH-001 revision 2 is unchanged. This is implementation evidence for independent review, not phase acceptance.

## Executed checks

| Command / check | Actual result |
| --- | --- |
| Project .venv Python | Python 3.12.10 in current repository; project environment used |
| .\.venv\Scripts\python.exe backend/tools/run_postgres_tests.py -q --tb=short --junitxml=.orchestration/reports/backend-windows.xml | PASS: 54 tests, 0 failures/errors/skips; 2 upstream deprecation warnings; 4.66s pytest duration |
| docker build -f backend/Dockerfile.test -t qa-backend-test-runtime:local . | PASS: Linux Python 3.12, hash-verified dependency install, package build and pip check |
| .\.venv\Scripts\python.exe backend/tools/run_postgres_tests.py --linux -q --tb=short | PASS: 54 tests, 0 failures/errors/skips; 2 upstream deprecation warnings; final 3.40s pytest duration |
| .\.venv\Scripts\python.exe backend/tools/check_clean_install.py | PASS: newly created Windows venv, --require-hashes lock install, --no-deps --no-build-isolation package install, pip check and application import/OpenAPI |
| .\.venv\Scripts\python.exe tests/frontend/run_integration.py --isolated-postgres | PASS: Frontend-owned actual client integration suite, 1 file / 2 tests against live Uvicorn and isolated PostgreSQL; fixture DB removed afterward |
| .\.venv\Scripts\python.exe backend/tools/export_openapi.py | PASS: 22 paths / 45 operations including health/readiness; four synthetic approved examples |
| .\.venv\Scripts\python.exe -m alembic upgrade head --sql | PASS: offline PostgreSQL DDL export in backend/schema.sql |
| .\.venv\Scripts\python.exe -m pip check | PASS: no broken requirements |
| Approved architecture SHA-256 comparison | PASS: all four fingerprints match Reviewer revision 2 report |
| Exported OpenAPI == app.openapi() | PASS |
| git diff --check -- backend tests/backend pyproject.toml alembic.ini | PASS: no whitespace errors; Git CRLF conversion advisories only |
| Original baseline comparison | PASS: no change to 0001_bootstrap versus checkpoint |
| Legacy cloud-sync absolute path search in source/config/architecture/orchestration | No matching legacy path found; no path replacements performed |

Machine-readable Windows evidence: [backend-windows.xml](backend-windows.xml). Linux output: [backend-linux.txt](backend-linux.txt).

## What the tests prove

- Project/Build/Locale/Category/Situation/StringKey/StringEntry CRUD; immutable identity, canonical locale uniqueness, description null versus omission, empty PATCH rejection and restrictive deletes.
- Real PostgreSQL Unicode readback: Japanese/Korean, supplementary emoji up to 10,000 scalars, combining marks, newlines/tabs, empty text and literal escape strings. NUL/residual surrogates/overlong text fail create and PATCH; rejected PATCH leaves stored value unchanged.
- Ordered Build/Situation expected mappings; missing versus empty translations; failed replacement is atomic. Concurrent duplicate Build yields 201/409; competing replacements serialize under the Build lock and do not produce mixed lists.
- Screenshot PNG/JPEG original bytes, filename sanitization after Unicode validation, metadata readback/hash/content headers/list/detail/current expectations, AND filters and half-open time range.
- Missing/out-of-scope references return 404; same-project category/situation mismatch returns 422; unsupported source/idempotency fields are rejected. Unknown/repeated queries and malformed transport/error envelopes are exercised.
- File/request size, malformed/truncated/unsupported images, bounded metadata and invalid nested Unicode/filename inputs fail before publication. Rejected metadata has no screenshot row and no remaining staged/published object.
- Unavailable publication, missing referenced content, known rollback compensation and ambiguous commit with both actually-committed/not-committed outcomes. Uncertain commit never deletes the original.
- Atomic no-overwrite local publication, traversal rejection, explicit stopped-writer reconciliation, 24-hour grace, dry-run/apply, missing references and DB-failure no-deletion.
- Fresh PostgreSQL schema built only by migrations; downgrade to unchanged baseline/re-upgrade; model metadata parity; direct SQL cross-project FK rejection. No SQLite substitution and no reset of user DB.

## Acceptance contribution

AC-WEB-01..10: Backend behavior evidenced by the API/storage tests above. AC-WEB-11: real PostgreSQL migration tests. AC-WEB-12: Windows/Linux Backend suites pass. AC-WEB-13: two actual Frontend-client integration tests pass; complete Frontend build/UI behavior/visual acceptance belongs to owner 04 and Reviewer.

ACCEPTANCE.yaml is not promoted by this owner report. PHASE 1 remains IN_PROGRESS and independent web review is still required.

## Failed attempts and resolution

Earlier attempts are not counted as PASS: Windows default pytest temporary-directory access error; stopped Docker/PostgreSQL connection timeout; configured localhost:5433 password authentication failure; duplicate Alembic path_separator option. Tests now use repository-owned temporary paths and isolated PostgreSQL containers. Alembic has one path_separator entry. The complete final suites above pass.

The default local deployment credential mismatch remains an environment issue. Existing DB passwords/volumes were not changed or deleted. The reproducible isolated runner avoids that dependency, and the Frontend integration suite also succeeds with an isolated server. Normal persistent local deployment needs the operator/PM to align the existing credential and .env before live use.

## Limits / NOT_RUN

- Full browser/UI visual acceptance, sustained/load testing and abrupt host power-loss tests: NOT_RUN by Backend. No claim about overall Frontend acceptance.
- Windows file fsync/no-overwrite publication is tested, but portable directory fsync is unavailable on Windows. POSIX directory fsync is implemented and Linux tests pass.
- The upload boundary is stream-counted and capped, then buffered (<=21 MiB request plus parser copies); isolated image decoding is a separate module executed off the async event loop, not a separate OS sandbox.
- Storage root must be operator-controlled and support hard links. No concurrent malicious local filesystem mutation guarantee is claimed.
- Root README is shared; Backend-specific reproducible commands/maintenance usage are supplied in backend/README.md for PM to link during shared documentation coordination.
- No S3 implementation, OCR, folder agent, ADB, automation, record/replay or state graph work.

## Git

Existing shared checkpoint: 811b1e36199d424d83930f3381c7d71e537bc7d6 on main, created by role 10. It contains earlier work in progress and is not the final reviewed implementation commit. Final Backend changes remain uncommitted; this task made no commit/push.
