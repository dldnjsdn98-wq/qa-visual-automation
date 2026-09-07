# PHASE 5 — Record & Replay

Status: Planned / Not Implemented Yet.
Entry gate: PHASE 4 ACCEPTED.
Flow: Before screenshot → User input → After screenshot → Recording → Replay.

## Required acceptance
- AC-P5-01: Persist tap/swipe/keyevent, timestamp, before/after and detected states
- AC-P5-02: Replay validates state and records failures
- AC-P5-03: Generate reviewable transition/template candidates and scenario drafts

## Exit and evidence
Owner runs relevant automated and integration checks, records commands and artifacts in handoff,
and submits READY_FOR_REVIEW. Reviewer 08 independently returns ACCEPTED or CHANGES_REQUESTED.
PM updates .orchestration/ACCEPTANCE.yaml and task state. Every required criterion must PASS.


