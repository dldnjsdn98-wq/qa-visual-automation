# BACKEND-UPLOAD-001 owner report

Date: 2026-09-25 KST. Contract: P2-UPLOAD-v1 document revision 2. Status requested: READY_FOR_REVIEW.

Implemented additive `0003_phase2_upload_receipts`, project-scoped permanent upload receipts, RFC 8785 fingerprinting with strict agent JSON parsing, lease/generation/token fencing, atomic Screenshot+receipt completion, first/replay/conflict/in-progress HTTP behavior, receipt-aware storage reconciliation, and unchanged manual upload semantics. No historical migration was edited and no commit or push was made.

Key behavior:

- Agent identity is `(project_id, client_upload_id)`; first completion returns 201/false, completed replay 200/true with the same resource, conflicting intent 409, and active/fenced work 409 with a positive database-lease-derived Retry-After.
- Receipt operations use fresh READ COMMITTED sessions, PostgreSQL `clock_timestamp()`, bounded lock/statement/transaction waits, 60-second leases, generation+UUIDv4 token fences, and fresh candidate object keys.
- Finalization inserts Screenshot and marks the receipt COMPLETED in one transaction. Agent workers never delete published objects. Ambiguous transaction recovery uses a fresh primary locked read and first-insert unique-key arbitration.
- Strict agent parsing rejects duplicate keys, malformed Unicode, nonfinite/overflow/underflow numbers, and unsafe integral binary64 values. Exact F23 canonical bytes are 582 bytes with SHA-256 `a5a4938ef3aa25cc06bb29711005b0aeb1ecb0f13e898983fb9d2b0faaa009b6`.
- Reconciliation protects every Screenshot key and every PROCESSING candidate, verifies referenced bytes, marks abandoned work FAILED only in apply mode under exclusivity, requires age >24h, and performs a fresh primary reference recheck before exact deletion.
- Packaging adds runtime `rfc8785>=0.1.4,<0.2`, exact locked `rfc8785==0.1.4` wheel hash `520d690b448ecf0703691c76e1a34a24ddcd4fc5bc41d589cb7c58ec651bcd48`, the agent httpx extra, and unified backend/agent discovery.

Validation performed against the isolated PostgreSQL 17 container and a clean Linux Python 3.12 image:

- `docker build --pull=false -f backend/Dockerfile.test -t qa-backend-upload-final:local .`: PASS; hash-locked install, project wheel build, and `pip check` passed.
- `docker run ... qa-backend-upload-final:local python -m pytest tests/backend -q -p no:cacheprovider --tb=short`: PASS, 94 passed, 2 third-party deprecation warnings.
- The suite includes fresh migration and populated 0002→0003 preservation, SQLAlchemy/Alembic metadata parity, receipt constraints, JCS vectors, manual regressions, HTTP headers/schema, first/replay/conflict/hash non-dedup, real concurrent active-owner arbitration, fresh fenced-owner replay/lease-delay handling, storage exact verification, reconcile protection/inventory failure, and packaging checks.
- AST parsing of backend/tests and `git diff --check -- backend tests/backend pyproject.toml`: PASS.

Subagent difficulty routing requested by the user: 최상 Astra/medium for transaction/fencing and an independent orchestration audit; 상 Sol/high for storage/reconcile; 중 Sol/medium for HTTP/schema; 하 Terra/high for migration/models; 최하 Luna/high for packaging checks. Requested models are recorded; actual applied models remain unverified.

NOT_RUN / review limits:

- A native Windows full Backend suite was not available because the local venv points to a missing interpreter; the clean Linux image is the executable product evidence here.
- Separate-process Backend response-loss/restart and actual agent→Backend→DB/storage→Web verification are owned jointly with uploader06 and remain for its integration run.
- No user database, real capture, commit, push, IP-connectivity check, README, PM YAML, architecture contract, or root integration file was modified.

Please perform independent implementation review. This owner report requests READY_FOR_REVIEW and does not self-accept BACKEND-UPLOAD-001 or any Phase 2 acceptance criterion.
