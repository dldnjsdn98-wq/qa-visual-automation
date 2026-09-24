# 2026-09-13 — designated remediation re-review ACCEPTED

**REVIEW-WEB-001 REVIEW: ACCEPTED. R08-WEB-002 RESOLVED; ENV-P1-DB-001 full closure ACCEPTED; AC-WEB-07 PASS recommended.** The corrected actual adapter root, all configured DB references, old-source preservation, new publication at the corrected root, original/new ID/hash/metadata/Unicode readback and final two-cwd regression were independently verified. Owner browser/restart/full-suite evidence remains explicitly attributed. No required issue remains; R08-WEB-001 stays RESOLVED.

[Final closure evidence and limits](R08-WEB-002-closure-08.md) · [PM handoff](../handoffs/R08-WEB-002-closure-08.md). PM owns final YAML/Phase reconciliation. The CHANGES_REQUESTED entries below are preserved history, superseded by this designated re-review; they do not describe the current disposition.

---

# Historical 2026-09-12 — REVIEW-WEB-001 independent review

Latest working-tree note: `local.py:11` changed to `parents[3]` at 12:22 KST, correcting root arithmetic. Existing-object preservation and affected regression/configured-root readback submission remain pending; the original finding below describes the reviewed pre-correction submission. Current review remains CHANGES_REQUESTED pending that evidence.

**REVIEW-WEB-001 REVIEW: CHANGES_REQUESTED**. MAJOR R08-WEB-002: default relative storage resolves outside the repository (`backend/app/storage/local.py:11,18`). Exact original synthetic fixture/hash is present under the parent directory's storage and absent from repository storage. Backend 03 must correct resolution while preserving existing objects and DB references, then verify configured-root persistence and affected regressions. MINOR R08-WEB-001 is RESOLVED following the README correction; one required product issue remains.

Independent 54 Backend / 23 Frontend / 2 actual API integration tests and build/typecheck PASS. Configured DB/readiness/head, post-restart original readback and default browser filters/detail/Expected Strings also have successful dated evidence. They do not establish correct storage placement; the earlier ENV-only closure conclusion is superseded, with its successful observations preserved. AC-WEB-07 FAIL; other AC-WEB criteria PASS recommended in the detailed matrix. Phase 1 remains IN_PROGRESS, full acceptance withheld.

Details, severity/files/reproduction/owners/retest conditions: [final review](REVIEW-WEB-001-08.md). Environment correction: [ENV review](ENV-P1-DB-001-08.md). PM actions: [Reviewer handoff](../handoffs/REVIEW-WEB-001-08.md). PM owns final YAML task/AC/Phase reconciliation; Reviewer made no product edits or Commit/Push. Historical architecture approval below remains valid and is not replaced by this Web result.

---

# 2026-09-06 — Revision 2 independent approval reconfirmed

**ARCH-001 REVIEW: ACCEPTED**. Explicit user-requested reinspection completed by Reviewer 08. Actual repository state at entry was already ARCH-001 ACCEPTED / AC-ARCH-01 PASS / R08-ARCH-001 RESOLVED, not the pending state quoted in the request. Those correct states are retained; no duplicate submission or fabricated state transition was added.

Read the requested orchestration files, PM readiness report, reviewer history, architect handoff and actual four architecture documents again. The old readiness report and owner handoff record the pre-approval submission; they do not override the current acceptance YAML or independent review. The original MAJOR finding below was compared directly with the current policy, not just document existence or owner test claims.

