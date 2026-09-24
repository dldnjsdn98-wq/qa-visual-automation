# Backend handoff — BACKEND-WEB-001 / owner 03

- Status: READY_FOR_REVIEW after executed implementation checks. Activation: ARCH-001 DONE / revision 2 ACCEPTED / AC-ARCH-01 PASS, PM PHASE-1-IMPLEMENTATION-01 handoff and explicit user authorization to implement/update task state.
- Repository: current project root, C:/Dev/qa-visual-automation. Backend role retained after relocation; old root was not accessed after the switch. Current state/review/acceptance/history references are present. No legacy absolute path match in inspected source/config/documents.
- Phase: 1 IN_PROGRESS. No phase acceptance or later-phase activation.
- Contract changes: none. All four approved architecture document fingerprints match the Reviewer report.
- Evidence: [BACKEND-WEB-001-03 report](../reports/BACKEND-WEB-001-03.md), Windows JUnit and Linux output linked there.
- Review request: independent review of Backend implementation and evidence; review_result remains null. PM coordinates combined web review when owner 04 is also ready.

## Implemented APIs

/api/v1/projects supports CRUD. Project-scoped builds, locales, categories, situations, string-keys and strings support POST/list GET/item GET/PATCH/DELETE. Situation expected-string-keys supports GET/atomic PUT; Situation expected-strings supports GET. Screenshot supports manual POST, filtered list, detail, content and expected-strings GET.

43 business operations plus unchanged /health and /ready. Typed request/response schemas, standard Error envelopes, server request IDs, local CORS, exact Page/filter/PATCH/null semantics and no automatic translation fallback.

## DB / migration

Nine domain tables: projects, builds, locales, categories, situations, string_keys, string_entries, situation_expected_strings, screenshots. Composite scope FKs enforce project/category agreement; unique constraints preserve catalog identity; restrictive deletes prevent silent data loss. StringKey.string_id is independent of translated text.

0001_bootstrap is unchanged. Additive 0002_phase1_domain creates all domain tables/constraints/indexes; backend/schema.sql is the offline generated DDL. Fresh PostgreSQL migration, baseline downgrade/re-upgrade, metadata parity and direct FK rejection tests pass on Windows/Linux.

Read snapshots are REPEATABLE READ; writes use explicit READ COMMITTED service transactions. Expected replacement locks Build before mapping mutation. Repositories never commit. UTF8/UTC are configured; unsupported DB encoding fails migration.

## Storage / upload

Local Storage Protocol implementation uses private staging and generated opaque object keys, original bytes, SHA-256, safe filenames and strict PNG/JPEG decoding/limits. No screenshot binary column or public static mount.

Durable no-overwrite publication precedes revalidation/short DB insert. Known rollback compensates the owned object; ambiguous commit retains and checks primary. Explicit dry-run/apply maintenance requires stopped/drained writers and primary availability, observes 24-hour grace, rechecks exact references and reports missing/mismatched objects.

Windows file durability/no-overwrite and Linux filesystem behavior are tested; Windows portable directory fsync remains a documented limitation.

## Environment / commands

Use Python >=3.12,<3.13 and project .venv. Settings: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, DATABASE_HOST, DATABASE_PORT, STORAGE_ROOT. Defaults: qa_visual / qa_visual / no secret / 127.0.0.1 / 5433 / storage/local. Compose DB address is postgres:5432. Storage resolves relative to project root; no user interpreter path is hardcoded.

Full commands and maintenance usage: [backend README](../../backend/README.md).

    .\.venv\Scripts\python.exe -m pip install --require-hashes -r backend/requirements.lock
    .\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
    .\.venv\Scripts\python.exe -m alembic upgrade head
    .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001
    .\.venv\Scripts\python.exe backend/tools/run_postgres_tests.py -q --tb=short
    docker build -f backend/Dockerfile.test -t qa-backend-test-runtime:local .
    .\.venv\Scripts\python.exe backend/tools/run_postgres_tests.py --linux -q --tb=short

Actual results: Windows 54 PASS; Linux 54 PASS; clean hash-locked installation on Windows/Linux PASS; pip check PASS; Frontend-owned actual API integration 2 PASS. Two upstream TestClient deprecation warnings remain. Never reinterpret earlier failed attempts as passing.

## Thread 04 connection contract

- Base http://127.0.0.1:8001; Frontend NEXT_PUBLIC_API_BASE_URL. Generated [OpenAPI](../../backend/openapi.json), [synthetic examples](../../backend/contract-examples.json), runtime /openapi.json and /docs. Regenerate with backend/tools/export_openapi.py.
- FormData has file and metadata; metadata is JSON.stringify(ScreenshotUpload). Browser sets Content-Type/boundary. source=manual only. Limits 20 MiB file / 21 MiB whole request. Do not automatically retry ambiguous uploads.
- Metadata part contains build_id,locale_id,category_id,situation_id,source and optional metadata_version=1/metadata={}; Project is only in URL. No client_upload_id/Idempotency-Key yet.
- Relative content_url must resolve against Backend origin. Content returns originals; 503 means known metadata but unavailable storage. Detail Expected Strings resolves the current build/locale/situation catalog.
- CORS origins exactly localhost:3001 and 127.0.0.1:3001 (HTTP), no credentials, GET/POST/PATCH/PUT/DELETE/OPTIONS, Content-Type. Expose X-Request-ID, Location and Retry-After.
- POST 201 + Location; DELETE 204 empty; PATCH omitted fields unchanged and null only clears description. Error shape {error:{code,message,details:[{field,reason}],request_id}}; 503 Retry-After 5. Error codes and field paths are documented in backend/README.md; the OpenAPI uses Error for business failures.
- Screenshot AND filters: build_id,locale_id,category_id,situation_id,source,uploaded_from,uploaded_to,limit,offset; Project is path scope. Missing scoped references 404; category/situation mismatch 422; unknown/repeated filters 422. Default pagination 50/0; time interval [from,to).
- Expected text null/missing differs from empty/present. Unicode scalar preservation and invalid-input rejection apply recursively, including pre-sanitization filename.
- Read-only comparison of frontend/lib/types.ts and api.ts found matching principal resource shapes, omission/null semantics, FormData and content-origin behavior. Existing Frontend actual-client integration suite ran against Uvicorn+PostgreSQL and passed 2 tests; whole UI/build acceptance remains owner 04.

## Files / remaining coordination

Backend app API/schemas/models/repositories/services/validation/storage/maintenance, migrations, tests/backend, pyproject.toml, alembic.ini, Backend Dockerfiles, requirements.lock, OpenAPI/examples/SQL exports and own evidence/handoffs. Frontend files were not edited by owner 03.

Implementation tests are not blocked. Default persistent local DB still rejects configured credentials on port 5433: PM/operator must align .env with existing DB credentials for normal startup. No credential/volume reset performed. Isolated test and Frontend API integration environments work.

Shared root README linking to Backend README is a PM documentation coordination item. Full browser visual/load/power-loss tests are NOT_RUN here. No Architecture semantic change is requested. Reviewer/PM retain authority for AC-WEB/phase acceptance.

Branch: main. Existing role-10 checkpoint: 811b1e36199d424d83930f3381c7d71e537bc7d6 (earlier WIP). Final implementation commit: null; final changes uncommitted; no commit/push by Backend.
