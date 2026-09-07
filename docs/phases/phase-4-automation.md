# PHASE 4 — Game Visual Automation

Status: Planned / Not Implemented Yet.
Entry gate: PHASE 3 ACCEPTED.
Flow: Device → Screenshot → Anchors → State → Transition → Action → Screenshot → Validation.

## Required acceptance
- AC-P4-01: ADB screenshot and allowed inputs only; no game internals
- AC-P4-02: Required / optional / forbidden anchors and uncertain states handled
- AC-P4-03: Bounded polling validates next state; fixed sleep is not core control
- AC-P4-04: Checkpoint files enter captures/pending and existing uploader handles delivery

## Exit and evidence
Owner runs relevant automated and integration checks, records commands and artifacts in handoff,
and submits READY_FOR_REVIEW. Reviewer 08 independently returns ACCEPTED or CHANGES_REQUESTED.
PM updates .orchestration/ACCEPTANCE.yaml and task state. Every required criterion must PASS.


