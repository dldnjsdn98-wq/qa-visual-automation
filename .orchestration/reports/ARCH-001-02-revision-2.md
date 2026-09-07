# ARCH-001 revision 2 evidence — owner 02

## Scope and initial state

TASKS.yaml was CHANGES_REQUESTED with R08-ARCH-001, not the older READY_FOR_REVIEW shown in historical owner handoff/PROJECT_STATE. Read reviewer report/handoff and retained existing domain/cardinality/unique/API/storage design. The required rework is Unicode persistence alignment; Backend module map and Frontend integration details were also made explicit. No product feature implementation or original reviewer evidence was changed.

## Finding response

R08-ARCH-001 (MAJOR): author correction submitted, independent closure pending. api-contract.md now rejects U+0000/residual surrogates across request strings, recursive metadata keys/values and filenames before sanitization. It requires strict UTF-8 decoding, safe 422 paths, no publication/application DB write on rejection and exact preservation of accepted scalars. domain-model.md requires UTF8 and the same validation; data-flow.md places it before publication; overview.md assigns validation/transaction/module ownership. No DB redesign.

Official references checked: [PostgreSQL 17 JSON types](https://www.postgresql.org/docs/17/datatype-json.html) and [character types](https://www.postgresql.org/docs/17/datatype-character.html). Text/JSONB storage restrictions motivate the accepted Unicode subset. The reference checker demonstrates local decoding/driver compatibility only, not live PostgreSQL JSONB behavior.

## Reproducible checks

Run at project root, using README-compatible interpreter selection:

```powershell
.\.venv\Scripts\python.exe docs/architecture/check_unicode_contract.py
.\.venv\Scripts\python.exe docs/architecture/check_contract.py
```

Unicode fixtures cover 18 cases: 12 rejections (NUL, high/low/reversed surrogate, metadata nested key/value, filename, name/description) and 6 positive preservation cases (paired/literal supplementary, Japanese/Korean/combining/whitespace, empty text, supplementary metadata key/value, literal backslash-u sequence). Two raw malformed UTF-8 inputs are separately rejected. Accepted strings are round-tripped through strict UTF-8/JSON and locally adapted with psycopg; original NUL failure is reproduced. Error-path expectations are safe and checked.

The document checker is a revision-submission check, not a permanent post-acceptance CI gate. It now preserves and checks prior CHANGES_REQUESTED evidence and allows pending PM acceptance reconciliation (NOT_RUN or FAIL), instead of incorrectly claiming no independent review has occurred.

## Coverage retained / completed

| User requirement | Contract location |
| --- | --- |
| Seven core domains, String ID, relationships, PostgreSQL | domain-model.md tables, identity and FK/index sections |
| Screenshot core/future metadata | domain-model.md extensible metadata; api-contract.md ScreenshotUpload/Screenshot |
| Backend module structure | overview.md target module map, dependency/transaction ownership and delivery sequence |
| Storage abstraction and failure recovery | data-flow.md operation table and failure matrix |
| Phase 1 endpoints, requests/responses, validation/errors | api-contract.md common policy, model/route tables, upload/Expected Strings |
| Frontend implementation contract | overview.md typed client/dependencies/CORS and api-contract.md Unicode/field behavior |
| Phase 2/3/4 extensions | domain-model.md future additions and data-flow.md agent/processing/visual execution |
| Decisions / complete handoff | DECISIONS.md ADR-ARCH-010..012; handoffs/architect.md |

## Acceptance limits

Independent re-review NOT_RUN. Prior Reviewer disposition remains CHANGES_REQUESTED / AC-ARCH-01 FAIL in review.md; acceptance YAML awaits PM reconciliation. Product validators, HTTP statuses/no-side-effect assertions, PostgreSQL round trips/migrations, storage failures and Frontend build/behavior are NOT_RUN because this is architecture rework. No duplicate DB connection attempt or service startup was needed; prior review already documented unavailable DB connectivity. Static/reference checks are not AC-WEB acceptance. No external messages, sub-agents, commits or push.

## Actual command results

```text
check_unicode_contract.py:
PASS: 18 Unicode fixtures (6 accepted, 12 rejected); safe error paths
PASS: accepted scalar preservation/driver adaptation; NUL rejection reproduced; 2 malformed UTF-8 cases
NOT_RUN: production validators, HTTP status/side-effect tests, PostgreSQL text/JSONB round trips

check_contract.py:
PASS: 4 documents; 3 local links; 4 JSON examples
PASS: example scopes, missing translation semantics, hash shape and content URL
PASS: orchestration YAML, preserved review history, re-review state and unchanged downstream gates
NOT_RUN: independent AC-ARCH-01 re-review, product API/DB/storage/Frontend tests
```

Both commands exited 0. These are owner evidence, not independent finding closure. The current revision retains CHANGES_REQUESTED in task review_history, sets current review_result=null/review_requested=true, and leaves Backend/Frontend/Web Review BLOCKED. Earlier architecture evidence and Reviewer reports are retained as history.
