# REVIEW-OCR-PREP-001 / Reviewer 08 preparation report

Date: 2026-09-25 KST  
Role: 08 Senior Reviewer  
Current source root: `C:\Dev\qa-visual-automation`  
Activation: `.orchestration/handoffs/PHASE-3-activation-01.md`

## Result

**PREPARATION COMPLETE; CONTRACT REVIEW AND IMPLEMENTATION REVIEW REMAIN BLOCKED.**

This report prepares the independent Phase 3 contract and implementation acceptance matrix. It is not an `ACCEPTED` or `CHANGES_REQUESTED` disposition, does not accept a contract, does not authorize implementation, and does not change any acceptance/task/phase state. AC-P3-01 through AC-P3-04 remain `NOT_RUN`.

`docs/architecture/phase-3-ocr-contract.md` does not yet exist. `REVIEW-ARCH-OCR-001` therefore remains blocked on the exact Architect 02 submission and PM activation. `OCR-001`, `BACKEND-OCR-001`, `FRONTEND-OCR-001`, and `REVIEW-OCR-001` remain blocked on independent contract acceptance, PM file ownership activation, matching owner submissions, and final PM review activation.

Phase 2 is confirmed `ACCEPTED` with all four Phase 2 criteria PASS. Its originals, durable upload identities, history, evidence, and accepted constraints are inputs that Phase 3 must preserve; they were not rerun by this preparation.

## Goal, scope, dependencies, claims, and completion

- Goal: prepare an independent AC-P3-01..04 risk map and a contract/implementation review checklist covering immutable expected snapshots, deterministic multilingual OCR and matching, durable fenced worker execution, append-only reruns, API/Web states, and repeatable actual evidence.
- In scope: read-only current requirements and source inspection; Reviewer-owned report/handoff only; bounded independent sidecar analysis with disjoint scopes.
- Out of scope: final contract decisions, feature implementation, dependency installation/model download, OCR execution, migrations, database/service/browser execution, Phase 4 device automation, mobile proposal changes, PM YAML edits, and acceptance.
- Satisfied dependency: Phase 2 accepted by `.orchestration/handoffs/PHASE-2-acceptance-01.md`.
- Current blocking dependency: exact `ARCH-OCR-001` contract submission does not exist yet.
- Future ownership proposals, not authorization: Architect 02 owns only `docs/architecture/phase-3-ocr-contract.md`; Owner 05 later owns `worker/ocr/`, `worker/verification/`, and `tests/ocr/`; Owner 03 later owns Backend, Backend tests and sole `pyproject.toml` dependency edits; Owner 04 later owns Frontend and Frontend tests. PM must issue exact claims after contract acceptance.
- Completion condition for this preparation: AC01-04 matrix, snapshot/matching/worker failure checklist, concrete Architect/PM inputs, verification commands/environments, risks, hashes, NOT_RUN limits, and model attribution are recorded below.

## Current baseline

- `worker/ocr/` and `worker/verification/` contain only `.gitkeep`; no Phase 3 implementation exists.
- `pyproject.toml` declares no PaddleOCR, PaddlePaddle, OpenCV, or RapidFuzz dependency. No installation or model availability is inferred.
- The current expected-string resolver returns `catalog_mode="current"`. Catalog edits can change the values later returned for an already uploaded screenshot. This live endpoint is not an immutable verification snapshot.
- Existing catalog semantics deliberately distinguish a missing translation (`text=null`, status missing) from a present empty translation (`text=""`, status present).
- Current screenshot persistence and API/Frontend types have no OCR job, OCR region, immutable expected snapshot, verification result, processing state, provenance, rerun history, or quality outcome.
- Existing high-level Phase 3 prose mentions OCR text, an axis-aligned box and generic confidence, but does not yet define polygon preservation, coordinate/orientation transforms, confidence provenance, normalization, scorer, candidate assignment, snapshot isolation, durable job protocol, error semantics, or exact API/Web resources.
- Current upload image dimensions are encoded-raster `Image.size` without EXIF transposition. The Phase 3 contract must explicitly choose the coordinate/orientation convention and cannot infer it from a future OCR engine.

## Independent acceptance preparation matrix

Every row is a future evidence requirement. Current status for each AC is `NOT_RUN`.

