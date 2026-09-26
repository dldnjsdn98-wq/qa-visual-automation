# BACKEND-OCR-001 / Backend Engineer 03 final owner report

- Date: 2026-09-25
- Status: **Backend owner implementation and schema integration evidence ready; Phase 3 review activation remains blocked on Worker05 runtime/model qualification and final live integration.**
- Activation: `.orchestration/handoffs/PHASE-3-implementation-01.md`
- Accepted contract archive: `docs/architecture/phase-3-ocr-contract-revision-1.md`
- Accepted contract SHA-256: `46940dd1dd7775422213b2ba422b63650f4e83740e034cf29dc83f23970acb82`
- Independent contract review SHA-256: `c9b723eca12e2f4df254e910c47fbf6104647301af9728c55d287760a5a268da`
- Unaccepted revision 2 candidate: `docs/architecture/phase-3-ocr-contract.md`, SHA-256 `478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44`; READY_FOR_REVIEW only.
- Branch / commit: `null` / `null`

## Implemented Backend scope

The Backend implementation now covers the accepted P3-OCR-v1 revision 1 server boundary:

- additive migration `0004_phase3_ocr_verification` with immutable snapshots/configuration, durable jobs and attempts, lease/fencing constraints, append-only result rows, lifecycle triggers, and PostgreSQL half-even six-place rounding;
- run creation, same-client replay, fingerprint conflict, immutable expected snapshots, deterministic history/pagination, scoped 404 behavior, nonterminal 409 behavior, and safe profile listing;
- durable claim, heartbeat, bounded retry, stale-fence rejection, ambiguous-commit recovery, terminal failure mapping, and a whole-attempt deadline that includes source I/O;
- bounded `send_bytes`/`recv_bytes` child IPC with one canonical JSON result transfer and explicit `ENGINE_OUTPUT_INVALID` handling;
- exact profile canonical-bytes/object binding, duplicate profile-ID rejection, requested-profile availability checks, and explicit projection from stored snapshot/configuration into the Worker verifier boundary;
- closed validation of source facts, runtime manifest, preprocessing/audit/timing structures, finite geometry, recognition confidence semantics, normalized text, item status/reason/counts, aggregate status, unmatched regions, and no-text behavior;
- integration with Worker05's registered v1 OCR/verification root validators, plus Backend enforcement of the closed runtime-manifest, raw-audit and timing projections against the frozen profile;
- versioned API schemas, response headers for first-create and replay responses, CORS exposure, and a generated `backend/openapi.json` that matches `app.openapi()` with 30 paths;
- RapidFuzz 3.14.6 hash lock coverage, package discovery for `worker*`, explicit wheel package-data for the seven Worker v1 schemas and fixture/registered profile JSON resources, and clean-install import checks for the Backend app, Worker verifier, and OCR callable/profile exports;
- Backend README and Phase 3 regression, migration, API, job, runner, result-validation, packaging, and Worker-boundary tests.

The historical low-difficulty API slice artifacts remain at:

- `.orchestration/reports/BACKEND-OCR-001-api-slice-03.md`
- `.orchestration/handoffs/BACKEND-OCR-001-api-slice-03.md`

## Independent difficulty routing

Requested routing and actual model telemetry are recorded separately. The task API accepted the requested model/effort, but this owner has no independent telemetry proving the model that executed each task; therefore actual model remains unverified.

| Difficulty | Requested route | Assigned work | Result |
| --- | --- | --- | --- |
| 최상 | Astra / medium | final durable fencing, canonical binding, result consistency, IPC, migration and OpenAPI residual audit | follow-up completed, but the task API returned an empty result body; no additional finding is claimed from that call |
| 상 | Sol / high | durable job/recovery test implementation | `tests/backend/test_ocr_jobs.py` added; integrated suite passes |
| 중 | Sol / medium | full Phase 3 Backend integration audit | initial P0/P1 findings corrected; post-fix follow-up completed without a new visible finding |
| 하 | Terra / high | packaging, lock, OpenAPI and stale regression audit | findings corrected; follow-up produced no new finding |
| 최하 | Luna / high | HTTP/API regression slice | historical slice preserved and now executes within the full passing suite |

## Verification evidence

All commands were run from `C:\Dev\qa-visual-automation` using the repaired isolated interpreter `.pytest_cache\agent-clean-win\Scripts\python.exe`.

1. Full Backend suite:

   `.pytest_cache\agent-clean-win\Scripts\python.exe -m pytest tests/backend -q --tb=short --basetemp=.pytest_cache\backend-full-raw-audit-final-20260925`

   **PASS — 167 passed, 1 existing Starlette/httpx deprecation warning, 10.87 seconds.** No failure or skip was reported.

   Default project suite after adding `tests/ocr` to `testpaths`:

   `.pytest_cache\agent-clean-win\Scripts\python.exe -m pytest -q --tb=short --basetemp=.pytest_cache\default-all-final-20260925`

   The latest run after private raw-audit text coverage used `.pytest_cache\default-all-raw-audit-final-20260925` and **PASS — 189 passed, 1 existing warning, 11.45 seconds.** This default run collects Backend, integration and OCR suites.

