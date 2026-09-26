# Phase 1 Backend

Run all commands from the repository root. Python >=3.12,<3.13 is required; use the project .venv. If absent, create it with py -3.12 -m venv .venv (or a verified Python 3.12 interpreter). Do not copy a virtual environment from another location.

## Reproducible installation and startup

    .\.venv\Scripts\python.exe -m pip install --require-hashes -r backend/requirements.lock
    .\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
    .\.venv\Scripts\python.exe -m pip check
    .\.venv\Scripts\python.exe -m alembic upgrade head
    .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001

Linux equivalents use .venv/bin/python. The lock includes runtime and test dependencies and platform-marked uvloop. Dockerfile also installs from this hash lock. Regeneration is an explicit dependency maintenance action, not a startup step.

Settings load the repository-root .env and environment overrides. Never put real credentials in version control.

| Variable | Default / purpose |
| --- | --- |
| POSTGRES_DB | qa_visual |
| POSTGRES_USER | qa_visual |
| POSTGRES_PASSWORD | Required matching database credential; no default secret |
| DATABASE_HOST | 127.0.0.1; postgres in Compose |
| DATABASE_PORT | 5433; 5432 in Compose |
| STORAGE_ROOT | storage/local, resolved from repository root |

PostgreSQL must use UTF8. Client encoding and server session timezone are UTF8/UTC. Health remains /health; /ready checks the configured database. HTTP /docs and /openapi.json expose the current contract.

## API and Frontend integration

Generated contract: [openapi.json](openapi.json). Synthetic approved examples: [contract-examples.json](contract-examples.json). Refresh with:

    .\.venv\Scripts\python.exe backend/tools/export_openapi.py

API base is http://127.0.0.1:8001. Frontend uses NEXT_PUBLIC_API_BASE_URL with that default. Project routes are /api/v1/projects; child routes are /api/v1/projects/{project_id}/{resource}. Resources: builds, locales, categories, situations, string-keys, strings and screenshots.

Catalog routes implement POST/list GET/item GET/PATCH/DELETE. Screenshot routes implement POST/list GET/item GET/content GET/expected-strings GET. Situation routes include expected-string-keys GET/PUT and expected-strings GET.

- POST returns 201 and Location; PATCH/PUT return 200; DELETE returns empty 204. Referenced deletion returns 409 RESOURCE_IN_USE. Identity fields and ownership are immutable.
- PATCH omission leaves a value unchanged; explicit null clears description only. Empty PATCH and null name/text are 422.
- StringKey.string_id is stable and independent of translated text. StringEntry is unique per project/build/key/locale. Preserve valid Unicode scalars, whitespace and combining sequences; reject NUL, residual surrogates and malformed UTF-8 before persistence/publication.
- Expected Strings resolve the current build/locale catalog. Missing translation has null text/entry_id and missing status; existing empty text has present status. Mapping PUT atomically replaces the complete ordered list.
- Collections return items,total,limit,offset. Defaults 50/0; limit 1–100. Filters combine with AND. Project scope is in the URL. Screenshot filters: build_id,locale_id,category_id,situation_id,source,uploaded_from,uploaded_to. Time interval is [from,to). Nonexistent scoped IDs are 404, category/situation mismatch 422, unknown/repeated query fields 422.
- Resolve returned relative content_url against the Backend origin. Content returns original bytes, authoritative MIME/length, nosniff and a generated safe inline filename. Missing storage for a known row is 503.

Browser upload example:

    const form = new FormData();
    form.append("file", file);
    form.append("metadata", JSON.stringify({
      build_id, locale_id, category_id, situation_id,
      source: "manual", metadata_version: 1, metadata: {}
    }));
    await fetch(apiOrigin + "/api/v1/projects/" + projectId + "/screenshots", {
      method: "POST", body: form
    });

Let the browser generate Content-Type and multipart boundary. Exactly one file part and one JSON-string metadata part are required. No automatic retry after ambiguous upload failure. Phase 1 rejects agent/automation sources, client_upload_id and Idempotency-Key.

Limits: 20 MiB file, 21 MiB request, 32 KiB metadata form part, 16 KiB decoded compact metadata, container depth 5, 100 total object keys. One PNG/JPEG frame only; fully decoded width/height <=16384 and <=40 million pixels. Original bytes are preserved.

Errors use {error:{code,message,details:[{field,reason}],request_id}}. X-Request-ID is server generated; 503 includes Retry-After: 5. Errors never include SQL, credentials or rejected input. Codes: VALIDATION_ERROR, RESOURCE_NOT_FOUND, METHOD_NOT_ALLOWED, DUPLICATE_RESOURCE, RESOURCE_IN_USE, RELATIONSHIP_MISMATCH, UNSUPPORTED_LOCALE_CODE, INVALID_MULTIPART, UPLOAD_TOO_LARGE, UNSUPPORTED_MEDIA_TYPE, INVALID_IMAGE, DATABASE_UNAVAILABLE, STORAGE_UNAVAILABLE, INTERNAL_ERROR.

CORS allows exactly http://localhost:3001 and http://127.0.0.1:3001; credentials disabled. Methods GET/POST/PATCH/PUT/DELETE/OPTIONS and Content-Type are permitted. Exposed headers: X-Request-ID, Location, Retry-After.

## Database and storage

Migration 0001_bootstrap remains unchanged; 0002_phase1_domain creates nine domain tables and composite scoped FKs, restrictive deletes, uniqueness/check constraints and indexes. No create_all startup and no QA seed data.

