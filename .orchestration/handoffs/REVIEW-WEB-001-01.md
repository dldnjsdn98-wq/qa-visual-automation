# Web review activation / PM 01 / 2026-09-08

- Task / owner: REVIEW-WEB-001 / 08 READY; ENV-P1-DB-001 / 03 READY for environment remediation, issue OPEN.
- Activation: Backend and Frontend both READY_FOR_REVIEW, review_requested true and review_result null. The old blocker waiting for both submissions is satisfied and removed. Review execution has not been claimed or dispatched by a task message.
- Changed files: PROJECT_STATE.yaml, TASKS.yaml, DECISIONS.md and this handoff. ACCEPTANCE.yaml unchanged: Phase 1 IN_PROGRESS, AC-WEB-01..13 NOT_RUN.
- Contracts: no architecture/API change. Product remains at Phase 1; roles 05/06/07/09 waiting; role 10 not activated.
- Branch / commit: null / null for PM action; no commit/push.

## Submission evidence examined

Backend canonical handoff handoffs/backend.md and task handoff BACKEND-WEB-001-03.md link reports/BACKEND-WEB-001-03.md, backend-windows.xml and backend-linux.txt. Windows XML inspected using PowerShell XML parsing: tests=54, failures=0, errors=0, skipped=0. Linux log ends with 54 passed, 2 warnings. Report includes clean Windows/Linux install, migration/constraint/storage/Unicode checks and actual Frontend-client integration 2 PASS.

Frontend canonical handoff handoffs/frontend.md and FRONTEND-WEB-001-04.md link reports/FRONTEND-WEB-001-04.md. Owner reports 23 behavior tests, typecheck/build, two isolated PostgreSQL/FastAPI/client integration tests and real desktop browser critical flow. Default authenticated SELECT 1 is explicitly FAIL/environment; default persistent full flow is NOT_RUN. Additional NOT_RUN scope includes Docker Frontend build, mobile/exhaustive accessibility and Backend-only checks. These limitations go to Reviewer, not fabricated PASS or automatic new mandatory scope.

PM read both reports and handoffs, state/decisions, Linux log and Windows XML; did not rerun product suites, probe DB credentials, perform browser review or certify submitted claims independently. One local tooling probe (`.\.venv\Scripts\python.exe -c "import yaml; print('YAML runtime available')"`) failed to launch the interpreter in this PM execution context. This is a separate tooling observation, not PostgreSQL authentication evidence or invalidation of prior owner PASS results. Thread 03 should confirm its executable runtime before revalidation; PM used PowerShell for read-only evidence inspection.

## ENV-P1-DB-001 — required environment issue

- Owner: 03 Backend; PM coordinates; Reviewer 08 verifies closure.
- State: OPEN, READY to remediate. No currently identified external dependency prevents starting diagnosis. This is a required completion blocker, not a reason to keep the already-submitted review entry blocked.
- Observed in owner reports: default qa_visual authentication at 127.0.0.1:5433 fails; configured persistent deployment cannot be certified. Root cause is not yet proven: target instance, environment overrides and persistent DB role credentials must be checked. Isolated test credentials work; that does not establish default credentials work.
- Impact: normal startup/readiness, default migration and persistent Web flow remain unverified. Related acceptance coverage AC-WEB-11/12/13 and the AC-WEB-01..10 live flow must be reviewed in the correct environment. No AC status is promoted here.

## Thread 03 instructions and closure evidence

1. Confirm current project runtime, intended PostgreSQL service/port/database/user, root .env versus process/Compose overrides and actual effective configuration. Compare credentials privately; never print secrets, dump full environment or place them in reports. Do not assume environment POSTGRES_PASSWORD changes an already-initialized DB role.
2. Align application configuration with the intended existing database credentials within authorized access. Preserve existing databases, volumes, screenshots and unrelated services. If obtaining credentials or altering the existing DB account requires unavailable operator access, record that exact blocker and requested action; do not reset/delete volumes or silently replace the persistent database with a test instance.
3. In the corrected DEFAULT configuration, capture sanitized authenticated SELECT 1 success and target identity, run supported additive migration upgrade/current-head verification without downgrading user data, then start the normal API and verify /ready returns 200 using the configured DB. /health alone is insufficient.
4. Validate the actual normal Frontend/API route through catalog creation, multilingual strings/expected mapping, synthetic screenshot upload, list/filter/detail/content/Expected Strings. Use uniquely named synthetic records, preserve real data, and verify these records/image remain readable after an ordinary application restart using the same DB and storage.
5. Re-run affected checks according to actual changes. Configuration-only fixes need configured-environment connection/migration/readiness/flow evidence; code, migration or contract edits need relevant regression suites and updated exports/consumer coordination. Isolated suite PASS remains useful regression evidence but cannot close this environment issue alone.
6. `tests/frontend/run_integration.py` always creates a temporary DB and overrides API session/storage; even without --isolated-postgres it does NOT certify the configured persistent app database/storage. Report its results separately from the normal deployment checks above.
7. Write own ENV-P1-DB-001-03 handoff/report with exact commands, sanitized results, changed files, remaining limitations and configuration context. Request independent closure. PM reconciles the open issue/failed probe only after Reviewer evidence; retain historical failure.

## Thread 08 instructions and review conditions

Start REVIEW-WEB-001 now from both owner submissions and approved revision 2. Independently inspect/reproduce AC-WEB-01..13 evidence, contract behavior, migrations/Unicode/storage/concurrency and Frontend real integration as appropriate. Attribute owner PASS versus your own runs and record FAIL/BLOCKED/NOT_RUN accurately. Architecture ACCEPTED is not web approval.

Review entry is READY because both submissions exist. ENV-P1-DB-001 remains a separate required final-acceptance blocker; review unaffected areas while Backend remedies it. If an individual configured-environment check cannot run, mark that check BLOCKED and link the environment issue. Do not report that either owner has not submitted. Keep new product findings separate from environment diagnosis; return required changes to the responsible owner.

Final review ACCEPTED requires required evidence including environment closure; unresolved default-deployment failure cannot be dismissed solely because isolated tests passed. Reviewer independently records ACCEPTED or CHANGES_REQUESTED and acceptance recommendations; PM updates final task/AC/Phase state. Phase stays IN_PROGRESS until every required AC PASS, required issue closure and independent review ACCEPTED. No later-phase activation from review entry.


## 2026-09-12 supersession / PM reconciliation

Historical activation and authentication observations above are retained. Review has completed CHANGES_REQUESTED; current state and Backend 03 assignment are in REVIEW-WEB-001-rework-01.md. Authentication/readiness and same-path restart subsequently PASS; ENV full closure is now withheld for R08-WEB-002 corrected-root preservation. AC07 FAIL; other Web ACs PASS per Reviewer matrix.