- **All original mandatory concerns resolved:** api-contract.md:14,25,27,41,145 specifies NUL/residual-surrogate rejection, recursive metadata key/value handling, create/patch and pre-sanitization filename validation, safe 422 errors and rejection before publication/application writes. domain-model.md:9,48 and data-flow.md:35,44 agree. Valid supplementary scalars, multilingual/combining sequences, whitespace, empty translations and literal escape text retain their required semantics. No unresolved part of R08-ARCH-001 remains at architecture level.
- **Regression review:** Project/Build/Locale/Category/Situation/StringEntry/Screenshot, supporting StringKey and expected mappings retain scoped relationships, uniqueness and immutable identity. Expected Strings still resolve the current Build/Locale catalog with ordered mappings and explicit missing/empty values. Request/response, PATCH/null, filters, errors, content origin, transaction ownership and Storage failure boundaries are mutually consistent. No new mandatory architecture blocker or implementation-blocking Backend/Frontend ambiguity found.
- **Extensions:** Phase 2 persistent upload receipts and queue ownership; Phase 3 separate OCR/verification records and frozen inputs; Phase 4 reserved metadata and Black Box boundaries remain sufficient extension points for their later tasks. They do not require implementation before Phase 1 begins.
- **Decision:** objective specification inspection plus executed reference checks supports retaining AC-ARCH-01 PASS and ARCH-001 ACCEPTED. Backend/Frontend architecture dependency is satisfied and their BLOCKED states may be cleared by Thread 01's coordinated promotion. Unresolved CRITICAL 0 / MAJOR 0; no new MINOR/RECOMMENDATION issue raised.

Executed from repository root on this reinspection:

```powershell
.\.venv\Scripts\python.exe docs/architecture/check_unicode_contract.py
.\.venv\Scripts\python.exe .orchestration/reports/check_arch_accepted.py
```

- PASS: 18 Unicode fixtures (6 accepted / 12 rejected), safe paths, scalar preservation/local driver adaptation, original NUL rejection and 2 malformed UTF-8 inputs.
- PASS: 4 documents, 3 local links, 4 parsed JSON examples; scope/missing/content consistency; accepted revision, closed issue, acceptance and preserved history/evidence links.
- The new read-only reviewer evidence script checks the actual accepted state. Owner check_contract.py was inspected but not rerun: it intentionally asserts a pending READY_FOR_REVIEW submission and would fail on approved state. No owner checker was modified and no state was reset to force a PASS.
- NOT_RUN: production API/DB round trips/migrations/storage side effects and Frontend build/behavior. Architecture reference checks do not prove runtime behavior. Git status still shows the untracked project tree; no commit or product edit performed.

Current reviewed source fingerprints (SHA-256, captured by the reviewer evidence script):

| Document | SHA-256 |
| --- | --- |
| overview.md | 6bf8c23796417aa9c06c3984b8347c9a7e917b3010626387713c6bfa6394a075 |
| domain-model.md | cb503fe4af4c2afccc33ba9f7d879a50ba69a0f145c21e754f125637e7e73341 |
| api-contract.md | b2fa671a17206f7484e8433e793bcf8489bfd101f68b3978e51bf255205d4ad6 |
| data-flow.md | c31f8c1c9c4e878c439f12c05a44bc5cfdf199cc27806fe19b054b4b3e3818d8 |

Thread 01 next action: promote BACKEND-WEB-001 and FRONTEND-WEB-001 together to READY, activate 03/04, set PHASE 1 Web MVP Implementation and give both these approved contracts. Preserve REVIEW-WEB-001's requirement for both implementation submissions and all later phase gates. Architecture reapproval is no longer needed to remove the implementation block. Today's changes are limited to this report, the read-only reviewer evidence script and own handoff; approval YAML already contains the requested final states.

---

# ARCH-001 revision 2 — Independent re-review / Reviewer 08

- Date: 2026-09-05. **ARCH-001 REVIEW: ACCEPTED**.
- Existing finding **R08-ARCH-001: RESOLVED** in revision 2. Original severity MAJOR retained in history; unresolved CRITICAL 0 / MAJOR 0. No new MINOR or RECOMMENDATION issue raised.
- **AC-ARCH-01: PASS**; **ARCH-001 status/review_result: ACCEPTED**. This approves architecture for Phase 1 implementation, not implemented web behavior or any phase completion.
- Activation verified from repository: revision 2 READY_FOR_REVIEW, review_requested=true, required AC-ARCH-01 carrying previous FAIL. The user's explicit re-review request supersedes the historical PM note to wait for web submissions; no architecture/web circular gate remains.
- Directly inspected every requested state/document/handoff/readiness file, original review below, revision 2 owner report, both checker sources and all Unicode fixtures. Compared original mandatory finding and previously reviewed contracts in this task with the current four documents; owner and PM conclusions were not treated as approval evidence.
- Git inspection: existing main with untracked project files; HEAD does not exist (`git rev-parse --verify HEAD`: Needed a single revision). There is no committed revision-1/revision-2 diff to claim. Comparison is against retained reviewer evidence and the earlier document contents available in this task. Reviewer branch / commit: null / null.

