# PHASE 3 — OCR / Verification

Status: Planned / Not Implemented Yet.
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


