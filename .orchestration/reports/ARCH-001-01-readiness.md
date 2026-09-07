# PM readiness audit — ARCH-001 revision 2

## Result

BLOCKED for final acceptance/promotion. The specification is sufficiently detailed for Phase 1 implementation planning, and no additional mandatory architecture omission was identified. The remaining blocker is acceptance evidence: reviewer finding R08-ARCH-001 has author corrections but no independent revision 2 ACCEPTED/closure. This report does not impersonate role 08 or close its finding.

## Directly inspected evidence

- TASKS.yaml, PROJECT_STATE.yaml, ACCEPTANCE.yaml, DECISIONS.md and handoffs/architect.md.
- docs/architecture/overview.md, domain-model.md, api-contract.md and data-flow.md, plus both architecture checker scripts and their fixture execution.
- reports/review.md and reports/ARCH-001-02-revision-2.md.

| Required area | PM inspection |
| --- | --- |
| Domain and relationships | Stable StringKey; build/locale translations; scoped composite FKs, unique constraints and restrictive deletion specified. |
| API implementation contract | CRUD models/routes, defaults, omission/null, pagination, filters, errors and content-origin handling specified. Generated OpenAPI is a Backend deliverable, not a missing prerequisite. |
| Expected Strings | Ordered build/situation mapping and shared locale resolver; current catalog and missing/empty distinction specified. |
| Screenshot/storage | Metadata bounds, original preservation, validation limits, Storage operations, durable publication, ambiguous commit retention and exclusive reconciliation specified. |
| Migration/module ownership | Preserve baseline, add domain migration, real PostgreSQL checks, service transaction ownership and dependency reproducibility assigned to Backend. |
| R08-ARCH-001 correction | API/domain/storage/overview consistently reject NUL/residual surrogates before publication/write and preserve valid scalars; positive/negative examples and production test obligations supplied. Independent closure absent. |
| Frontend and scope | Typed client, multipart encoding, selection/cache reset, stale responses and error behavior specified. Later phases and Black Box boundaries preserved. |

## Commands actually executed

```powershell
.\.venv\Scripts\python.exe docs/architecture/check_contract.py
.\.venv\Scripts\python.exe docs/architecture/check_unicode_contract.py
```

- Contract checker PASS: four documents, three local links, four JSON examples, example scope/content and pending-review state checks.
- Unicode checker PASS: 18 fixtures (6 accepted, 12 rejected), safe error paths, scalar preservation/local driver adaptation, original NUL rejection and two malformed UTF-8 cases.
- Product HTTP/DB/migrations/storage tests and Frontend build/behavior NOT_RUN: architecture-only PM review. Independent re-review NOT_RUN; no reviewer dispatch. No product acceptance marked PASS.

## Required closure

1. Independently assess revision 2 against R08-ARCH-001: recursive values/keys, create/patch, filename before sanitization, safe 422 paths, no publication/write, and supplementary/combining/empty text preservation. Architecture review need not wait for future product tests.
2. Attach explicit revision 2 ACCEPTED and finding closure evidence before AC-ARCH-01 becomes PASS and ARCH-001 becomes DONE.
3. Then promote both web tasks to READY together, activate roles 03/04 and set PHASE 1 Web MVP Implementation. Keep web acceptance unpassed until actual execution/review.

The user's current instruction holds role 08 until both web tasks are READY_FOR_REVIEW. With the existing architecture independent-review prerequisite this creates a gate conflict; PM has recorded it and has not dispatched review or waived acceptance. No new Architect design rework is requested by this inspection alone.

## Conditional handoff to Thread 03 Backend

Start only after PM records ARCH-001 DONE with AC-ARCH-01 PASS and BACKEND-WEB-001 READY. Read docs/prompts/03_backend.md, the same four revision 2 architecture documents and handoffs/architect.md. Prioritize models and additive migration with real PostgreSQL constraint checks; shared Unicode/error validation and scoped CRUD; StringKey/translations/Expected Strings; Storage/upload/content and fault/reconciliation tests. Export OpenAPI early for Frontend reconciliation; deliver dependency reproducibility and executed evidence. Do not claim frontend criteria independently.

## Conditional handoff to Thread 04 Frontend

Start only after the same architecture gate and FRONTEND-WEB-001 READY. Read docs/prompts/04_frontend.md and the same revision 2 documents/handoff. Prioritize one typed API client, common Page/Error and Backend-origin content resolution; Project and scoped metadata editors; build/locale translations and expected-key assignment; upload/list/filter/detail. Test dependent resets, stale responses, missing versus empty translations, omitted/null PATCH, Unicode scalar limits and ambiguous uploads. Reconcile mock types with generated OpenAPI and supply build/typecheck/behavior evidence.

Branch / commit: null / null for PM work. No product edits, external messages, commits or push.
