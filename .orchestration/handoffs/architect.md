# Architect handoff — ARCH-001 revision 2

- Task / owner: ARCH-001 / 02 Software Architect; Architecture role retained.
- Status / activation: Current request began with CHANGES_REQUESTED, no task dependencies, and reviewer finding R08-ARCH-001. Existing architecture was retained and corrected, not recreated. Revision 2 is READY_FOR_REVIEW; independent acceptance is still required.
- Review / history: Prior review result CHANGES_REQUESTED and AC-ARCH-01 FAIL disposition remain in [review.md](../reports/review.md). Current submission requests re-review; no finding is self-closed. ACCEPTANCE.yaml still records NOT_RUN pending PM reconciliation, not PASS.
- Changed files: the four docs/architecture Markdown documents; docs/architecture/check_contract.py, check_unicode_contract.py and unicode-cases.json; .orchestration/DECISIONS.md, TASKS.yaml, PROJECT_STATE.yaml; this handoff and ARCH-001-02.md; .orchestration/reports/ARCH-001-02-revision-2.md. Product code and prior reviewer artifacts are unchanged.
- Branch / commit: null / null for this work. No commit/push or downstream role activation.
- Evidence: [revision 2 report](../reports/ARCH-001-02-revision-2.md), including exact commands, actual results and NOT_RUN limits. Unicode reference fixtures/driver checks PASS; document/state validation results are recorded there. These do not substitute for independent acceptance or HTTP/DB tests.

## 확정된 Architecture / Domain / Relationship

The architect-selected Phase 1 design uses Next.js + TypeScript → FastAPI/Pydantic → SQLAlchemy/Alembic/PostgreSQL, with a separate local Storage adapter for originals. Trusted loopback single-operator deployment, existing README ports and project .venv commands remain. See [overview](../../docs/architecture/overview.md).

Project owns Builds, Locales, Categories and StringKeys; Category owns Situations. StringEntry is a Build/Locale-specific translation of a stable project string_id, never identified by its text. Supporting SituationExpectedString gives a Build/Situation an ordered many-to-many relation to keys; missing translations remain visible. Screenshot has one Project/Build/Locale/Category/Situation; composite FKs enforce scope and Category agreement. Referenced deletion is restrictive. Schema directions and indexes are in [domain-model](../../docs/architecture/domain-model.md).

## API Contract / Validation

[API contract](../../docs/architecture/api-contract.md) defines /api/v1 CRUD for Project/Build/Locale/Category/Situation/StringKey/StringEntry, screenshot upload/list/detail/content, AND filters, offset pagination and Situation/screenshot Expected Strings. All request/response fields, defaults, nullability, PATCH behavior, statuses and error envelope are specified. Expected mapping PUT is atomic; Expected Strings are the current Build catalog, not a historical snapshot.

Revision 2 corrects R08-ARCH-001: all string values/object keys, recursively including metadata and pre-sanitization filename, reject NUL and residual surrogate code points with 422 VALIDATION_ERROR before publication/application DB writes. Strict UTF-8 decode and safe error paths are mandatory. Accepted Japanese/Korean, supplementary characters, combining sequences, whitespace and empty translations remain exact. No schema redesign or text stripping.

## Backend 구현 지침

Thread 03 follows the explicit module map in overview.md. Preserve main/config/db and the app import path; implement api/v1 routers, shared schemas/validation/errors, services, scoped repositories, models and Storage Protocol/local adapter. Services own transaction commit; repositories and dependency finalizers do not. Share Expected Strings resolution. Import mapped classes into Alembic metadata and add a revision after unchanged 0001_bootstrap.

Implement real PostgreSQL migration/constraint tests, HTTP boundary tests (including Unicode create/patch/nested metadata), upload failure/ambiguous commit tests and a safe reconciliation command. Prove invalid input never reaches writes/publication, and read back accepted supplementary/combining text unchanged. Generate OpenAPI and coordinate Frontend types. Supply dependency reproducibility/README updates. None of that product implementation was performed by ARCH-001.

