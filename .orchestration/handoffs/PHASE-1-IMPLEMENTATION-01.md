# Phase 1 implementation activation — PM 01 / 2026-09-06

- Tasks / owners: ARCH-001 / 02 DONE; BACKEND-WEB-001 / 03 READY; FRONTEND-WEB-001 / 04 READY.
- Activation evidence: reports/review.md latest 2026-09-06 decision is ARCH-001 REVIEW: ACCEPTED, R08-ARCH-001 RESOLVED, unresolved CRITICAL 0 / MAJOR 0. AC-ARCH-01 is PASS; current four document SHA-256 fingerprints match the reviewed source fingerprints. No open architecture blocker/critical issue in state.
- Changed files: TASKS.yaml, PROJECT_STATE.yaml, ACCEPTANCE.yaml (Phase 1 IN_PROGRESS only), DECISIONS.md and this PM handoff.
- Contract effects: none; approved revision 2 is the implementation contract. Historical owner handoffs saying pending and prior PM BLOCKED reports are superseded by current review/state.
- Branch / commit: null / null for this PM action; no commit or push.
- Verification: project .venv Python read-only YAML/assertion/hash checks PASS before promotion: reviewer result, resolved finding, criterion, blockers and all four SHA-256 fingerprints. Product API/DB/storage/Frontend tests NOT_RUN for this coordination action; prior Reviewer reference checks remain attributed to Reviewer. No AC-WEB PASS claimed.
- Review / next action: owners may start in parallel; PM marks actual start on evidence of execution. Submit own handoff and actual validation evidence for READY_FOR_REVIEW. Activate REVIEW-WEB-001 only when both submissions are ready. Phase 1 acceptance still requires every required criterion PASS and independent web review ACCEPTED.

## Shared approved contract

Read each role prompt, TASKS.yaml, PROJECT_STATE.yaml, ACCEPTANCE.yaml, DECISIONS.md, handoffs/architect.md and all four approved files: docs/architecture/overview.md, domain-model.md, api-contract.md, data-flow.md.

Use project-scoped UUID relations, immutable StringKey/string_id identity, build/locale-specific StringEntry, ordered Build/Situation expectations and current-catalog resolution. Missing translation is null/missing; existing empty text is present. Preserve valid Unicode scalars; reject NUL/residual surrogates recursively before publication or writes. API /api/v1 schemas, Page/Error, PATCH omitted/null, scoped filtering and Backend-origin content URLs are binding. Upload is one file plus JSON-string metadata with a browser-generated multipart boundary. Phase 1 has no automatic retry guarantee on an ambiguous manual upload.

Both tasks retain required AC-WEB-01..13. AC-WEB-01..05 cover Project/Build CRUD and Locale/Category/Situation management; 06 String ID multilingual strings; 07 manual screenshot upload; 08 metadata; 09 Expected Strings; 10 scoped filters; 11 reproducible fresh domain migrations; 12 Backend tests; 13 Frontend build/behavior. Ownership contributions below do not remove shared acceptance or authorize one owner to certify the other's tests.

## Thread 03 Backend

- Task: BACKEND-WEB-001, READY, blockers empty. Follow docs/prompts/03_backend.md and Backend module map in approved overview.
- Acceptance contribution: implement API/data/storage behavior for AC-WEB-01..10; directly evidence AC-WEB-11 migrations and AC-WEB-12 tests; provide real API integration support for AC-WEB-13.
- Sequence: (1) models/composite constraints and additive Alembic revision after unchanged baseline; fresh real PostgreSQL migration/constraint checks. (2) Common Unicode validation, error envelope and scoped CRUD. (3) StringKey/translations and shared Expected Strings resolver. (4) Storage adapter, bounded manual upload/content, compensation/ambiguous-commit cases and safe reconciliation. (5) OpenAPI/type alignment, reproducible dependency artifact, integration examples and evidence.
- Share with Frontend: early generated OpenAPI/export location and stable synthetic examples; routes/fields/nullability, error codes/field paths/request IDs, CORS/exposed headers, multipart metadata, content URLs and filter semantics. Generated OpenAPI must match the approved contract; discrepancies return to Architect/PM.
- Validate Unicode Create/Patch and nested metadata/filename boundaries, no-write/no-publish rejection, positive PostgreSQL readback, scope/concurrency/restrictive deletes and storage failures. Run project-.venv Backend tests. README/dependency shared edits require PM coordination within existing role boundaries.
- Submit .orchestration/handoffs/BACKEND-WEB-001-03.md with changed files, commands/results, AC evidence, unresolved issues and review request. Do not implement Frontend or later-phase agents.

## Thread 04 Frontend

- Task: FRONTEND-WEB-001, READY, blockers empty. Follow docs/prompts/04_frontend.md and approved typed-client guidance.
- Acceptance contribution: UI plus real API behavior for AC-WEB-01..10; directly evidence AC-WEB-13 build/behavior. Consume Backend's AC-WEB-11/12 evidence rather than treating mocks as proof of migrations or API tests.
- Sequence: (1) One typed API client, Page/Error models, configurable Backend origin and shared synthetic fixtures. (2) Project/scoped metadata editors and dependent selection state. (3) Build/locale translation editor and expected-key assignment. (4) Manual upload, screenshot filters/list/detail/content/Expected Strings. (5) OpenAPI reconciliation, real API integration, accessibility, build/typecheck/behavior evidence.
- Share with Backend: request/response examples and type mismatches, omitted/null PATCH values, 204 handling, Unicode scalar counting, error field mapping, FormData metadata and content origin. Mock work may proceed concurrently; final contract/integration must use generated OpenAPI and real API responses.
- Test dependent resets/cache keys, stale-response handling, missing versus empty text, error/input preservation, delete conflicts and ambiguous upload guidance. Run npm.cmd run typecheck, npm.cmd run build and meaningful behavior tests.
- Submit .orchestration/handoffs/FRONTEND-WEB-001-04.md with commands/results and AC evidence. Do not change Backend schemas or later-phase behavior unilaterally.

## Remaining gates

Roles 05/06/07/09 WAITING; role 08 WAITING until both web implementations are READY_FOR_REVIEW; REVIEW-WEB-001 remains BLOCKED. Role 02 remains available for approved contract coordination. No task creation/message dispatch or product implementation is claimed by this handoff. Phase 1 IN_PROGRESS denotes activation of the work, not acceptance.
