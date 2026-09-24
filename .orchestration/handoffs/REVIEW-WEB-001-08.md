# 2026-09-13 final handoff supersedes the rework request below

**REVIEW-WEB-001 ACCEPTED; R08-WEB-002 RESOLVED; ENV closure ACCEPTED; AC07 PASS recommended.** Use [designated closure handoff](R08-WEB-002-closure-08.md) for current PM actions. The following CHANGES_REQUESTED handoff is retained history.

# Historical REVIEW-WEB-001 / Reviewer 08 → PM 01 / 2026-09-12

- Task / owner: REVIEW-WEB-001 / 08. Activated by both Owner submissions and `REVIEW-WEB-001-01.md`; independent review completed.
- Result: **CHANGES_REQUESTED**. CRITICAL 0; MAJOR product issue R08-WEB-002 OPEN; MINOR documentation issue R08-WEB-001 RESOLVED after current README recheck. Architecture approval remains unchanged.
- Changed files: own reports `REVIEW-WEB-001-08.md`, `ENV-P1-DB-001-08.md` (dated correction retaining prior evidence), reviewer source manifest, reviewer Windows XML, consolidated `reports/review.md`, this handoff and supersession notes in scoped Reviewer reports. No product/config/credentials/state YAML changes, Commit or Push. Branch/commit: null/null.
- Contract changes: none. The requested Backend fix implements the already approved repository-relative storage contract.

## Required Backend action

Late update at 12:22 KST: the working-tree adapter now uses `parents[3]`. Acknowledge that scoped code correction; request the outstanding existing-object preservation and regression/configured-root readback evidence below. No completed revised Owner handoff was found at this cutoff. The original finding describes the pre-correction submission; prior passing suites predate this line change.

R08-WEB-002: `backend/app/storage/local.py:11,18` resolves default relative storage using `parents[4]`, producing `C:\Dev\storage\local` instead of the repository's `storage/local`. The original synthetic fixture exists outside the repository with the expected hash and is absent at the contracted path. Compose mounts the repository storage tree, so the two documented deployment modes diverge. This is a product defect, independent of DB authentication.

Assign Owner 03 a scoped correction with preservation of existing objects and DB references. Do not merely change the root and strand existing images; do not reset/delete user volumes or blindly move/overwrite outside-root data. Require default-relative/cwd-independent and absolute-override regression coverage, affected storage/upload/API integration checks, actual resolved-root evidence and same ID/hash/metadata/Unicode readback after the preservation procedure and restart. Verify documented local/Compose storage alignment. Owner resubmits READY_FOR_REVIEW; Reviewer rechecks the affected scope.

R08-WEB-001: root README scope/migration/test correction is RESOLVED; see `REVIEW-WEB-001-docs-08.md`. Preserve that completed documentation work. No independent Frontend product rework is requested.

## Evidence and limits

- Independent PASS: 54 Backend Windows/PostgreSQL tests (`reviewer-backend-windows.xml`), 23 Frontend behavior tests, typecheck/build, 2 actual ApiClient/FastAPI/PostgreSQL integration tests. Exact commands and dates: [review report](../reports/REVIEW-WEB-001-08.md).
- Default environment: authenticated DB/readiness/head, original object hash/Unicode/metadata and post-restart readback PASS on 09-09. Owner executed migration/controlled restart and original default browser upload; Reviewer independently corroborated configured DB/API readback and default browser filters/detail/image/Expected Strings. Isolated tests did not replace these checks.
- Those successes used the wrong local storage root. The preliminary ENV08 full-closure conclusion is superseded by its dated correction; keep valid authentication/readback results and historical failures. Full closure remains pending corrected-root preservation verification.
- NOT_RUN: local-to-Compose failure reproduction, corrected-root migration/restart (fix absent), a fresh full independent browser creation/upload workflow, independent Linux/container suite and clean reinstall/Docker Frontend build. Do not convert owner evidence into Reviewer executions. These limits and nonrequired future checks are separated in the report.

## PM state reconciliation requested

1. REVIEW-WEB-001: record CHANGES_REQUESTED, attach this handoff and final review evidence; reconcile stale READY/null dispatch wording to completed review awaiting Backend rework.
2. BACKEND-WEB-001: CHANGES_REQUESTED for R08-WEB-002; owner 03. Preserve original submitted tests/history. FRONTEND-WEB-001 keeps its submission/evidence; no new Frontend blocker is inferred.
3. AC-WEB-07: FAIL (default manual upload violates storage placement contract). AC-WEB-01–06 and 08–13: PASS recommended from the explicitly attributed evidence matrix. Passing test criteria do not imply overall acceptance.
4. ENV-P1-DB-001: full-closure review CHANGES_REQUESTED, issue OPEN with R08-WEB-002 preservation/root revalidation as the remaining condition. Keep the completion gate; update obsolete current-tense authentication-failure claims to the dated successful revalidation. Do not erase the original failure.
5. Phase 1 stays IN_PROGRESS with review_result CHANGES_REQUESTED; no later-phase promotion or role 10 activation. Apply final state/AC updates under PM authority in the activation handoff.

Difficulty/model allocation used for final checks: 최상 Astra medium — confirmed blocker/current submission; 상 Sol high — environment conclusions; 중 Sol medium — AC evidence; 하 Terra high — report consistency; 최하 Luna high — final artifact references. Primary Reviewer owns the consolidated decision.