## Frontend 구현 지침

Thread 04 uses one typed API client and Backend-origin content URLs. Implement scoped metadata editors, build/locale translation editor, expected-key assignment and screenshot upload/list/detail. Use FormData file + JSON-string metadata with browser boundary. Preserve omitted versus null PATCH values. Project/filter changes reset dependent selection, pagination and caches; ignore stale responses.

Differentiate missing translation (null, missing) from existing empty text. Preserve valid user input exactly, count Unicode scalars rather than UTF-16 units, reject unpaired surrogates if client validation is provided, and display authoritative server errors/request IDs. Do not silently fix text or automatically retry ambiguous manual uploads. Build/typecheck plus behavior/integration evidence are required.

## Storage 정책 / Screenshot Metadata

Required relational core: project, build, locale, category, situation, source, original_filename, uploaded_at. Server computes UUID/hash/dimensions/size/MIME. Versioned bounded JSONB carries optional capture context. Binaries are not DB columns; generated keys sit behind stage/inspect/publish/open_read/stat/delete/list operations.

[data-flow](../../docs/architecture/data-flow.md) specifies image/request limits, original preservation, durable publication before short DB commit, known-rollback compensation and retention on ambiguous commit. Invalid Unicode may leave parser staging but must never publish an object. Reconciliation requires stopped upload writers, primary DB reference checks and 24-hour grace; missing referenced images are diagnosed, not silently erased.

## 후속 Phase 확장 포인트

- Phase 2: client_upload_id, file_hash, source, persistent fingerprint/receipt/lease idempotency; durable pending queue and retry preserve originals. No hash-only deduplication.
- Phase 3: separate OCRResult/regions with bounding_box/confidence; VerificationResult/items with frozen inputs, match_score and verification_status. Job failure is separate from translation failure.
- Phase 4: metadata.run_id/device/resolution/scenario/checkpoint/screen_state are additive. Visual Automation → captures/pending → Screenshot Upload Agent → Backend.
- Later recording/graph: separate ScreenState, VisualAnchor, Action, Transition, Scenario, Checkpoint. Transition(from_state,to_state,action,cost) supports directed multigraph edges with finite nonnegative cost; bounded visual next-state verification remains mandatory. Black Box restrictions remain unchanged.

## 현재 위험 / 이번 Phase 제외

Known limits: mutable catalogs, no safe automatic manual-upload retry until Phase 2, non-atomic DB/filesystem, restricted parent deletion, hostile image resource use, last-write-wins edits and local unauthenticated deployment. Unicode correction still needs independent re-review and later production HTTP/PostgreSQL tests. Architecture fixtures do not prove runtime persistence.

Phase 1 excludes screenshot edit/delete, historical catalog freeze/audit, bulk import/build copying, agent delivery, OCR/verification execution, visual automation/recording/graph, cloud adapter, authentication and thumbnails. ARCH-001 itself changes only architecture/evidence/orchestration, no product feature code.

## Thread 01 활성화 확인사항

1. Route this revision to Thread 08 for **ARCH-001 re-review**, explicitly checking R08-ARCH-001 closure. Existing REVIEW-WEB-001 is not the architecture review task.
2. Preserve prior CHANGES_REQUESTED/FAIL evidence and reconcile ACCEPTANCE.yaml's stale NOT_RUN. Obtain fresh independent ACCEPTED and record AC-ARCH-01 PASS with evidence; owner static checks alone cannot pass the gate.
3. Only then set ARCH-001 to the accepted state and promote BACKEND-WEB-001 and FRONTEND-WEB-001 together. Give both the same four revised documents and this handoff.
4. Keep REVIEW-WEB-001 blocked until both web owners are READY_FOR_REVIEW with evidence. Keep Phase 2+ behind previous-phase acceptance; do not auto-activate role 10.
