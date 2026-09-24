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

## 2026-09-08 — PM opens web review with separate environment remediation

- Both BACKEND-WEB-001 and FRONTEND-WEB-001 are READY_FOR_REVIEW with current handoffs/reports. Windows JUnit contains 54 tests and zero failures/errors/skips; Linux output contains 54 passed; Frontend reports 23 behavior tests, two isolated real-API tests, build/typecheck and desktop critical flow. These are owner submissions, not PM-executed product tests or independent acceptance.
- Remove the satisfied submission-wait blocker from REVIEW-WEB-001 and set READY. Role 08 becomes active/eligible; project_status IN_REVIEW while ACCEPTANCE Phase 1 stays IN_PROGRESS and all AC-WEB entries remain NOT_RUN.
- Track configured persistent PostgreSQL authentication failure as required ENV-P1-DB-001, owner 03, READY to remediate, issue OPEN. It blocks default-deployment verification/final Phase 1 acceptance, not independent inspection or isolated reproducible review. Preserve both owner READY_FOR_REVIEW submissions. No new architecture defect or Frontend rework is inferred from the environment failure.
- Record the owner-reported failed authenticated DB check separately from passing isolated suites. Close only after configured-environment revalidation and independent Reviewer confirmation; never substitute an isolated test DB for persistent-deployment proof.
- Thread 03 diagnoses connection target and credential sources without exposing secrets or deleting/resetting existing DB volumes. Thread 08 reviews submitted product evidence independently and withholds final acceptance until required environment closure. Exact scope and gates: handoffs/REVIEW-WEB-001-01.md. No product/credential changes, independent review, commit or push by PM.

## 2026-09-11 — Resume with difficulty-based independent checks

- User explicitly requests five difficulty levels and extensive appropriate subagent use. Highest: Backend integrity/storage/concurrency review (xhigh effort); high: Frontend/API review (high); medium: AC evidence audit (medium); low: root README R08-WEB-001 correction (low); lowest: evidence path/hash/format checks bundled with the audit and PM. Four disjoint subagent work scopes; main agent owns state reconciliation and environment restoration.
- Found completed ENV-P1-DB-001-08 independent ACCEPTED report despite the previous agent's final usage-limit error. Read the stored evidence rather than assuming the task produced no result. ENV is DONE/RESOLVED; historical authentication failure retained separately. No full Web acceptance inferred solely from environment closure.
- Found pre-existing REVIEW-WEB-001-08 independent CHANGES_REQUESTED report. Its independent 54 Backend / 23 Frontend / 2 API integration tests and build/typecheck evidence remains attributable to that review. Compared all 90 recorded source hashes: only the separately reviewed persistence helper changed. Remaining runtime sources match the snapshot; unnecessary broad reruns are avoided.
- Web follow-up review is IN_PROGRESS pending the current scoped review reports. Earlier reports remain historical and are not overwritten. No later-phase activation, commit or push from this reconciliation.


## 2026-09-12 PM final Web review reconciliation

Reviewer 08 final CHANGES_REQUESTED supersedes preliminary ENV full closure and in-progress review wording. R08-WEB-002 MAJOR remains OPEN despite parents[3] correction, pending preservation and post-fix corrected-root/restart verification assigned to Backend 03. R08-WEB-001 RESOLVED. AC07 FAIL; AC01-06/08-13 PASS with original evidence attribution. Historical 54/23/2 suites and build/typecheck retained as pre-fix evidence. ENV authentication/readiness/head and same-path restart successes retained; ENV OPEN and required completion gate retained. Phase 1 stays IN_PROGRESS; no later-phase promotion. See handoffs/REVIEW-WEB-001-rework-01.md for revised submission and Reviewer re-review gate.


## PM accepts R08-WEB-002 remediation for re-review

Backend03 remediation report and linked XML inspected: 55 Backend and final 2 cwd tests have zero failures/errors/skips; runtime and integration claims remain Owner attributed. BACKEND-WEB-001/ENV-P1-DB-001 READY_FOR_REVIEW, REVIEW-WEB-001 READY, prior CHANGES_REQUESTED retained in history. Designated Reviewer08 re-review requested via handoffs/R08-WEB-002-rereview-01.md. R08-WEB-002/ENV OPEN, AC07 FAIL and Phase1 IN_PROGRESS/CHANGES_REQUESTED retained until independent closure.


## 2026-09-13 PM accepts Phase 1

Designated Reviewer closure ACCEPTED verified against report, runtime JSON PASS (two configured references), and focused XML (2 tests, zero failures/errors/skips). R08-WEB-002 and ENV RESOLVED; all thirteen Web AC PASS. BACKEND/FRONTEND/REVIEW/ENV DONE with ACCEPTED review; Phase1 ACCEPTED after PM gate evaluation. Earlier findings/results and execution attribution retained. Overall project IN_PROGRESS; later-phase scheduling remains separate. No Commit/Push. Evidence and limits: handoffs/PHASE-1-acceptance-01.md.


## 2026-09-13 PM Phase2 activation

Rechecked current Phase1 ACCEPTED, 13 Web PASS, completed implementation/review/environment tasks and resolved issues. Phase2 IN_PROGRESS for contract/preparation, all four AC NOT_RUN. Reuse UPLOAD-001; add contract, Backend, preparation, compatibility and independent review work with explicit gates. Receipt/fingerprint/lease/fencing contract must be independently accepted before parallel Backend/uploader implementation. Existing task titled 리뷰 confirmed by role/content despite old cwd; first require safe current-root access. PM exclusively owns state/decisions/phase plan and coordinates shared-file claims. Per-unit model requests recorded; actual application unverified until confirmed. Preserve Phase1 and user changes. See handoffs/PHASE-2-activation-01.md. No Commit/Push.