2. Python compilation of the Phase 3 models, repositories, services, worker, API schema/router and OpenAPI exporter:

   **PASS.**

3. Generated OpenAPI comparison:

   Loaded `backend/openapi.json`, generated `app.openapi()`, and compared the objects for exact equality.

   **PASS — `OPENAPI_EQUAL paths=30`.**

4. `git diff --check`:

   **PASS — no whitespace error.** Git printed only existing LF-to-CRLF conversion warnings.

5. Accepted artifact hashes:

   - accepted revision 1 archive: `46940dd1dd7775422213b2ba422b63650f4e83740e034cf29dc83f23970acb82` — MATCH
   - independent review: `c9b723eca12e2f4df254e910c47fbf6104647301af9728c55d287760a5a268da` — MATCH
   - unaccepted revision 2 candidate: `478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44` — MATCH, no acceptance inferred

6. Earlier focused evidence retained from this implementation cycle:

   - core migration/constraint/runner/result validation: 13 passed;
   - API and Worker boundary: 12 passed;
   - job/API/runner/result group: 22 passed;
   - migration roundtrip: 3 passed;
   - packaging contract after generated OpenAPI test: 7 passed;
   - hash-locked clean install, wheel build/install, `pip check`, and Backend/Worker import checks: PASS.
   - updated wheel build: PASS; archive inspection confirmed `worker/ocr/schemas/__init__.py` and all seven `v1/*.schema.json` resources are included.
   - post-correction wheel SHA-256: `32443355e085fb5dea62eb38d4a414190e9776e9766d2aa9c296c11e14b5da6a`; archive schema hashes exactly match the Worker source files.
   - Worker05 stdlib suite: **17 passed** in 0.039 seconds, covering geometry, nested schema closure, registry separation, normalization, rational threshold boundaries, pinned RapidFuzz behavior and deterministic sparse assignment comparisons.
   - Current Worker/Backend integration selection (`tests/ocr` plus packaging, runner and result-validation modules): **41 passed, 1 existing warning** in 0.47 seconds.
   - Updated schema loader/public validator SHA-256: `3e9a7da0bb73e75f96e4bb71e05c00cd44ef924344aca48482afd7cceb22b902`. It preserves Backend's imported root/version preflight behavior and separately exposes full nested Draft 2020-12 validation.
   - Windows resolver report `.pytest_cache/phase3-ocr-05/windows-resolver-report.json`: SHA-256 `dce46dc6dc9434a00a0137d8ea484e3e9f44a34ca02a21d82beb0f049a9cdb57` — MATCH.
   - Windows CPython 3.12 RapidFuzz 3.14.6 wheel: SHA-256 `cfca36e4612208875e08611a779164b6cb8900ab8bbd3d82d4cfdfae9efbfac9` — MATCH with the existing Backend lock entry. This verifies the Windows wheel only.
   - Explicit profile-resource wheel build: PASS; archive contains `worker/ocr/profiles/fixtures/fixture-contract-v1.profile.json` with SHA-256 `4d9e2246bc2b23a5b7047f30164e2ba53dfb0169ec420528672c1e3ca49767b1`.
   - `backend/tools/check_clean_install.py`: PASS in a new local Python 3.12 environment. Hash-locked dependencies installed, package wheel built/installed, `pip check` reported no broken requirements, and installed `load_fixture_profile_document('fixture-contract-v1')` returned digest `a00338303e25d2c4d85827432eea33a4a564fbecbf7816dc5f2645609a0f03cd` with `production_eligible=false`.
   - Post-raw-audit wheel: SHA-256 `5dd92e06decb8b1474540e27c1118438c66e3bdb1b2b9ba2060b1744e192a41c`; archive inspection confirmed both the updated OCR-output schema and fixture profile resources.

## Failure history and corrections

The following intermediate failures were resolved and are not represented as passing evidence:

1. Initial PostgreSQL runs inside the restricted sandbox timed out; approved real PostgreSQL runs succeeded.
2. Early migration tests exposed SQL binding, base temporary-directory, and test-assumption defects; these were corrected before the passing runs.
3. A combined run first reported 16 passed and 20 setup errors because the user Temp pytest directory was inaccessible.
4. The workspace `--basetemp` rerun reported 28 passed and 8 failed because session-scoped pending API jobs were visible to job tests.
5. Job tests were moved to a module-specific temporary PostgreSQL database, after which the combined and full suites passed.
6. OpenAPI export initially imported a stale installed wheel. `backend/tools/export_openapi.py` now places workspace code first and the schema was regenerated.
7. The first schema-package test invocation stopped before collection because an identical TOML package-data block was present twice during concurrent editing. The duplicate block was removed; targeted tests then passed 17/17 and the full suite passed 165/165.
8. The first schema hash-display command let PowerShell expand `$id` and raised `KeyError`. The corrected command constructed the key safely and verified all seven URNs and hashes.
9. The first profile-package test invocation stopped before collection because an identical TOML package-data line was present twice during concurrent editing. The duplicate was removed; targeted tests, default collection and clean installation then passed.