## R08-ARCH-001 closure comparison

File references are repository-relative and line numbers refer to the reviewed revision 2.

| Original mandatory concern | Revision 2 evidence / verification | Disposition |
| --- | --- | --- |
| Contract accepts NUL text that cannot persist; correct all persisted string inputs | api-contract.md:14,25 and domain-model.md:9 exclude U+0000 and residual surrogates, require UTF8 and cover every create/patch field. Reference rejection cases include text, description and name. | RESOLVED |
| Recursive JSONB metadata keys and values need the same policy | api-contract.md:25,27 and domain-model.md:48 include unknown/reserved keys, nested objects and array values; Unicode precedes byte-size calculation. Nested NUL and surrogate fixtures reject at the specified paths. | RESOLVED |
| Invalid scalar sequences need explicit rejection, without rejecting valid supplementary characters | api-contract.md:25 distinguishes residual surrogates from valid decoded pairs; strict UTF-8 required. High/low/reversed cases reject; paired/literal emoji pass with scalar length 1. Two malformed UTF-8 probes reject. | RESOLVED |
| Reject before publication/DB writes; never silently strip or repair | api-contract.md:27, data-flow.md:35,44 and overview.md:58 explicitly prohibit publication/application writes, allow only private parser staging with discard, and assign production no-side-effect tests. api-contract.md:145 validates the full filename before sanitization. | RESOLVED at architecture level; production side-effect tests remain Backend work |
| Stable 422 VALIDATION_ERROR and safe field paths | api-contract.md:27 specifies body.text, metadata paths, invalid-key container paths and fixed messages; rejected payloads/unsafe keys excluded from serialization/logging. Reference error-path assertions pass. | RESOLVED at architecture level; HTTP handler tests remain Backend work |
| Preserve valid multilingual/combining/whitespace/empty text | api-contract.md:14,25,31–41 and domain-model.md:9 preserve exact accepted scalars; reference cases pass JSON/UTF-8 preservation and driver adaptation. Empty text remains a present translation; literal backslash-u text is not confused with NUL. | RESOLVED |
| State positive/negative boundary tests and ownership | api-contract.md:41 explicitly requires Create/Patch, ScreenshotUpload, representative fields, nested keys, no-write/no-publish assertions and PostgreSQL readback; overview.md:58,72 assigns shared Backend validation and Frontend scalar counting. | RESOLVED; no requirement to implement future web tests inside ARCH-001 |

## Regression and implementation-readiness review

| Area | Independent conclusion |
| --- | --- |
| Domains and relationships | Project/Build/Locale/Category/Situation/StringEntry/Screenshot and supporting StringKey/expected mapping remain defined with cardinality, immutable ownership, uniqueness, composite project FKs and restrictive deletes. Screenshot Category/Situation agreement is enforced. No blocking regression identified. |
| string_id / multilingual catalogs | Semantic identity stays on project StringKey; entries remain unique by Build/Locale/key. Unicode refinement changes admissible invalid input, not identity or normalization. No implicit build/locale fallback. |
| Expected Strings | Complete capped ordered Build/Situation mapping, Build+Locale LEFT JOIN, current-catalog label and missing versus empty response remain consistent. Shared resolver adds implementation clarity without changing API semantics. |
| API / request-response / errors | CRUD route inventory, types, omission/null PATCH, pagination, scoped references, 404/409/422 and upload/content responses are sufficient for both owners to implement. Unicode field paths and validation order agree with storage flow. No mandatory consumer ambiguity found. |
| Screenshot metadata / Storage | Immutable relational core and bounded extensible JSONB retained; metadata size/depth clarified. Private stage/publish/read/stat/delete/list interface, original bytes, short DB commit, compensation, uncertain-commit retention and exclusive reconciliation remain consistent. |
| Backend/Frontend boundary | Service-owned commit and no dependency/repository commit preserve transaction responsibility. Typed client, Backend-origin content URLs, browser multipart boundary, exposed headers, scalar counting, null handling, dependent reset and stale-response handling are specified. OpenAPI reconciliation is a delivery obligation, not an architecture blocker. |
| Migration / environment | Unchanged baseline plus additive domain migration, real PostgreSQL checks and UTF8 prerequisite are explicit. Existing entrypoints/relative interpreter commands retained; no large product refactor is required by the correction. |
| Phase 2 extensibility | Stable upload ID/receipt/fingerprint/lease extensions and durable queue ownership retained; no hash-only deduplication or premature Phase 1 idempotency promise. |
| Phase 3 extensibility | Separate versioned OCR regions/results and verification snapshots preserve boxes/confidence, expected inputs and processing-versus-quality status. Unicode input validation does not normalize comparison text. |
| Phase 4 extensibility / Black Box | Reserved run/device/resolution/scenario/checkpoint/state metadata remains additive. Automation writes pending captures for the uploader; ScreenState/Action/Transition/Scenario separation and Black Box restrictions retained. |

