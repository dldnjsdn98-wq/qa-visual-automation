# REVIEW-WEB-001 rework / PM 01 / 2026-09-12

- Task / next owner: BACKEND-WEB-001 and ENV-P1-DB-001 / 03; subsequent independent re-review / 08.
- Disposition: CHANGES_REQUESTED; required MAJOR R08-WEB-002 OPEN. R08-WEB-001 RESOLVED.
- Evidence: ../reports/REVIEW-WEB-001-08.md, ../reports/review.md and REVIEW-WEB-001-08.md. PM read these and inspected local.py; parents[3] is present. PM did not execute product tests or restart services.
- AC-WEB-07 FAIL; AC-WEB-01 through 06 and 08 through 13 PASS according to attributed Reviewer matrix. Phase 1 IN_PROGRESS, review_result CHANGES_REQUESTED. Preserve initial 54 Backend / 23 Frontend / 2 actual API integration / build / typecheck PASS as pre-correction evidence.
- ENV issue OPEN, full closure withheld. Preserve dated DB authentication/readiness/head and same-path restart successes and historical failures; current blocker is storage preservation and corrected-root verification.
- Changed scope: TASKS.yaml, ACCEPTANCE.yaml, PROJECT_STATE.yaml, DECISIONS.md, this PM handoff and dated supersession note in original PM activation handoff. Contracts unchanged. Branch / commit: null / null.

## Backend 03 assignment and resubmission gate

1. Acknowledge the existing parents[3] correction. Identify DB-referenced misplaced objects and preserve originals and references through an explicit safe migration or compatibility procedure. Do not blindly move, overwrite or delete outside-root data, reset volumes or reseed records.
2. Verify default relative storage is repository-relative and independent of cwd from multiple working directories; retain absolute override coverage. Run affected storage/upload/actual API integration checks after the correction. Report exact commands, dates and results separately from old suites.
3. Record sanitized actual configured adapter root and storage mapping. Verify original IDs, image bytes/SHA-256, metadata and exact Unicode before/after preservation and ordinary restart using the same configured DB. Verify documented local/Compose alignment or supported transition, with executed versus inferred evidence distinguished.
4. Submit updated own report/handoff with changed files, preservation procedure, results and limitations; request READY_FOR_REVIEW through PM. Send the revised evidence to Reviewer 08 for independent affected-scope re-review and notify PM. Do not claim the finding or ENV closed solely from the arithmetic fix or old PASS results.

## Reviewer 08 gate

Re-review only after revised Owner submission. Independently verify R08-WEB-002 and ENV closure evidence, preserve source attribution, and return ACCEPTED or CHANGES_REQUESTED plus AC07 recommendation to PM. PM owns final state reconciliation. No new Frontend product work or Architecture redesign; no later-phase promotion or role 10 activation, Commit or Push.