| AC | Exact contract-review requirements | Owner implementation evidence required | Reviewer 08 independent checks after PM activation | Current gate |
| --- | --- | --- | --- | --- |
| AC-P3-01 — multilingual OCR preserves text, bounding boxes and confidence | Versioned engine/runtime/model/dictionary/language provenance; supported-locale and no-fallback rules; raw Unicode preservation; original-raster coordinate/orientation/preprocessing transform; polygon/AABB and reading order; detection versus recognition confidence semantics and finite bounds | Actual pinned-engine inference on synthetic multilingual images; raw result JSON; source/model/font/image hashes; coordinate overlays/oracles; repeatability/tolerance statement; unsupported-language and malformed-engine-output evidence | Independently execute actual Korean/Japanese/Arabic/Latin and declared-language cases; inspect exact code points, polygons/AABB, edge/rotation/EXIF transforms, confidence 0/1 and rejection of nonfinite/out-of-range data; verify provenance against artifacts | Contract file absent; actual OCR NOT_RUN |
| AC-P3-02 — exact, normalized and fuzzy multilingual matching | Immutable ordered expected snapshot; exact raw equality; versioned normalization; pinned RapidFuzz scorer/version with `processor=None`; deterministic candidate generation, one-region consumption, split/duplicate/tie rules; missing/empty/no-observation/error semantics | Deterministic canned OCR/matcher vectors separate from actual engine; Korean/Japanese/Arabic/Latin, NFC/NFD Hangul/Latin, whitespace, fullwidth, confusables, duplicate text, multi-region and tie fixtures; persisted raw/normalized values and unrounded score | Independently run vectors and property/boundary cases; prove current catalog edits cannot change attempt A; prove same inputs/config produce same item assignments and result digest; confirm mocks are not used to claim AC-P3-01 | Contract file absent; matching NOT_RUN |
| AC-P3-03 — thresholds >=95 PASS, >=85 and <95 REVIEW, <85 FAIL | Numeric type/precision, finite range, comparison before display rounding, immutable threshold/config version, item aggregation and non-quality states | Injected score classifier tests at 100, 95, 94.999999, 85, 84.999999 and 0; aggregate cases; persisted config snapshot; no engine confidence substitution | Independently execute exact numeric boundaries and aggregation; verify quality exists only for successfully evaluated items/runs; inspect API and Web display rounding cannot alter stored status | Contract file absent; thresholds NOT_RUN |
| AC-P3-04 — verification results visible in Web with repeatable evidence | Exact enqueue/get/history/rerun API; job/processing/error versus quality schema; append-only history; snapshot and provenance exposure; stable pagination/order; public idempotency/concurrency semantics | API/component/type/build tests plus a current-source production Web run using fresh synthetic database/storage; queued, processing, succeeded, failed-processing, PASS/REVIEW/FAIL, missing, empty, no detections, multilingual, provenance and rerun-history views | Independently upload a synthetic multilingual screenshot through the accepted path, enqueue publicly, inspect browser status/result/history/original, cross-check IDs/hashes/snapshot/provenance/regions/scores and cleanup; component mocks alone are insufficient | Contract/API/UI absent; actual Web NOT_RUN |

## Required contract inputs to Architect 02

### 1. Immutable request, expected snapshot, and job identity

The final contract must define one atomic enqueue boundary. In one short PostgreSQL transaction, validate and lock the project-scoped Screenshot, bind its immutable original ID/hash/size/MIME/dimensions, materialize all ordered expected items, compute/store a canonical snapshot digest/version/count, insert the durable job, and commit. A worker must not claim an uncommitted or partial snapshot.

Snapshot rows must copy, not reference for later resolution:

- project/build/locale/situation and screenshot identity;
- position, `string_key_id`, `string_id`, optional `entry_id`;
- `translation_status` and exact expected text, preserving missing `null`, present empty `""`, whitespace and Unicode sequences;
- snapshot schema/canonicalization version and digest.

The contract must choose a public idempotency identity, such as a project-scoped client job UUID plus a canonical request fingerprint. Same identity/same request must replay the same job; same identity/different request must conflict. A lost enqueue response must not create a duplicate job or snapshot.

### 2. Durable job, lease, fencing, retry, and rerun

