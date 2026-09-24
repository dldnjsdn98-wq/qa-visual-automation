# Phase2 implementation activation / PM01 / 2026-09-25

P2-UPLOAD-v1 revision2 independently ACCEPTED by Reviewer08. PM verified both review artifacts and all four current contract hashes. R08-P2-ARCH-001 RESOLVED; revision1 history preserved. Phase1 remains ACCEPTED. Phase2 IN_PROGRESS, AC-P2-01..04 NOT_RUN.

BACKEND-UPLOAD-001 (03, High Sol/high), UPLOAD-001 (06, High Sol/high), FRONTEND-UPLOAD-001 (04, Medium Sol/medium) are READY now. Persistent identity/concurrency/crash risks require High or higher work units; use Highest Astra/medium if contract surprises/data-loss risk/repeated reasoning failures justify escalation. Routine docs/state must use lower difficulty. Actual models unverified. Environment/permissions/429 are not model defects.

Goals/done: 03 implements additive receipts, scoped identity/JCS, transactional fencing/recovery, manual preservation; submit migration/fresh+populated/PostgreSQL concurrency/fault evidence.06 implements atomic queue, immutable binding/OS lock, marker-last publication, bounded retry/strict ACK/recovery/CLI; submit real process-crash/original preservation/F25-F30 evidence.04 separates manual writes from expanded reads and renders safe full multilingual metadata; submit scoped regression tests/build. Each parent integrates disjoint subagents and sends its own report/handoff for PM READY_FOR_REVIEW, never self-accepts.

File claims:

- 03: backend/, tests/backend/, pyproject.toml. Backend receipt/migration/service/storage/reconcile tests and Backend lock; sole pyproject editor preserving base/dev deps, adding rfc8785>=0.1.4,<0.2, agent extra httpx>=0.28,<1, package discovery agent*. No global pytest scope change.

- 06: agent/screenshot_upload/, tests/upload/, agent/__init__.py. Uploader production/tests including requirements.lock and requirements.in; agent/__init__.py only if needed for packaging, preserve existing content. No common agent/__main__.py. Full base+agent/test lock. Own Backend-response-loss integration tests under tests/upload/integration.

- 04: frontend/lib/types.ts, frontend/lib/api.ts, frontend/components/screenshots.tsx, frontend/app/globals.css, frontend/tests/api.test.ts, frontend/tests/components.test.tsx. Manual request/read response separation and safe full CaptureMetadata/version/non-null ID detail display; preserve user changes. No source filter/retry/receipt UI.

03 sends 06 the completed pyproject patch/lock constraints before06 generates its final unified lock. Both use rfc8785==0.1.4 reviewed wheel hash520d690b448ecf0703691c76e1a34a24ddcd4fc5bc41d589cb7c58ec651bcd48. No packaging split, custom serializer or unreviewed upgrade. Strict raw JSON parser separate. Preserve reproducible fixtures and exact commands; spike temporary harness is not product verification.

README uploader section is06 conditional only after implemented/verified behavior. Root tests/integration, shared generated docs/OpenAPI, root config outside pyproject, contract files and nonallocated files require a new scoped PM claim before editing. Mobile proposal remains separately owned. Backend service/global DB/start-stop mutations must be coordinated to avoid integration conflicts; use disposable synthetic environments for destructive/crash tests. Never use real captures or mutate user DB for tests.

FRONTEND-UPLOAD-VERIFY-001 and REVIEW-UPLOAD-001 remain BLOCKED until matching submissions. Real agent->Backend->DB/storage->Web and response-loss cross-process evidence required; mock-only success insufficient. Preserve manual upload/original bytes/Unicode. No Phase2 ACCEPTED before all four AC PASS and designated independent implementation review ACCEPTED. IP checks excluded; no Commit/Push. Preserve all existing user/owner edits, inspect file diffs before patching. PM alone edits state/acceptance/decisions.
