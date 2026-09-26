# BACKEND-OCR-001 / Backend 03 API regression slice

- Task / owner: `BACKEND-OCR-001` / Backend Engineer 03
- Slice: lowest difficulty, HTTP/API regression coverage only
- Date: 2026-09-25
- Requested routing: `gpt-5.6-luna` / high for this low-difficulty slice; actual model telemetry is unverified.

## Scope and ownership

This submission adds only `tests/backend/test_ocr_api.py`. Product files, migrations, schemas, services, worker files, `pyproject.toml`, Phase 2 files, and PM-owned orchestration state were not edited by this slice.

The tests cover the accepted P3-OCR-v1 revision 1 API boundary:

- deterministic profile listing and safe profile projections;
- first `POST` creation, same-ID replay, fingerprint conflict, required headers, and closed request validation;
- immutable expected snapshot values after current catalog text changes, including `present` empty text versus `missing` translation;
- run history `selection=all|succeeded`, created-time/UUID ordering, offset pagination, and unknown query rejection;
- scoped 404 behavior for foreign project/screenshot/run identities;
- `RESULT_NOT_READY` 409 responses for OCR and verification resources before completion;
- expected/result page bounds and unknown query validation;
- unchanged Phase 2 screenshot detail/content/current expected-string behavior and original bytes.

The tests use the existing `client` and `catalog` fixtures from `tests/backend/conftest.py`, create a small PNG through the existing multipart screenshot API, and create catalog data through the existing public catalog endpoints. No direct database writes, profile registry writes, runner calls, or engine calls are used.

## Contract assumptions reported to the implementation owner

1. The isolated test registry exposes at least one `AVAILABLE` profile through `GET /api/v1/projects/{project_id}/ocr-profiles`. The test selects the lexicographically first available profile and does not assume a production model is installed.
2. A newly-created run remains observable as `PENDING`/nonterminal during these API tests because no background OCR runner is started by the `TestClient` fixture. If the application starts a runner automatically, the result-not-ready test needs a documented test seam that keeps this run pending.
3. The fixture profile can process the catalog locale used by the shared fixture (`ja-JP`), or the API test environment must provide a profile whose declared availability and locale support make the create request valid.
4. The accepted contract's expected snapshot endpoint is `/verification-runs/{run_id}/expected`; the existing live catalog endpoint remains `/screenshots/{screenshot_id}/expected-strings`.
5. `GET .../verification-runs?selection=succeeded` returns an empty page for newly-created, not-yet-completed runs. Completed-result positive tests belong to the qualified engine/runner integration slice.
6. `Access-Control-Expose-Headers` is emitted when the request includes the configured loopback Origin. The test checks `Location`, `Retry-After`, `Idempotency-Replayed`, and `X-Request-ID` on the first creation response.

## Static validation and execution record

Commands run from `C:\Dev\qa-visual-automation`:

- `Get-Content`/`rg` inspection of `AGENTS.md`, `docs/prompts/03_backend.md`, `PHASE-3-implementation-01.md`, the accepted `docs/architecture/phase-3-ocr-contract.md`, existing backend fixtures/tests, and the active OCR router/schema surface: PASS.
- `Get-ChildItem`/`git status --short`: PASS; existing dirty worktree changes were preserved.
- `& .\\.venv\\Scripts\\python.exe -m py_compile tests/backend/test_ocr_api.py`: NOT_RUN — the repository venv `python.exe` is a Windows launcher targeting an unavailable user Python path in this environment.
- `& .\\.venv\\Scripts\\pytest.exe --collect-only -q tests/backend/test_ocr_api.py`: NOT_RUN — the same launcher failure occurs before pytest starts.
- Final source inspection of the edited file: PASS by direct review; no Python parser could be launched in this environment.

No PostgreSQL migration, API runtime, OCR engine, worker, or full pytest execution was completed in this slice. The new tests are therefore not represented as product acceptance evidence and do not change AC-P3-01..04, which remain PM-owned.

## Review request

Please review the test assumptions above together with the accepted contract. In particular, confirm the disposable profile registration and the deterministic pending-run seam before treating the `RESULT_NOT_READY` assertions as executable in the integrated environment. The implementation owner should resolve any failures caused by absent 0004 schema/service/runtime support; this slice does not change product code to make tests pass.

- Branch / commit: `null` / `null`
- Product acceptance: not claimed
- Phase 2 behavior: regression assertions included; existing Phase 2 implementation and evidence preserved
