# PHASE 3 — OCR / Verification

Status: IN_PROGRESS — revision1 contract independently ACCEPTED;03/05/04 implementation READY under exclusive PM claims. Runtime qualification and product acceptance pending.
Entry gate: PHASE 2 ACCEPTED.
Flow: Screenshot → OCR text / bounding box / confidence → Expected Strings → exact / normalized / fuzzy → result.

## Required acceptance
- AC-P3-01: Multilingual OCR preserves text, bounding boxes and confidence
- AC-P3-02: Exact, normalized and fuzzy matching tested on multilingual fixtures
- AC-P3-03: Config thresholds: >=95 PASS, >=85 and <95 REVIEW, <85 FAIL
- AC-P3-04: Verification results visible in Web with repeatable evidence

## Exit and evidence
Owner runs relevant automated and integration checks, records commands and artifacts in handoff,
and submits READY_FOR_REVIEW. Reviewer 08 independently returns ACCEPTED or CHANGES_REQUESTED.
PM updates .orchestration/ACCEPTANCE.yaml and task state. Every required criterion must PASS.



## Current assignments

See `.orchestration/handoffs/PHASE-3-activation-01.md` for scope, dependency, completion and verification requirements. Existing02/05/03/04/08 role tasks received instructions; delivery is not completion.

| Task | Owner | State | Requested model |
| --- | --- | --- | --- |
| ARCH-OCR-001 |02|DONE / ACCEPTED|gpt-6-astra / medium|
| PREP-OCR-001 |05|DONE|gpt-5.6-sol / high|
| PREP-BACKEND-OCR-001 |03|DONE|gpt-5.6-sol / medium|
| PREP-FRONTEND-OCR-001 |04|DONE|gpt-5.6-sol / medium|
| REVIEW-OCR-PREP-001 |08|DONE|gpt-5.6-sol / medium|
| REVIEW-ARCH-OCR-001 |08|DONE / ACCEPTED|gpt-5.6-sol / high|
| OCR-001 / BACKEND-OCR-001 |05 /03|READY: qualification/integration gates apply|gpt-5.6-sol / high|
| FRONTEND-OCR-001 |04|READY: live integration after03/05|gpt-5.6-sol / medium|
| REVIEW-OCR-001 |08|BLOCKED: final matching submissions|gpt-5.6-sol / high|

AC-P3-01..04 remain NOT_RUN. Actual model unverified. Phase2 acceptance and all historical evidence preserved; Phase4 not activated.

## Latest checkpoint: revision2 runtime resume

Revision2 exact478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44 independently ACCEPTED. PM verified Reviewer report/handoff and latest Backend owner submission.03/05 runtime qualification/integration resumed; both new execution turns observed. Frontend implementation READY_FOR_REVIEW; FRONTEND-OCR-VERIFY-001 remains BLOCKED pending matching qualified Backend/OCR. Final REVIEW-OCR-001 remains BLOCKED. All Phase3 AC NOT_RUN. Owner Backend167/default189/focused41 are owner evidence, not PM reruns. See `.orchestration/handoffs/PHASE-3-runtime-resume-01.md`.