- Exhaustively define processing states and legal DB constraints. Recommended semantic states are `QUEUED`, `PROCESSING`, `SUCCEEDED`, and `FAILED`, with durable retry schedule/attempt history where needed.
- Use PostgreSQL `clock_timestamp()` after lock acquisition, strictly increasing attempt generation, fresh random token and bounded lease. Equality is expired.
- Every renew, retry schedule, failure write, result insert and terminal finalize must compare job/request fingerprint/generation/token and the contract's chosen lease-validity rule. Do not assume Phase 2 failure-write semantics transfer automatically; state the Phase 3 rule explicitly.
- Claim, renew and finalize transactions must contain no OCR, filesystem or network work and must have bounded lock/statement/transaction waits.
- Ambiguous claim/renew/finalize commit requires connection invalidation and resolution in a fresh primary transaction under lock. Never guess rollback, mark FAILED, delete evidence or create a replacement job from uncertainty.
- Final immutable OCR/verification rows and terminal job state must commit atomically with at most one terminal result for that job.
- Retry is another attempt of the same job and snapshot. Explicit rerun is a new job, new snapshot and new append-only result, linked with `rerun_of`/root and a deterministic run order. Prior jobs, attempts, snapshots and results never change.
- Screenshot originals/storage keys remain read-only. Missing or mismatched original bytes are an operational input failure; Phase 3 never overwrites, re-encodes or deletes the accepted original.
- Attempt tokens must never appear in public APIs or safe logs.

### 3. OCR provenance, language, coordinates, and confidence

Each attempt must persist exact, immutable provenance rather than a mutable alias:

- PaddleOCR and PaddlePaddle versions/builds; OpenCV version when used;
- CPU/GPU backend, precision, threads and deterministic settings;
- detector, recognizer and orientation/classifier model identifiers plus SHA-256 of every model and character dictionary;
- artifact source/license, canonical locale-to-language/model mapping, ordered mixed-script arbitration, inference/filter parameters, and unsupported-locale behavior;
- source screenshot hash and encoded-raster dimensions.

No silent fallback to English or another model is acceptable. Actual support must be established by Owner 05 and then represented exactly in the contract.

Each successful OCR result contains zero or more regions. Zero regions is successful OCR, not an engine error. Each non-empty region must preserve raw emitted Unicode, a canonical four-point polygon in original encoded-raster pixel-edge coordinates, deterministic vertex and reading order, a derived AABB under one rounding rule, recognition confidence and separately identified detection confidence (or explicit unavailable reason). Define origin, axes, edge bounds, EXIF policy and every inverse transform from resize/pad/crop/rotate/deskew. Reject malformed/blank regions, zero-area/self-intersecting polygons, nonfinite/out-of-range coordinates and confidences rather than clipping or repairing them silently. Engine confidence is not a calibrated probability and must remain distinct from match score.

### 4. Exact, normalized, fuzzy, assignment, and thresholds

Recommended conservative `normalized_v1` input for Architect decision: validate scalar Unicode, convert CRLF/CR to LF, then NFC. Do not implicitly use NFKC, case folding, punctuation/diacritic removal, transliteration, trimming or broad whitespace collapse; any additional behavior needs a separately versioned profile.

Required precedence:

1. raw code-point equality → `EXACT`, score 100;
2. versioned normalized equality → `NORMALIZED`, score 100;
3. otherwise one named, pinned RapidFuzz scorer with `processor=None` → `FUZZY`, unrounded score;
4. apply thresholds to full precision: score >=95 PASS; 85<=score<95 REVIEW; score<85 FAIL.

The contract must define candidate segmentation/concatenation, separators, reading order, one-region consumption, global versus greedy assignment, duplicate expected strings, equal-score tie-breaks and whether a region may satisfy multiple expected items. The same input must yield the same assignment independent of DB row order or process scheduling.

### 5. Missing, empty, no-detection, processing error, and quality

These cases must not collapse:

| Expected/OCR condition | Required semantic class |
| --- | --- |
| Missing expected translation (`text=null`) | `NOT_EVALUATED_MISSING_EXPECTED`; method/score/quality null |
| Present empty expected text (`text=""`) | Distinct `EMPTY_EXPECTED`; no automatic score-100 PASS without a separately defined spatial absence assertion |
| Present non-empty expected, successful OCR with zero regions | Quality FAIL, score 0, reason `NO_OBSERVED_TEXT` |
| Present non-empty expected with valid candidates | Exact/normalized/fuzzy evaluated result |
| OCR engine/model/preprocessing/input failure | Processing FAILED or `NOT_EVALUATED_OCR_ERROR`; no fabricated quality FAIL |
| Region blank/malformed or non-empty raw value normalizes empty | Adapter/algorithm error or explicit non-evaluated reason; never automatic PASS |