## Cross-owner blockers and acceptance limits

Worker05 public imports, the exact `ProfileDocument` boundary, seven Draft 2020-12 schema files under `worker/ocr/schemas/v1`, and 11 source-level Worker tests are now present. Their reported/public file hashes were checked, and the Backend consumes the registered OCR/verification root validators.

The three schema integration findings are resolved:

- canonical and OCR adapter bbox coordinates now use positive/nonnegative JSON numbers and preserve the contract's continuous coordinate domain;
- preprocessing now requires a lowercase SHA-256 `pixel_sha256`, while Backend enforces equality with the top-level pixel digest;
- runtime packages now require `{name,version,sha256}`, while Backend enforces equality with the frozen profile packages.
- private `raw_audit.regions[]` now requires `raw_text`; Backend validates persistable Unicode through the bundle guard, enforces the 10,000-scalar limit, retains nonempty engine text/polygons/confidences, and leaves the public region text contract unchanged.

Corrected schema hashes are:

- `canonical-regions.schema.json`: `d8c7465376717a1f9ce109bb81b48465e76007d1154f300f18dda6e357cbc9db`;
- `ocr-adapter-output.schema.json`: `9d0cdbba200efe3a148583ffc6bfd6fed7737d46153f678952ab8a0b34e4d9b4` after adding private audit `raw_text`;
- schema loader/public validator: `3e9a7da0bb73e75f96e4bb71e05c00cd44ef924344aca48482afd7cceb22b902`.

Worker05 aggregate `4a8d332a2c88daad7643761ab89dfd2db06e080598f6d4949b83f67c6e8c6598` preceded the raw-audit text change and is superseded. The updated aggregate is pending from Owner05 and is not inferred here.

Worker05 additionally reported a contract-maximum assignment run with 1,000 expected items, 1,000 regions and 65,536 real edges: 1,000 assignments in 66.4358 seconds, deterministic result SHA-256 `88264c60782cdc2dd25be95d3fc1a891f5801214d1562d44cc6c4d38a46ac4eb`, below the 300-second whole-attempt ceiling. This performance run is Owner05 evidence; this Backend follow-up did not duplicate the 66-second execution. The current 250 randomized small comparisons against exhaustive brute force do run in the passing Worker tests.

The current Worker state still has these blockers:

- `worker/ocr/paddle_engine.py` reports `ENGINE_UNAVAILABLE` and no qualified real Paddle runtime has been demonstrated;
- `worker/ocr/profiles/registered/` has no production profile; the fixture profile is deliberately `production_eligible=false` and returns `MODEL_UNAVAILABLE`;
- source-level `tests/ocr` are present and passing, but real multilingual Windows/Linux inference/resource evidence remains absent;
- Windows RapidFuzz resolver evidence is verified, but Linux RapidFuzz hash/lock qualification remains pending;
- the Windows resolver selects PaddleOCR 3.7.0 and PaddleX 3.7.2; PaddleX OCR extras require non-headless `opencv-contrib-python==4.10.0.84`, which conflicts with the intended headless baseline and awaits Architect/PM disposition before engine/model acquisition;
- Worker05 remains in approval-waiting state for the blocked external qualification action.

PM recorded this as dependency decision `P3-OCR-DEP-001`. The resolver evidence and direct PaddleX 3.7.2 `ocr-core` requirement were accepted as the problem statement. Architect02 produced an Option A, single upstream official wheel, minimal revision 2 candidate with requested Sol/high routing. Its exact hash is `478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44`; status is READY_FOR_REVIEW, not independently accepted or PM-activated.

Until an exact revision 2 receives independent approval:

- no candidate OCR runtime installation, model acquisition, production `AVAILABLE` profile, or new OCR dependency application is authorized;
- no `--no-deps`, headless-package override, or `pip check` exception is authorized;
- existing accepted Phase 2 dependencies remain unchanged and no baseline may be silently replaced;
- the resolver original remains preserved by Worker05, and the blocked work is classified as contract compatibility rather than an environment-permission failure;
- pure matching, geometry, schema, Backend DB/API/fencing and other engine-independent work may continue.

Accordingly, this report claims Backend owner readiness only. It does not claim real OCR availability, qualified multilingual inference, final Backend/Worker/Web integration, Phase 3 acceptance, or any AC-P3 PASS. `AC-P3-01` through `AC-P3-04` remain **NOT_RUN**. Reviewer08 was not activated. PM must verify the revision 1 archive, revision 2 candidate, Architect report and handoff hashes before activating the existing Reviewer08 for focused amendment review; final implementation review still requires all owner submissions and live integration evidence.

## Change-control record

No commit, merge, push, deployment, user-data deletion, database initialization/reset, account change, or security-setting change was performed. PM-owned `.orchestration/TASKS.yaml`, `PROJECT_STATE.yaml`, `ACCEPTANCE.yaml`, and `DECISIONS.md` were not edited by this Backend follow-up. Worker-owned corrections and resolver work were applied by Worker05 and only verified here. The resolver message caused no new `pyproject.toml` or Backend lock edit. Existing unrelated worktree changes were preserved.
