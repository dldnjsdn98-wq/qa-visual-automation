# 2026-09-12 consolidated environment note

The R08-WEB-001 documentation resolution below stands. Any reference below to ENV acceptance describes the earlier scoped conclusion, now superseded for full closure by the R08-WEB-002 storage-root finding in [the final review](REVIEW-WEB-001-08.md). Dated DB/authentication/readback PASS evidence is preserved; full Web/ENV acceptance is withheld.

# REVIEW-WEB-001 documentation recheck — 08

Date: 2026-09-12 KST. Scope: Phase 1 root-README correction for R08-WEB-001 only. No later-phase review, product implementation, orchestration-state change, service operation, database/storage action, test execution, commit, or push was performed.

## Result

**RESOLVED — R08-WEB-001 documentation finding.** The existing uncommitted root `README.md` correction is sufficient. This recheck made no further README edit because the current content agrees with the owner runbooks and the checked scripts; further wording changes would be unsupported expansion of the assigned correction.

The prior independent evidence remains attributed to its original reviewers and execution dates:

| Evidence | Retained result and boundary |
| --- | --- |
| `REVIEW-WEB-001-08.md` | Windows Backend 54 PASS; Frontend 23 PASS; typecheck/build PASS; isolated TypeScript client/API integration 2 PASS. These are historical independent execution results, not executions by this documentation recheck or a complete Phase 1 acceptance. |
| `ENV-P1-DB-001-08.md` | ACCEPTED for the documented environment-closure scope only. Its report retains migration/restart/browser observations as owner evidence where stated and does not accept the full Web review, every AC-WEB criterion, or Phase 1. |
| `REVIEW-WEB-001-08-source-manifest.json` | 90-file review snapshot. The prior comparison found only `backend/tools/verify_default_persistence.py` different; its verify-mode correction is separately described in the retained review evidence. This documentation recheck did not recalculate or replace the manifest. |

## Root README verification

| Root README area | Compared sources | Resolution |
| --- | --- | --- |
| Current product status and scope | `backend/README.md`, `frontend/README.md`, current API/UI source paths | Correctly identifies implemented Phase 1 catalog CRUD, multilingual strings, manual screenshot upload/detail, Expected Strings, and filters; it keeps OCR and automation as later work. |
| Installation and local startup | `backend/README.md`, `scripts/setup-env.ps1`, `backend/Dockerfile`, `docker-compose.yml` | Correctly uses the hash-locked Backend install followed by editable no-dependency install; `setup-env.ps1` preserves an existing `.env`; Compose/local port and host descriptions match the configuration. |
| Frontend startup and API origin | `frontend/README.md`, `frontend/package.json`, `frontend/Dockerfile`, `frontend/lib/api.ts` | Correctly directs users to `npm.cmd ci` and `npm.cmd run dev` from `frontend/`, identifies port 3001, and refers origin changes/rebuild behavior to the Frontend runbook. |
| Migration guidance | `backend/README.md`, `backend/migrations/versions/0002_phase1_domain_phase1_domain.py`, `backend/Dockerfile` | Correctly names `0002_phase1_domain`, distinguishes disposable migration round-trips from user databases, and states that the Backend container upgrades to head on startup. |
| Test/build guidance | `backend/README.md`, `frontend/README.md`, `backend/tools/run_postgres_tests.py`, `tests/frontend/run_integration.py`, `frontend/package.json` | Correctly lists the isolated Backend runner, isolated Frontend integration runner, `pip check`, Compose configuration, and Frontend unit/component, build, and typecheck commands. It accurately states that the isolated runners avoid migration/reset of the configured user database and retain the runbooks for their additional conditions. |
| Historical versus current claims | `REVIEW-WEB-001-08.md`, `ENV-P1-DB-001-08.md` | Correctly labels the 2026-09-05 Bootstrap table as historical and limits the later PASS/ACCEPTED evidence to its stated scope. It does not promote the documented evidence to overall Phase 1 acceptance. |

The reviewed root links target the current Backend and Frontend runbooks and the retained review reports. The root README's existing change is intentionally preserved as the prior agent's work; it is not relabeled as a change made by this recheck.

## Files changed by this task

- `.orchestration/reports/REVIEW-WEB-001-docs-08.md` — this finding-resolution record.

`README.md` was inspected but not modified by this task. No tests were run because this was a documentation-only recheck and the retained independent suite evidence already covers the product criteria.