Job processing state and quality outcome must be mutually constrained. `PASS|REVIEW|FAIL` is available only after successful processing/evaluation. Queued, processing and failed jobs have quality null. API transport failure is distinct from a persisted processing failure. Structured errors require stable code, safe message, stage, retryability and correlation ID without secrets.

### 6. API and Web contract

The exact contract needs paths, methods, response/status/header schemas, pagination, error codes and race behavior for:

- enqueueing one verification job for a screenshot;
- fetching one job/attempt and state/result;
- listing stable append-only history;
- explicitly requesting a rerun;
- exposing OCR regions, provenance, expected snapshot, item matching, aggregate quality and processing error.

Web must show queued/processing/succeeded/failed-processing separately, and never show a processing failure as quality FAIL. It must distinguish expected missing, expected empty, no observed text and loading. It must show exact engine/model/language/config provenance, OCR text, boxes/confidences, score/method/status, snapshot identity and prior reruns. Multilingual text must render safely as text with appropriate direction handling. A current-catalog panel, if retained, must be labeled separately from the immutable snapshot used by the selected attempt.

### 7. Additive migration and ownership preservation

Phase 3 must add a new migration after `0003`; applied revisions remain unchanged. No OCR backfill should mutate accepted Screenshots or upload receipts. Fresh and populated `0003 → Phase3` migration evidence must preserve all existing IDs, Unicode metadata, source/client IDs, storage keys, hashes, relationships and original bytes. New parent relations use project-scoped restrictive FKs. Maintenance must fail closed around live jobs/results and never obtain ownership of Screenshot originals.

## Adversarial review matrix

### Durable job/snapshot/concurrency cases

| ID | Scenario | Required invariant |
| --- | --- | --- |
| OJ01 | Crash before/after job insert, snapshot rows, digest and enqueue commit | No job or one complete claimable job/snapshot; never partial |
| OJ02 | Mapping replacement or translation patch/delete races snapshot | Snapshot entirely before or after one change, never mixed |
| OJ03 | Concurrent same client job ID; changed fingerprint; lost enqueue response | One job/replay, deterministic conflict, no duplicate |
| OJ04 | Multiple processes claim pending/expired work; expiry equality | One owner; generation increments once; fresh token |
| OJ05 | Stale worker after takeover calls renew/fail/result/finalize | Every mutation denied; newer attempt unchanged |
| OJ06 | Ambiguous renew/result/finalize commit and primary loss | Fresh-primary resolution; no guessed FAILED or duplicate result |
| OJ07 | Crash/restart during durable backoff/exhaustion | Identity, counters and deadline survive; retries bounded |
| OJ08 | Concurrent explicit reruns and catalog edit between runs | Distinct ordered jobs/snapshots/results; prior bytes unchanged |
| OJ09 | Missing/tampered original | No result; retained Screenshot/receipt; operational failure only |
| OJ10 | Fresh and populated additive migration plus injected DDL failure | Phase 2 rows/originals preserved; no partial backfill |

Real PostgreSQL, independent connections/processes, deterministic barriers and invariant queries are required; mocks and sleeps alone are insufficient.

### OCR, geometry, confidence, matching, and semantic cases

| ID | Scenario | Required oracle |
| --- | --- | --- |
| OCR01 | Every declared locale plus unsupported locale and mixed scripts | Exact deterministic model mapping/arbitration; unsupported is explicit error |
| OCR02 | Identity, resize, crop, letterbox, 90/180/270 rotation, EXIF, deskew | Polygon maps to original encoded-raster space; AABB derivation exact |
| OCR03 | Edge boxes; negative/over-bound/nonfinite/zero-area/self-intersecting polygon | Edges valid; malformed values rejected |
| OCR04 | Confidence 0, 1, below 0, above 1, NaN/Inf, unavailable detector confidence | Endpoints accepted; invalid rejected; unavailable explicit |
| OCR05 | Japanese, Korean, Arabic/RTL, Latin, combining, supplementary, emoji/ZWJ/variation selectors | Raw code points preserved; unsupported engine output handled safely |
| MAT01 | Raw identical; `é`/decomposed and NFC/NFD Hangul; CRLF/LF | EXACT/100 or NORMALIZED/100 as versioned |
| MAT02 | Fullwidth/ASCII, case, diacritics, confusables, NBSP/U+3000/whitespace | No uncontracted equivalence |
| MAT03 | Pinned scorer vectors and score 100/95/94.999999/85/84.999999/0 | Exact unrounded score; PASS/PASS/REVIEW/REVIEW/FAIL/FAIL |
| MAT04 | Duplicate expected/observed text, equal ties, split labels and multi-region spans | Deterministic non-overlapping assignment and separator |
| SEM01 | Missing, empty, successful zero detections, engine error, malformed blank region | Five distinct semantic outcomes; no false PASS/FAIL |
| FIX01 | Actual-engine lane versus canned deterministic lane | Separate attribution; mocks cannot satisfy AC-P3-01 |