No additional mandatory architecture omission or regression was found. Known scoped limits (mutable current catalog, restrictive parent deletion, unauthenticated loopback deployment and manual ambiguous retries) remain explicit design decisions, not newly introduced blockers. Historical owner documents saying review pending/NOT_RUN describe their submission time; current acceptance is recorded here and in orchestration state.

## Independently executed verification

Commands run from repository root before changing approval state:

```powershell
.\.venv\Scripts\python.exe docs/architecture/check_contract.py
.\.venv\Scripts\python.exe docs/architecture/check_unicode_contract.py
```

- **PASS:** 4 architecture documents, 3 local links, 4 JSON examples; scope/missing-text/content consistency and revision-submission state/history checks.
- **PASS:** 18 Unicode fixtures: 6 accepted, 12 rejected; safe error paths; accepted scalar preservation/local psycopg adaptation; original NUL rejection; 2 malformed UTF-8 cases.
- Both checker sources and fixture expectations inspected. These are documentation/reference checks; fixture names containing create/patch do not mean HTTP requests were executed.
- **NOT_RUN:** production validators, HTTP statuses/no-write/no-publish assertions, PostgreSQL text/JSONB round trips/migrations, storage fault tests and Frontend build/behavior. They belong to the still-blocked web implementation tasks; no product acceptance is inferred. No DB connection retry or service mutation performed in this re-review.
- `check_contract.py` intentionally requires a pending submission (READY_FOR_REVIEW/null result). Its pre-approval PASS is preserved; it is not a post-acceptance CI gate. Its printed independent-review NOT_RUN is a submission message, superseded by this independent review. Reviewer did not rewrite owner scripts to make them assert approval.

## Approval and Thread 01 handoff

The user explicitly authorized acceptance/task updates on successful independent re-review. Recorded R08-ARCH-001 RESOLVED, AC-ARCH-01 PASS and ARCH-001 ACCEPTED, with revision/history/evidence. ACCEPTED is directly supported by TASKS.yaml dependency_rules; no additional DONE transition is needed to satisfy the architecture dependency. Previous review text is preserved verbatim below.

Thread 01 should now promote BACKEND-WEB-001 and FRONTEND-WEB-001 to READY together, activate roles 03/04 and set the milestone to PHASE 1 Web MVP Implementation using the same approved revision 2 documents. Reviewer leaves those tasks BLOCKED only pending PM promotion, with corrected blocker descriptions; architecture itself is no longer blocking. Keep REVIEW-WEB-001 blocked until both implementations are READY_FOR_REVIEW with evidence. Do not pass AC-WEB criteria or accept Phase 1 from architecture approval. Later phases and role 10 remain gated. No external messages, product edits, commit or push were performed.

---

# Historical revision 1 review — preserved; superseded by revision 2 approval above

# Independent review — Senior Reviewer 08

