# Phase 1 Architecture — ARCH-001

Revision 2: targeted correction of R08-ARCH-001; existing design retained; independent re-review pending.

Status: architect specification complete; independent review pending. Owner: 02. Date: 2026-09-05. This contract is submitted for AC-ARCH-01 and does not claim implemented functionality or acceptance.

## Boundaries and deployment

Next.js App Router + TypeScript provides metadata CRUD, upload and screenshot review. Python 3.12 / FastAPI / Pydantic v2 / SQLAlchemy 2 / Alembic / PostgreSQL 17 owns validation, transactions and project scoping. PostgreSQL stores metadata; an injected Storage interface stores binaries. Phase 1 uses local storage and has no OCR worker, broker or automation service.

Phase 1 is a trusted single-operator local workstation deployment, without authentication. Project scoping is data integrity, not access control. Keep loopback bindings in Compose. Network deployment requires a separately reviewed authentication, authorization and TLS design. Browser calls Backend using configurable public API origin (default http://127.0.0.1:8001). CORS allows exactly http://localhost:3001 and http://127.0.0.1:3001, credentials disabled. Future server-side calls need a separate internal origin; container loopback is not the host Backend.

Existing /health, /ready, /docs and /openapi.json remain unchanged. Business routes use /api/v1 and the error contract in api-contract.md. Forbid undeclared request fields except the extensible screenshot metadata object. Never expose storage keys, filesystem paths or DB exceptions.

## Contract decisions

- Project owns Builds, Locales, Categories and stable StringKeys. Situation belongs to one Category and Project. Cross-project references are rejected by services and composite foreign keys.
- StringKey contains stable string_id. StringEntry is a translation unique by (project, build, string_id, locale). Text is never identity. Separate builds cannot overwrite one another's translations.
- SituationExpectedString maps a Situation to a StringKey for one Build, independently of Locale. Missing translations remain explicit. Expected Strings are the current catalog for the selected build, not an upload-time snapshot.
- Referenced resources use restrictive deletion; no cascading wipe, screenshot deletion, build cloning or ownership reassignment in Phase 1.
- Screenshot relational core is immutable. Versioned JSONB holds optional future capture context. Filenames are labels only.
- Phase 1 computes SHA-256 and reserves nullable client_upload_id. Phase 2 implements durable idempotency. Phase 1 rejects supplied client upload IDs rather than promising safe retries.

See [domain-model.md](domain-model.md), [api-contract.md](api-contract.md), and [data-flow.md](data-flow.md) for normative details.

## Backend implementation guidance

Use routers → application services → repositories/SQLAlchemy session and Storage adapter. Pydantic validates shape; services enforce scope and business rules; DB unique constraints and composite FKs guard concurrent writes. Translate known violations into stable errors and roll back transactions. Ownership cannot be inferred from a UUID alone.

Use a session per request and explicit short transactions. File decoding and storage I/O stay outside long DB transactions. Synchronous SQLAlchemy/psycopg with synchronous FastAPI handlers is acceptable; do not block an async event loop. Storage cleanup is an explicit maintenance command, not an in-process callback that disappears on restart.

Implement every route/model in api-contract.md and every constraint in domain-model.md. Test concurrent duplicates, cross-project IDs, missing translations, restrictive deletes, pagination/filter combinations and upload failure boundaries. Generated FastAPI OpenAPI becomes the machine-readable contract; Frontend types must be generated from or checked against it. Contract changes return to Architect and PM before consumers diverge.

### Backend module map — Thread 03 target structure

Retain existing `backend.app.main:app`, `config.py`, `db.py` and Alembic entrypoints so README commands continue to work. The following are implementation targets, not files created by ARCH-001:

| Module under backend/ | Responsibility and dependencies |
| --- | --- |
| app/main.py | App composition, existing health/readiness, CORS, request ID/error handlers, mount api/v1 router; no domain transactions |
| app/config.py | Existing environment settings plus bounded upload/CORS settings and Storage selection; no interpreter paths |
| app/db.py | Existing Base/engine plus session factory; one Base across all domain models |
| app/api/dependencies.py | Yield/close request session, inject Storage; rollback outstanding transaction on exception; never commit in dependency finalizer |
| app/api/v1/router.py | Assemble resource routers under /api/v1 |
| app/api/v1/{projects,builds,locales,categories,situations,string_keys,strings,screenshots}.py | HTTP binding, typed models, status/headers; Situation router includes expected mapping/resolution, Screenshot router includes upload/detail/content/expected resolution |
| app/schemas/{common,catalog,strings,screenshots}.py | Pydantic requests/responses matching contract names; closed models, PATCH omission handling, Page/Error, scoped UUIDs |
| app/validation/{unicode,metadata,images}.py | Shared strict Unicode boundary, recursive metadata limits/types, isolated bounded image decoding; usable by future agent/worker entrypoints without HTTP imports |
| app/models/{catalog,strings,screenshots}.py | SQLAlchemy tables, FK/unique/check/index declarations; models/__init__.py imports every mapped class |
| app/repositories/{catalog,strings,screenshots}.py | Scoped DB lookups/inserts/queries; receive Session, no independent commit and no storage/HTTP imports |
| app/services/{catalog,strings,expected_strings,screenshots}.py | Own transaction boundaries, relationship rules, ordered replacement, missing translation resolution and upload compensation; no FastAPI Response dependencies |
| app/storage/{base,local}.py | Storage Protocol and local implementation; no SQLAlchemy dependency; exact operations in data-flow.md |
| app/errors.py | Domain error types and stable conversion to API Error; safe validation paths, no rejected payload echo |
| app/maintenance/reconcile_storage.py | Explicit dry-run/apply maintenance entrypoint with stopped-writer precondition, no request background scheduling |
| migrations/env.py and versions/ | Import models before target_metadata is consumed; preserve 0001_bootstrap and add domain revision |

Dependency direction: API → schemas/validation/services → repositories/models and Storage Protocol. `main.py`/dependencies construct the local adapter; repositories do not import routers, and Storage does not import repositories. ExpectedStrings uses one shared resolver for Situation and Screenshot endpoints. Write services explicitly commit only after all required validation; request-session cleanup never implies success. Reads use a consistent query/snapshot for count/items. For upload, separate reference validation from final short insert transaction per data-flow.md.

Apply one persistable-Unicode validator across request models and recursively decoded metadata before any persistence. Reject U+0000 and residual surrogates with 422; preserve accepted scalar sequences. Configure UTF8 database/client encoding. Alembic should fail clearly on incompatible encoding rather than silently altering an existing database. Add API tests proving rejected input cannot call repository writes/Storage.publish and positive supplementary-character round trips. The storage-independent architecture fixture check is not the production validator.

### Backend delivery sequence

After PM activation: (1) models/new migration and PostgreSQL constraint tests; (2) shared errors/validation and metadata CRUD; (3) string keys/translations and Expected Strings; (4) Storage, upload/content and failure/reconciliation cases; (5) OpenAPI export, end-to-end contract examples and owner evidence. Thread 04 can build against this document concurrently; once the first OpenAPI export exists, check all consumer types and behavior against it before integration. Changes to contract semantics require Architect/PM review rather than unilateral consumer workarounds.

## Frontend implementation guidance

Provide Project CRUD and selection, scoped Build/Locale/Category/Situation management, string key and build/locale translation editing, ordered Expected Strings assignment, upload form, filtered screenshot list and detail. Show string_id as semantic identity. Empty translations and missing translations are distinct. Do not infer OCR or verification badges.

Project changes clear dependent selections/caches; Category changes clear incompatible Situation; Build changes reload translations and expectations. Cache keys include project and filters. Abort or ignore stale responses after selection changes. Reset offset when filters change. Display field errors/request IDs and preserve input after errors. Confirm deletes, explain RESOURCE_IN_USE and handle 204 without JSON parsing.

Upload requires Build, Locale, Category, Situation and one PNG/JPEG with source=manual. Refresh only after 201. An ambiguous timeout has no safe automatic retry in Phase 1: prompt the operator to inspect the list before manually retrying. Detail uses scoped content and Expected Strings endpoints, labeling catalog_mode=current and selected Build. Render filenames and translations as plain text.

Centralize calls in a frontend API module with configurable Backend base URL, typed Page/Error models and one error parser. Build FormData with `file` and JSON-string `metadata`; let the browser set the multipart boundary. Explicitly allow methods GET/POST/PATCH/PUT/DELETE/OPTIONS and Content-Type in local CORS, and expose X-Request-ID, Location and Retry-After so the browser can inspect contract headers. Store timestamps as server UTC values and format only for display. Preserve omitted versus null PATCH fields. Do not use JavaScript string.length as the scalar limit for supplementary characters; validate unpaired surrogates and count scalars as specified in api-contract.md. Server validation stays authoritative.

Frontend data dependency: select Project → load Builds/Locales/Categories → Category-filtered Situations. Catalog editor uses string-keys plus strings filtered by Build/Locale; assignment editor uses expected-string-keys with Build; review view uses screenshots and screenshot expected-strings. Independent lists may load concurrently, but dependent IDs must be cleared before fetching new scoped data. Contract mock fixtures are synthetic and must be reconciled with generated OpenAPI; a working mock screen is not API integration acceptance.

## Environment, migrations and dependencies

Follow README Quick Start: project .venv first; if absent use py -3.12, then a verified Python 3.12 interpreter to create .venv. No system Python or Node absolute paths. Local DB is 127.0.0.1:5433, Compose DB postgres:5432. Host ports stay 3001/8001/5433 and container ports 3000/8000/5432. Use npm.cmd ci and existing frontend lockfile.

Keep 0001_bootstrap unchanged. Backend adds a domain revision with tables/constraints/indexes in dependency order. On an isolated PostgreSQL database, verify fresh upgrade head, baseline-to-head, downgrade to baseline/re-upgrade and direct SQL cross-scope rejection. Never downgrade user data. No QA seed data in migrations. Future migrations add result/run tables, nullable columns and backfills; never rewrite applied revisions.

The single Backend container may retain startup migration for Phase 1; before multiple replicas, use one release migration job. SQLite/bootstrap tests do not establish domain migration acceptance. Backend must add a reproducible Python 3.12 dependency lock/constraints artifact with versions/hashes and no machine paths, verify clean Windows/Linux installs and document the command in README before claiming installation reproducibility. Current ranges are not a lock. ARCH-001 does not modify dependencies or runtime code.

## Future phases, exclusions and risks

Phase 2 adds durable uploader/idempotency. Phase 3 adds OCRResult/VerificationResult and immutable verification inputs. Phase 4 visual automation writes captures/pending and the separate upload agent handles delivery. Phase 5 adds recordings and reviewable transition candidates. Phase 6 executes a weighted state graph; Phase 7 integrates accepted phases.

Keep ScreenState, VisualAnchor, Action, Transition, Scenario and Checkpoint distinct. Only screenshots, ADB tap/swipe/keyevent/text, OpenCV, templates and OCR assistance are permitted. Unity GameObject, Unreal Widget/Object, resource-id game automation, game/debug APIs, memory, internal events/scripts and developer hooks are forbidden.

Phase 1 excludes agent delivery, OCR/matching, graph execution, recording, authentication, cloud adapter implementation, bulk import, build copy/freeze, historical catalog audit, screenshot edits/deletes and thumbnails. Risks include mutable expectations, non-atomic filesystem/DB writes, hostile image decoding, missing translations and last-write-wins concurrent catalog edits. Linked contracts specify mitigations. Independent role 08 review and PM acceptance precede Backend/Frontend activation.