Reads use REPEATABLE READ for consistent counts/items. Write services use READ COMMITTED; expected mapping replacement locks the Build row so a waiting replacement observes the previous committed mapping. Repositories do not commit; request cleanup only rolls back.

Storage Protocol separates stage/inspect/publish/open_read/stat/delete/list from DB services. Local paths are generated, relative opaque keys. Traversal, symbolic links and Windows reparse points are rejected. No public static directory or database binary columns.

Stage original bytes and fsync before atomic no-overwrite hard-link publication. NTFS and Linux local filesystem behavior is tested. POSIX directory entries are fsynced; Python offers no equivalent portable Windows directory fsync, so sudden power-loss durability on Windows has that limitation. Use a local filesystem supporting hard links.

Publish precedes a short revalidated DB insert/commit. Known rollback compensates the exact owned object; ambiguous commit retains it and checks a fresh primary connection. Failed compensation is logged for reconciliation.

## Maintenance

Stop every upload writer and drain/terminate in-flight requests first. Dry-run is default:

    .\.venv\Scripts\python.exe -m backend.app.maintenance.reconcile_storage --writers-stopped
    .\.venv\Scripts\python.exe -m backend.app.maintenance.reconcile_storage --writers-stopped --apply

Primary DB and complete inventories are required before deleting anything. Only adapter-owned unreferenced objects/staging older than 24 hours qualify. Each exact key is checked against a fresh primary snapshot immediately before deletion. Missing referenced objects and hash/size mismatches are reported, not silently removed. Never run this command concurrently with upload writers. Coordinate DB/object backups at a stopped-writer checkpoint.

## Verification

Configured PostgreSQL (requires matching credentials and permission to create disposable test databases):

    .\.venv\Scripts\python.exe -m pytest tests/backend -q --basetemp=.pytest_cache/backend-local

Independent PostgreSQL container, preserving configured databases:

    .\.venv\Scripts\python.exe backend/tools/run_postgres_tests.py -q --tb=short
    docker build -f backend/Dockerfile.test -t qa-backend-test-runtime:local .
    .\.venv\Scripts\python.exe backend/tools/run_postgres_tests.py --linux -q --tb=short
    .\.venv\Scripts\python.exe backend/tools/check_clean_install.py

The runner uses generated credentials, a random loopback port and uniquely owned containers/networks/databases. It cleans up its resources. Clean-install environments remain under ignored .pytest_cache for inspection.

Tests cover CRUD, Unicode round trips and rejection, scopes, restrictive deletes, missing/empty expectations, concurrent duplicates/mapping replacement, uploads/content/filters, original-byte preservation, storage failures, rollback/ambiguous commit, safe reconciliation and fresh migration/downgrade/re-upgrade/model parity.

## Phase 3 OCR verification backend

The Backend stores an immutable creation snapshot, profile/config digests and a durable PostgreSQL job for each explicit verification run. Start the separately supervised runner with:

    python -m backend.app.workers.ocr

Create and read runs below `/api/v1/projects/{project_id}/screenshots/{screenshot_id}/verification-runs`; list deployment profiles at `/api/v1/projects/{project_id}/ocr-profiles`. First creation returns `202`, replay of the same `(project_id, client_run_id)` and fingerprint returns `200`, and both return the original run location. Active run reads expose `Retry-After: 2`. Result resources stay unavailable until OCR and verification results commit atomically.

The runner claims from the database with a generation/token lease, renews on a separate session, verifies the frozen source hash and canonical inputs, runs the `worker.ocr` and `worker.verification` adapters in a supervised child process, and publishes only complete bounded results. A profile is usable only when its registered immutable production document is valid, its canonical qualification status is `QUALIFIED`, it is production eligible, and the deployment admits that exact profile ID and digest for its worker target and release. API-local platform matching is not deployment admission; it cannot make an invalid, unqualified, or non-production document usable, and its local mismatch does not invalidate an otherwise exact external admission for the worker target. The repository fixture profile is never a production profile; an empty production registry is valid but cannot execute OCR.

Admission defaults to unavailable. Supply the same externally managed, immutable JSON assertion to the API and runner with `QA_OCR_ADMISSION_PATH`, its exact raw-byte SHA-256 in `QA_OCR_ADMISSION_SHA256`, and the expected `QA_OCR_WORKER_TARGET` and `QA_OCR_RELEASE_ID`. The assertion is at most 64 KiB and has this exact versioned shape:

    {"schema_version":1,"worker_target":"windows-x86_64","release_id":"release-2026.09.25","profiles":[{"profile_id":"qualified-profile-v1","profile_digest":"<64 lowercase hex characters>"}]}

Unknown fields, duplicate keys or profile IDs, malformed values, a content-pin mismatch, or a target/release mismatch make every profile unavailable. There is no boolean readiness setting, and API-local operating-system, cgroup, cache, package, or model observations cannot enable admission. The content pin protects assertion integrity; it is not qualification evidence. Operators may publish a real assertion only after the exact target, release, profile, runtime, containment, models, dictionaries, native libraries, and required behavior have completed the approved qualification process.

Phase 3 execution errors include `OCR_PROFILE_UNKNOWN`, `OCR_PROFILE_UNAVAILABLE`, `OCR_LOCALE_UNSUPPORTED`, `RUN_IDEMPOTENCY_CONFLICT`, `RESULT_NOT_READY`, and the durable safe worker error codes recorded on a failed Run. These errors do not expose storage paths, model locations, rejected payloads or child tracebacks.

Device automation, screenshot edits/deletes, S3 implementation and authentication remain excluded.
