# Decisions
- 2026-09-05: Preserve the open project root; logical package name qa-visual-automation. No nested project.
- Existing empty Git repository retained; unborn branch set to main. No commit or push authorized.
- Python 3.12.14 available through desktop runtime; create .venv from it and use .venv directly.
  py/python are not on PATH. No machine-specific executable paths in project artifacts.
- FastAPI + SQLAlchemy 2 + Alembic + psycopg; Next.js App Router + TypeScript.
- PostgreSQL 17 with named volume; host localhost ports 5433/8001/3001. No Redis/OCR containers yet.
  Existing services occupy 5432/8000/3000, so host ports were changed after startup conflicts.
  Internal container ports remain PostgreSQL 5432 and Backend 8000.
- Empty Alembic baseline only; domain model and API documents are proposals pending ARCH-001.
- Initial local filesystem storage mount; storage abstraction and safe upload belong to Phase 1.
- Generate random local DB secret into ignored .env; .env.example contains placeholders only.
- Backend liveness and DB readiness are separate. No CRUD, OCR or automation in Bootstrap.
- Role states in YAML describe eligibility; separate Codex tasks are to be created in the next session.
- Frontend lockfile records resolved dependency versions. Python uses constrained ranges; cross-platform lock policy deferred to Architect.
- 2026-09-05 (PM): Review dependency readiness is an explicit exception to implementation dependency acceptance: REVIEW-WEB-001 becomes READY when both web owners submit READY_FOR_REVIEW with evidence. This implements the user's review sequence and prevents circular acceptance gating.
- 2026-09-05 (PM): ARCH-001 remains READY, not IN_PROGRESS. No matching Architecture role task was found in the current app task listing; dispatch is pending. Roles describe eligibility, not execution. Backend and Frontend are BLOCKED by unaccepted ARCH-001; later phases remain TODO behind existing phase gates.

## 2026-09-05 — ARCH-001 / owner 02, submitted for review

These are architect-selected contracts, pending independent AC-ARCH-01 review; they supersede the bootstrap proposals, not the acceptance gate.

- ADR-ARCH-001: Project-scoped Locale and Category; Situation belongs to Category. Composite FKs enforce scope, including Screenshot Category/Situation agreement. Immutable semantic identifiers and restrictive deletes avoid silent reparenting/data loss.
- ADR-ARCH-002: Add StringKey as stable project/string_id identity, StringEntry unique per Build/Locale/key, and Build/Situation-to-key expected mappings. Text is never identity. No implicit translation fallback. Missing and empty translations are distinct. Current catalog semantics are explicit; Phase 3 freezes verification inputs.
- ADR-ARCH-003: /api/v1 typed CRUD, separate StringKey management, atomic ordered expectation replacement, stable error envelope, bounded offset pagination and AND filters. Screenshot content is served through scoped Backend route. API contract is normative until generated OpenAPI is available.
- ADR-ARCH-004: Immutable relational screenshot core plus bounded versioned JSONB for future capture context. Original bytes remain behind Storage interface, local adapter first; SHA-256 computed immediately. No binary DB columns or public static storage directory.
- ADR-ARCH-005: Durable object publication before short DB insert transaction. Known rollback uses compensation; uncertain commit never triggers immediate deletion. Reconciliation requires exclusive maintenance with upload writers stopped, primary DB available and 24-hour age grace. Missing referenced objects are reported, not silently removed from DB.
- ADR-ARCH-006: Phase 1 manual PNG/JPEG only, max 20 MiB file/21 MiB whole request/40 million pixels. Preserve originals. Reserve nullable client_upload_id; actual persisted receipt/fingerprint/lease idempotency is Phase 2. Hash alone is not deduplication.
- ADR-ARCH-007: Trusted loopback-only single-operator deployment, no Phase 1 authentication. Shared deployment needs identity/authorization review. Browser API origin configurable with explicit local CORS origins. Current README ports and project .venv workflow retained.
- ADR-ARCH-008: Preserve applied empty baseline; add domain migration and test with real PostgreSQL. Single-container startup migration permitted until replica deployment. Backend owns a reproducible Python 3.12 lock/constraints artifact with clean Windows/Linux install evidence and README update; existing ranges are not a lock.
- ADR-ARCH-009: Future OCR/verification results are separate versioned records. ScreenState, VisualAnchor, Action, Transition, Scenario and Checkpoint remain separate; Transition is a directed multigraph edge with nonnegative finite cost. Visual Automation → captures/pending → Screenshot Upload Agent → Backend. Black Box restrictions remain binding.
- Coordination: User explicitly requested actual task-state updates in this Architect task. Owner records ARCH-001 READY_FOR_REVIEW and dispatch REVIEW_REQUESTED after producing evidence. PM still coordinates independent role 08 review and acceptance/promotion; AC-ARCH-01 remains NOT_RUN, review_result null, all downstream gates unchanged. This does not claim PM approval or create a separate review task. Historical PM handoff remains intact.

## ARCH-001 revision 2 — targeted rework after R08-ARCH-001

