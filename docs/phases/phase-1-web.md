# PHASE 1 — Web Review System

Status: Planned / Not Implemented Yet.
Entry gate: ARCH-001 ACCEPTED before Backend/Frontend implementation.
Flow: Project → Build → Locale → Category → Situation → String → Manual Screenshot → Detail → Expected Strings.

## Required acceptance
- AC-WEB-01: Project CRUD
- AC-WEB-02: Build CRUD
- AC-WEB-03: Locale management
- AC-WEB-04: Category management
- AC-WEB-05: Situation management
- AC-WEB-06: String ID based multilingual string management
- AC-WEB-07: Manual screenshot upload
- AC-WEB-08: Screenshot metadata
- AC-WEB-09: Expected Strings display
- AC-WEB-10: Project / Build / Locale / Situation filters
- AC-WEB-11: Fresh database migrations reproduce domain schema
- AC-WEB-12: Backend tests PASS
- AC-WEB-13: Frontend build and behavior tests PASS

## Exit and evidence
Owner runs relevant automated and integration checks, records commands and artifacts in handoff,
and submits READY_FOR_REVIEW. Reviewer 08 independently returns ACCEPTED or CHANGES_REQUESTED.
PM updates .orchestration/ACCEPTANCE.yaml and task state. Every required criterion must PASS.
OCR and game automation are explicitly excluded from Phase 1.