## 2026-09-13 PM preparation acceptance and scoped Frontend allocation

Frontend and Backend preparation DONE/PM preparation accepted. Add FRONTEND-UPLOAD-001 BLOCKED from evidenced manual/response type coupling and missing capture detail display; contract approval remains prerequisite. Link 7 Frontend/12 Backend questions to Architect, including receipt-aware reconciliation and consistent fenced object ownership. All Phase2 AC NOT_RUN; no Phase1 task reopened. See handoffs/PHASE-2-frontend-backend-prep-01.md.


PM accepted PREP-UPLOAD-001 consultation and delivered all three preparation reports to Architect02. Shared file requests remain pending contract/PM claim. Owner restricted Python failure and PM file-exists/approved-execution success are distinct observations; missing interpreter not established, owner correction requested. Phase2 AC remain NOT_RUN and all implementation gates remain blocked.


## 2026-09-16 PM resume

Reconciled Reviewer current-root preparation as DONE from existing artifacts. Existing incomplete contract draft retained; Architect resume dispatched with Astra/medium to finish exact submission before independent review. All Phase2 product AC NOT_RUN and implementation gates unchanged. See handoffs/PHASE-2-resume-01.md.


## 2026-09-16 Contract revision1 submitted

PM matched four submitted SHA256 values and accepted review entry, not design/product approval. ARCH-UPLOAD-001 READY_FOR_REVIEW; REVIEW-ARCH-UPLOAD-001 READY for independent Sol/high review. Atomic file/OS-lock queue replaces proposed SQLite in submitted contract; all substantive decisions require independent assessment. Implementation/shared-file claims and four AC gates remain pending. See handoffs/REVIEW-ARCH-UPLOAD-001-01.md.


## 2026-09-20 role-based resumption

Prior 429 failures and unavailable interrupted support agents verified; resumed five existing role tasks once with explicit difficulty/model/subagent instructions. Two bounded support agents restarted for unfinished audits, avoiding duplicate owner implementation. New delivery is not completion; contract/implementation gates retained. See handoffs/PHASE-2-role-resume-20260920-01.md.


## 2026-09-22 resume checkpoint

Five existing roles resumed once; 02/03/06/08 fresh execution observed, 04 delivery only. Contract review still pending; no product activation or AC promotion. Mobile proposal has separate exclusive ownership. See .orchestration/handoffs/PHASE-2-role-resume-20260922-01.md. Previous support audits are advisory; no active support execution inferred.


## 2026-09-25 bounded origin-binding rework

Recovered designated Reviewer revision1 CHANGES_REQUESTED judgment; report publication pending. Architect returned to CHANGES_REQUESTED with origin-only revision2 scope after report preservation. Implementation remains blocked; all Phase2 AC NOT_RUN. See .orchestration/handoffs/PHASE-2-rework-20260925-01.md.


2026-09-25 progress: Backend03 and uploader06 execution plans now submitted and SHA256 recorded in state/tasks. Packaging uses unified distribution preserving base dependencies; pyproject single editor03 after gate, agent lock/input editor06. JCS disposable dependency spike authorized for03 now (medium Sol/medium); no duplicate06 investigation. Reviewer file publication is waiting on scoped write approval, not a new analysis blocker. No product acceptance or test PASS inferred.


Final Reviewer report preserved and PM hash-verified: .orchestration/reports/REVIEW-ARCH-UPLOAD-001-08.md, SHA256 aec4661e79e7a8628e4df49c6aba3659ce9d4fa78d7752eabc88e230de290c53. R08-P2-ARCH-001 MAJOR OPEN; revision1 CHANGES_REQUESTED. Write approval is no longer the blocker. Architect revision2 edits activated; independent re-review waits for exact revision2 submission. Product gates unchanged.


Revision2 owner submission received and all four exact hashes verified. ARCH-UPLOAD-001 READY_FOR_REVIEW; REVIEW-ARCH-UPLOAD-001 READY for focused independent closure of R08-P2-ARCH-001. Revision1 CHANGES_REQUESTED preserved; required finding still OPEN. Product implementation BLOCKED and all Phase2 AC NOT_RUN. Owner static checks are not independent or product PASS.


JCS spike report hash verified; select rfc8785==0.1.4 and reviewed universal wheel 520d690b448ecf0703691c76e1a34a24ddcd4fc5bc41d589cb7c58ec651bcd48 for both implementations after contract gate. Owner03 disposable Windows/Linux results are owner evidence, not PM/product tests. Strict parser remains separate. Temporary harness was removed, so production fixtures/exact executable commands must be retained and rerun; full unified installs/JSONB/parity remain NOT_RUN. No product or shared-file edit activated.


## 2026-09-25 revision2 accepted / implementation activated

Independent review ACCEPTED, R08-P2-ARCH-001 RESOLVED. Backend03/uploader06/Frontend04 READY with exact exclusive claims in .orchestration/handoffs/PHASE-2-implementation-20260925-01.md. Review history preserved; four product AC NOT_RUN. Web verification/implementation review wait for matching submissions.
