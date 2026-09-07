# PHASE 2 — Screenshot Automatic Upload

Status: Planned / Not Implemented Yet.
Entry gate: PHASE 1 ACCEPTED.
Flow: captures/pending → Upload Agent → Backend → Storage → DB → Web.

## Required acceptance
- AC-P2-01: Durable offline queue preserves original screenshots
- AC-P2-02: Retry with backoff and logged terminal failures
- AC-P2-03: Idempotency and duplicate prevention survive process restart
- AC-P2-04: Uploaded screenshots and metadata appear in Web

## Exit and evidence
Owner runs relevant automated and integration checks, records commands and artifacts in handoff,
and submits READY_FOR_REVIEW. Reviewer 08 independently returns ACCEPTED or CHANGES_REQUESTED.
PM updates .orchestration/ACCEPTANCE.yaml and task state. Every required criterion must PASS.