- Date: 2026-09-05
- Task: ARCH-001; implementation owner: 02 Architect; reviewer: 08.
- Result: **CHANGES_REQUESTED**. CRITICAL 0 / MAJOR 1 / MINOR 0 / RECOMMENDATION 0.
- Activation: ARCH-001 was READY_FOR_REVIEW, requested review, and references required AC-ARCH-01. Owner handoff and evidence were present.
- Scope: architecture acceptance only. REVIEW-WEB-001 remains BLOCKED; no Phase 1 functional or later-phase acceptance is claimed.
- Reviewed inputs: reviewer prompt; PROJECT_STATE.yaml, TASKS.yaml, ACCEPTANCE.yaml, DECISIONS.md; all handoff Markdown files; owner report; four architecture documents and check_contract.py; README, Phase 1 plan, Compose, .env.example, .gitignore, pyproject.toml and Backend connection/settings code. Secret .env contents were not displayed.
- Branch / commit for reviewer work: null / null. Existing main has no reviewer commit. No product code changed.

## Required finding R08-ARCH-001

- Severity: **MAJOR**
- Task ID: **ARCH-001**
- File: `docs/architecture/api-contract.md:12`; related `docs/architecture/domain-model.md:44` and screenshot JSONB column at line 17.
- 문제: Text accepts 0–10000 Unicode characters without excluding U+0000 and promises preservation. Open metadata accepts JSON strings, including escaped NUL in keys/values, without the corresponding PostgreSQL restrictions. These are contract-valid inputs which the chosen text/JSONB storage cannot persist. An implementation cannot satisfy both acceptance of these values and the storage contract; silently stripping characters would also violate preservation. This affects translation create/update and screenshot metadata, so the shared validation contract must be corrected before implementation approval. This is a design defect, not an observed HTTP 500 in an implemented business API.
- 근거: Local Python JSON decoding accepts `"hello\u0000world"`; length is within the Text limit. `{"note":"hello\u0000world"}` serializes to 28 UTF-8 bytes, below the metadata limit, and satisfies the stated depth/key bounds. The installed psycopg StrDumper rejects the text with `DataError: PostgreSQL text fields cannot contain NUL (0x00) bytes`. PostgreSQL 17 explicitly rejects `\u0000` in JSONB and requires correctly paired Unicode surrogates: [official JSON types documentation](https://www.postgresql.org/docs/17/datatype-json.html). The character-type restriction is also documented in [official character types documentation](https://www.postgresql.org/docs/17/datatype-character.html).
- 재현 방법: From project-root PowerShell, execute the block below. It needs no database and writes no data. For later integration confirmation, submit the same text through StringEntryCreate/Patch using valid scoped IDs, and submit a valid PNG with `metadata.metadata={"note":"hello\u0000world"}`. Also cover nested values, object keys and unpaired surrogates. Business endpoints are not implemented yet; these HTTP cases are NOT_RUN.
- 권장 수정: Architect should define accepted Unicode consistently across persisted text fields and recursive metadata keys/values. Reject U+0000 and invalid Unicode scalar sequences before storage publication/DB writes with 422 VALIDATION_ERROR and an appropriate field path; preserve valid multilingual text, whitespace, normalization and empty translations. Specify positive cases for supplementary-plane characters and negative cases for escaped NUL/unpaired surrogates. Backend should implement these as boundary tests after architecture approval. No redesign of tables is needed.

```powershell
@'
import json
from psycopg.types.string import StrDumper
text_value = json.loads('"hello\\u0000world"')
metadata = json.loads('{"note":"hello\\u0000world"}')
print('Text length allowed by contract:', len(text_value) <= 10000)
print('Metadata UTF-8 bytes:', len(json.dumps(metadata, ensure_ascii=False).encode('utf-8')))
try:
    StrDumper(str).dump(text_value)
    print('psycopg adaptation: ACCEPTED')
except Exception as exc:
    print('psycopg adaptation:', type(exc).__name__, str(exc))
'@ | .\.venv\Scripts\python.exe -
```

Observed output:

```text
Text length allowed by contract: True
Metadata UTF-8 bytes: 28
psycopg adaptation: DataError PostgreSQL text fields cannot contain NUL (0x00) bytes
```

## Coverage and evidence

| Review area | Architecture inspection result |
| --- | --- |
| Domain / DB relationships | Cardinality, project composite FKs, Category/Situation agreement, uniqueness and restrictive deletes are specified. No additional blocking design issue found. Actual DB constraints NOT_RUN. |
| String ID / Locale / Category / Situation | Stable project StringKey, Build/Locale translation tuple, locale subset and immutable identity are explicit. Unicode validation blocked by R08-ARCH-001. |
| Screenshot metadata / API validation | Server-derived identity/hash/dimensions, bounded upload and error envelope are explicit. Recursive metadata Unicode acceptance blocked by R08-ARCH-001. |
| Expected Strings | Build/Situation mapping, locale-specific LEFT JOIN, missing versus empty, ordered replacement and current-catalog semantics are explicit. |
| Storage / migration | Durable publication before short DB insert, ambiguous-commit retention, exclusive reconciliation, no-overwrite/path restrictions, unchanged baseline and real PostgreSQL migration test obligations are specified. Implementation/fault tests NOT_RUN. |
| Frontend API / filter / error state | Backend-origin content URLs, AND filters, dependent reset, stale responses, missing strings, 204 handling and ambiguous upload failures are specified. Build/behavior NOT_RUN for this architecture review. |
| Common / environment / README | Project-relative executable commands, loopback deployment, placeholder secret, ignored runtime data and explicit dependency-lock follow-up reviewed. README accurately labels product features as unimplemented. Quick-start runtime/build commands were not rerun; bootstrap evidence is historical. |
| Phase 2–6 boundaries | Queue ownership/original preservation, future idempotency receipts, OCR snapshots, separate visual state/action/transition/scenario and Black Box invariants reviewed as extension design only. All phase execution tests NOT_RUN. |

Executed checks:

1. `.\.venv\Scripts\python.exe docs/architecture/check_contract.py` — **PASS before reviewer state update**: 4 documents, 3 links, 4 JSON examples; example consistency and submission-state gates. Its printed `NOT_RUN: independent AC-ARCH-01 review` describes the owner's submission, not this completed review. This checker intentionally asserts READY_FOR_REVIEW/null review_result; it is not valid as a post-review gate and was not modified.
2. Inline Unicode reproduction above — **PASS (defect reproduced)**; this is not a product acceptance PASS.
3. Read-only DB probe via existing `backend.app.db.engine`, intending `SET TRANSACTION READ ONLY` and `SELECT CAST(:value AS text/jsonb)` for ordinary/NUL/invalid-surrogate cases — **NOT_RUN SQL cases**: connection failed with `psycopg.errors.ConnectionTimeout: connection timeout expired` before any SELECT. No data/schema change and no DB assertion claimed. JSONB finding is supported by official PostgreSQL documentation, not an executed local JSONB test.
4. `git status --short`, `git branch --show-current` — inspected pre-existing untracked project tree/main. No baseline commit diff is available; findings are against the submitted files, not attributed to an invented commit.
5. Product Backend tests, migration tests, Frontend build/behavior and README service startup — **NOT_RUN**: no web implementation is eligible for review and architecture-only changes cannot establish AC-WEB-01..13.

## State and handoff

- TASKS.yaml ARCH-001 status/review_result updated to CHANGES_REQUESTED under the user's explicit instruction; blocker and reviewer evidence attached. Owner evidence retained.
- AC-ARCH-01 review disposition: **FAIL**, pending PM recording in ACCEPTANCE.yaml (PM-owned). Existing NOT_RUN there must not be interpreted as PASS. Report is the independent acceptance evidence.
- PM should reconcile PROJECT_STATE.yaml's historical REVIEW_REQUESTED milestone and acceptance entry. Backend/Frontend/REVIEW-WEB remain blocked; no phase or downstream promotion was made.
- Owner 02 fixes the contract and supplies refreshed evidence, then resubmits READY_FOR_REVIEW through the defined coordination flow. Reviewer 08 is **WAITING** until that activation condition is met.
- Re-review: confirm R08-ARCH-001 is resolved consistently in API/domain contracts and test obligations; inspect revised evidence. Functional runtime checks remain owned by subsequent web tasks.