- ADR-ARCH-010: Keep the existing Domain/relationship/API design. Correct the persisted-string contract: all incoming string values and object keys, including recursive metadata and filenames before sanitization, exclude U+0000 and residual surrogate code points. Strict UTF-8/JSON decoding precedes this check. Invalid input receives 422 VALIDATION_ERROR before any published object/application DB write; accepted supplementary characters, combining sequences, whitespace and empty translations remain intact. Use UTF8 database/client encoding. No schema redesign. This addresses R08-ARCH-001 at author level; independent closure remains pending.
- ADR-ARCH-011: Make Thread 03 module ownership explicit in overview.md: retain current main/config/db entrypoints; separate API/schemas/validation/services/repositories/models/Storage/maintenance; services own commit, repositories never commit, dependency cleanup never commits. Register all models in Alembic metadata. One Expected Strings resolver serves both endpoints.
- ADR-ARCH-012: Frontend uses one typed Backend-origin API client, browser-generated multipart boundary, explicit omitted/null PATCH handling, scalar-based Unicode length and exposed request/error headers. This refines the existing API without changing routes or identity semantics.
- Review coordination: Initial submission was independently reviewed with CHANGES_REQUESTED and AC-ARCH-01 FAIL disposition in reports/review.md. Preserve that evidence; do not claim review never occurred. Revision 2 is submitted READY_FOR_REVIEW with null current review_result and prior result retained in review_history. ACCEPTANCE.yaml still has historical NOT_RUN and needs PM reconciliation; it is not evidence of approval. Thread 01 must obtain independent re-review and AC-ARCH-01 PASS before promoting Thread 03/04. No downstream role is activated by this rework.

## PM readiness audit — ARCH-001 revision 2

- Directly inspected requested state, architect handoff, four architecture documents, reviewer evidence and revision 2 scripts/report. Specification covers Phase 1 implementation needs; no additional mandatory design omission was identified in this PM inspection. Both architecture checks executed successfully; these are not product or independent review acceptance.
- Reconciled AC-ARCH-01 from stale NOT_RUN to the last independent FAIL disposition, with revision 2 closure explicitly pending. Preserve owner and reviewer evidence. Do not treat an owner correction or PM reference-check PASS as an independent ACCEPTED result.
- ARCH-001 remains READY_FOR_REVIEW; Backend/Frontend remain BLOCKED. Implementation milestone and role promotion are withheld pending required review evidence. Roles 05/06/07/09 remain waiting and role 10 is not activated.
- Latest user instruction keeps role 08 waiting until both web tasks are READY_FOR_REVIEW. No new review is dispatched. This conflicts with the existing prerequisite for independent architecture closure; record the gate conflict explicitly rather than silently waiving it or activating a reviewer against the instruction.

## Independent revision 2 approval — Reviewer 08

- The subsequent explicit user request authorizes ARCH-001 revision 2 independent re-review and acceptance/task updates. It supersedes the preceding hold for this architecture review and resolves the recorded gate conflict.
- Reviewer compared every R08-ARCH-001 requirement against revision 2, inspected retained domain/API/storage/extension contracts, and independently reran both architecture checkers successfully. R08-ARCH-001 is RESOLVED; AC-ARCH-01 PASS; ARCH-001 ACCEPTED. Evidence and original revision 1 review are in reports/review.md.
- ACCEPTED satisfies TASKS.yaml architecture dependencies; a separate DONE transition is not required for implementation eligibility. PM owns coordinated Backend/Frontend READY promotion and role 03/04 activation. Those tasks remain blocked pending that PM action, with the obsolete architecture-failure blockers replaced.
- No product tests, web criteria or phase acceptance are claimed. REVIEW-WEB-001 still requires both implementation submissions; later-phase gates and user-only role 10 activation remain unchanged. Reviewer made no product-code, architecture-source, commit or push changes.

## 2026-09-06 — PM activates Phase 1 implementation

- Verified current Reviewer ACCEPTED, R08-ARCH-001 RESOLVED, AC-ARCH-01 PASS, empty architecture blockers/critical issues and zero unresolved CRITICAL/MAJOR in the latest review. All four current contract SHA-256 fingerprints match the independently approved report.
- ARCH-001 transitions from ACCEPTED to DONE for PM completion bookkeeping; review_result ACCEPTED, revision 2 and historical review evidence remain intact. No additional review is required by this transition.
- BACKEND-WEB-001 and FRONTEND-WEB-001 are promoted together to READY with no blockers. Roles 03/04 become eligible alongside PM and Architect contract support. Milestone is PHASE 1 Web MVP Implementation; Phase 1 is IN_PROGRESS, not ACCEPTED. READY is eligibility, not a claim that either owner has begun execution.
- Roles 05/06/07/09 stay WAITING. Role 08 is both conditionally eligible and currently WAITING until both web tasks have READY_FOR_REVIEW evidence. Role 10 remains user-request-only.
- All web and later-phase criteria remain NOT_RUN. Owner submission/accepted-state scripts have state-specific assertions and are not permanent DONE-state gates; no script or state is rewritten merely to obtain a PASS. Promotion evidence and owner instructions: handoffs/PHASE-1-IMPLEMENTATION-01.md.