Threshold classification must use injected numeric scores. Hand-picked string pairs are not a reliable oracle for exact 95/85 boundaries.

### API/component/actual Web cases

| Concern | API proof | Component proof | Actual production Web proof |
| --- | --- | --- | --- |
| Queued/processing | Legal shape, terminal fields absent, polling identity stable | Status and reload behavior | Reload does not duplicate enqueue or show quality |
| Succeeded quality | Complete snapshot/provenance/regions/items/aggregate | PASS/REVIEW/FAIL rendering | Original and exact evidence visible together |
| Failed processing | Structured error and quality null | Dedicated error panel | Visibly distinct from quality FAIL after reload |
| Missing/empty/no text | Distinct JSON shapes | Explicit non-falsy branches | Browser labels each distinctly |
| Multilingual/geometry | Exact Unicode and finite polygon/confidence JSON | Safe text/direction and overlay | Visual inspection plus API/source hashes |
| Rerun/history | Stable ordering/pagination; prior attempt immutable | History selector | Attempt A remains after catalog edit and rerun B |
| Provenance/binding | Exact screenshot ID/hash/dimensions and artifact digests | Provenance panel | Browser/API jointly prove screenshot → attempt → result |

## Principal risks for later review

| Severity | Risk and required response |
| --- | --- |
| CRITICAL | Mutable `catalog_mode=current` reused as verification input would make historical results change. Require an atomic copied snapshot and race tests. |
| CRITICAL | Incomplete fencing on terminal/error paths lets an expired worker overwrite a newer generation. Require generation+token+time rules on every mutation and two-process barriers. |
| CRITICAL | Empty expected, missing translation, no OCR detections and OCR failure can become false quality PASS/FAIL. Require mutually exclusive schema and the full semantic matrix. |
| HIGH | Ambiguous commits can duplicate/hide a result. Require fresh-primary locked recovery and no guessed failure. |
| HIGH | Retry/rerun conflation or mutable result rows destroy reproducibility. Require same-job retry, new-job rerun and append-only history. |
| HIGH | Axis-aligned boxes alone lose rotated/skewed geometry; EXIF/inverse transforms are undefined. Preserve polygons and define transforms. |
| HIGH | Generic confidence can conflate detector, recognizer and verification score. Persist separate named values and provenance. |
| HIGH | Rounding before 95/85 changes classifications. Compare finite full-precision score before display rounding. |
| HIGH | Actual engine evidence drifts without model/font/image/runtime hashes. Pin and hash every artifact and separate actual versus deterministic lanes. |
| HIGH | Phase 3 mutation or deletion of accepted originals/history violates Phase 2. Use additive migration, restrictive FKs and before/after hash manifests. |
| MEDIUM | NFKC/case/whitespace/punctuation normalization can hide localization defects. Use a conservative versioned profile. |
| MEDIUM | Candidate segmentation, duplicate text and ties can produce nondeterministic matches. Define global assignment/tie-break rules. |
| MEDIUM | Frontend falsy handling can collapse `null`, `""`, confidence 0 and `[]`. Require explicit API/component/browser cases. |

## Verification commands and evidence requirements for later phases

These are planned commands/classes, not executed claims:

1. Hash-lock exact final contract, owner reports/handoffs, source manifests, dependency locks, model/dictionary/font/fixture manifests and generated OpenAPI/schema.
2. In clean pinned Windows and Linux environments, install the approved dependency lock and run `pip check`; record PaddleOCR/PaddlePaddle/OpenCV/RapidFuzz versions and model artifact hashes without machine paths.
3. Run actual OCR fixture tests separately from deterministic adapter/matcher tests under `tests/ocr/`, preserving raw JSON and coordinate overlays.
4. Run injected classifier boundaries and Unicode normalization/candidate assignment vectors independently of OCR confidence.
5. Run fresh PostgreSQL migration and populated `0003 → head` preservation tests, plus real multi-connection/process OJ01-OJ10 barriers and restart/ambiguous-commit recovery.
6. Run Backend API/schema/state-machine tests, generated OpenAPI parity, Frontend API/component/typecheck/build tests, and illegal-state response validation.
7. Extend the disposable current-source Web harness: upload synthetic multilingual originals through the accepted uploader/manual paths, enqueue verification through the public API, record exact IDs/hashes/provenance/snapshots/results, inspect actual production Web queued/processing/succeeded/failed and history views, and remove the disposable database/storage/services.
8. Reviewer independently reruns risk-selected lanes and distinguishes Owner evidence, independent evidence, failures and NOT_RUN.

Required evidence artifacts include exact executable commands and exit codes, environment/runtime/image IDs, JUnit or machine-readable results, raw engine JSON, input/output hashes, code-point manifests, model/dictionary/font licenses and hashes, coordinate oracles/overlays, matcher vectors, database invariant dumps, migration before/after manifests, Web evidence JSON/log and browser inspection notes.

## Commands, environment, and results in this preparation

Environment: Windows PowerShell; explicit workdir `C:\Dev\qa-visual-automation`; Git branch/HEAD observed as `main` / `a22294f5343fb865f02dfd049c041df5b8a33eb3`. This role did not create a branch or commit, so role branch/commit remains `null` / `null`.

| Command/check | Result |
| --- | --- |
| Read `AGENTS.md`, `docs/prompts/08_reviewer.md`, Phase 3 activation, PROJECT_STATE, TASKS, ACCEPTANCE and DECISIONS from explicit current root | PASS; Phase 2 accepted, preparation READY, later tasks blocked, AC-P3-01..04 NOT_RUN |
| `rg` over Phase 3/OCR/snapshot/matching/provenance/job terms and current Backend/Frontend/worker/tests | PASS; current baseline and absence of implementation identified |
| Read `docs/phases/phase-3-ocr.md`, current architecture contracts, expected resolver, string/screenshot models, Frontend types/API/components and relevant tests | PASS; static contract gaps and reusable Phase 2 invariants identified |
| `Test-Path docs/architecture/phase-3-ocr-contract.md` | PASS as a gate check: file is absent, so full contract review is BLOCKED |
| `Get-FileHash -Algorithm SHA256` over governing and baseline inputs | PASS; exact hashes recorded below |
| Three disjoint read-only sidecars: durable jobs/snapshot, OCR/matching/provenance, API/Web | PASS as preparation analysis; no file edits; requested model/effort recorded below |
| Git status/read-only baseline | PASS; existing dirty worktree observed and preserved; unrelated permission warnings from historical temp report directories did not block target reads |
| Product tests, typecheck/build, OCR/model download/inference, services, database, migration, API/browser flow | NOT_RUN by preparation scope |

Input SHA-256 values:

- `AGENTS.md`: `060df1fb9c37e93306d0bae6d6aa085214fd9f7cd55663f483924751b8148bc6`
- `docs/prompts/08_reviewer.md`: `28384182d4a24d51f09bc4b62809bdfae68889e9efd21c72b520abd72caab951`
- `.orchestration/handoffs/PHASE-3-activation-01.md`: `4c502c3abdec9a51b953c3c71d0f18a0b68a01613cd42f791b7a715dd9ed6588`
- `.orchestration/PROJECT_STATE.yaml`: `e45e460224f9595f365a9d7fdd27fbafc5ab02ed6ff96909432a8d1096ee693f`
- `.orchestration/TASKS.yaml`: `c3f407e83272257529e870103cad3fa71a7e94408b9a18c2da8310f925a4efb6`
- `.orchestration/ACCEPTANCE.yaml`: `6a13c6a36f21891a3a1d72af8a2475d8512374571f47019f3f7a99e3530ab9ae`
- `.orchestration/DECISIONS.md`: `6f9dd23aef72f286d75c87c309e2c1de68c562addf3ede91dbfce46f15e66cee`
- `docs/phases/phase-3-ocr.md`: `9104f3ec5fb7b9cfea386798e8fa5ef39ebf4da8d4e765ed2476117b1ca90cc5`
- `docs/architecture/api-contract.md`: `abcab2109becbe6938628aa3810bc547a33a8b2cc23348c71d8688bf6e7a0e70`
- `docs/architecture/domain-model.md`: `4147fde8c52e084b974f2fbc0f9cde14d493bd1442d234f01be9bdfb51680c1a`
- `docs/architecture/data-flow.md`: `08cb9119712d4731830d6b5513b6c38a1857f04360c9595f9c6eddb8be4f6f86`
- `backend/app/services/expected_strings.py`: `b7c911561004dcecc41c7141384d4f7e7ac9cdeb04139869d9212014a7de419a`
- `backend/app/models/strings.py`: `dd5fb6326a5f1ad49af5ecfb3f06621b2e270291dcdde467247c3c5e16636d45`
- `backend/app/models/screenshots.py`: `4f36e232d3ac5e234df7cebada56c4df370df491a95d60062513a2e83a787ddc`
- `frontend/lib/types.ts`: `050e57b9691fe70555d5af5d71e051519587e9f41101a660f81e79c609867894`
- `frontend/lib/api.ts`: `d878049044a2a2f51f774e9101a9fb7337df1193d376094627d1662db0f5b04c`
- `frontend/components/screenshots.tsx`: `f0bb3b21081269ae7fa4c7132a766505ac634738e47dc356bad9bdd7a8ed8c9d`
- `pyproject.toml`: `0024490e4faf1ca7bb21a25ec0c19fe72486229dd82f394fb157366de43bc003`

## NOT_RUN and gate limits

- AC-P3-01, AC-P3-02, AC-P3-03 and AC-P3-04: `NOT_RUN`.
- Exact Phase 3 contract review: BLOCKED because the contract file/submission is absent.
- OCR inference, model/language packs, coordinates/confidence, matching and thresholds: NOT_RUN.
- PaddleOCR/PaddlePaddle/OpenCV/RapidFuzz installation/download/license execution: NOT_RUN.
- Phase 3 migration, PostgreSQL jobs/concurrency/crash/restart, Backend API, Frontend build/typecheck/tests and actual Web: NOT_RUN.
- Sidecars performed read-only analysis only; their conclusions are integrated preparation input, not independent product evidence.
- No Phase 4 device automation, ADB interaction, game internals, mobile proposal edit or future-phase promotion occurred.

## Difficulty and model attribution

- Parent preparation: medium; requested `gpt-5.6-sol` / medium. Actual model identifier was not exposed and is `unverified`.
- Durable job/snapshot/concurrency sidecar: high because persisted evidence and stale-owner corruption are acceptance-critical; requested `gpt-5.6-sol` / high; agent `01a0d64b-46b6-7ab0-9d51-0970d91cefa9`; actual model `unverified`.
- OCR/matching/provenance sidecar: high because multilingual semantics, geometry and deterministic scoring can silently produce false QA conclusions; requested `gpt-5.6-sol` / high; agent `01a0d64b-4724-7721-b323-4c767fa2474b`; actual model `unverified`.
- API/Web sidecar: medium because it is a bounded compatibility/display matrix after semantic inputs are defined; requested `gpt-5.6-sol` / medium; agent `01a0d64b-478c-7693-a934-b6fe39c8f2b9`; actual model `unverified`.
- Parent Reviewer 08 read the governing files, performed independent baseline inspection, integrated all sidecar results, and remains responsible for the matrix and risks. No sidecar made an acceptance decision.

## Changes, prohibitions, and next actions

Changed files: this new report and `.orchestration/handoffs/REVIEW-OCR-PREP-001-08.md` only. Contract/product/tests/dependencies/PM state/mobile proposal changes: none. Branch/commit: `null` / `null`. No Commit, Push, deployment, user/shared DB reset, user-data deletion, account/security change or IP check occurred.

Next owner 02: use the required contract inputs and adversarial matrix above when authoring `docs/architecture/phase-3-ocr-contract.md`; choose exact semantics rather than copying recommendations implicitly. Submit an exact contract hash/report/handoff. Next owner PM01: hash-verify this preparation, preserve all AC as NOT_RUN, coordinate preparation inputs from 03/04/05, and activate `REVIEW-ARCH-OCR-001` only after the exact contract submission. Reviewer 08 will then return `ACCEPTED` or `CHANGES_REQUESTED` against that exact revision.
