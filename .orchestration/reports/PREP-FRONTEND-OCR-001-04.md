# PREP-FRONTEND-OCR-001 Frontend preparation report

Date: 2026-09-25 KST  
Owner: 04 Frontend  
Status requested: `READY_FOR_REVIEW` preparation only  
Implementation status: `FRONTEND-OCR-001` remains `BLOCKED`

## Goal, scope and gates

This preparation assesses the existing Web/API/type surface and supplies concrete input to Architect02 and PM01 for the Phase 3 OCR contract. It covers OCR regions, original-image coordinates, multilingual confidence, expected/observed/score presentation, processing errors versus quality outcomes, repeatable reruns, immutable history and the minimum later Frontend file claim.

Phase 2 acceptance was confirmed from `.orchestration/handoffs/PHASE-2-acceptance-01.md`, SHA-256 `17c524e2bfcad078080e15f04d53dd9713e0c281a396e13f048b1b64b6f1358c`. Phase 3 activation is `.orchestration/handoffs/PHASE-3-activation-01.md`, SHA-256 `4c502c3abdec9a51b953c3c71d0f18a0b68a01613cd42f791b7a715dd9ed6588`.

Only contract and preparation work is authorized. Product implementation requires both:

1. `REVIEW-ARCH-OCR-001` independently `ACCEPTED` for the exact final contract.
2. PM approval of the exact implementation file claim.

No Frontend, Backend, worker, test, shared architecture, PM state or mobile proposal file was changed. Phase 4 work was not started.

## Current compatibility inventory

The existing Web provides a sound base but has no OCR/run/result model yet:

- `frontend/lib/types.ts` models Screenshot upload identity, metadata and current Expected Strings. It has no OCR region, processing run, verification item or history type.
- `frontend/lib/api.ts` exposes screenshot list/detail/content and `/expected-strings`. `ApiClient.request()` has a 60-second timeout, reports transport/contract failures as `ApiError`, and intentionally does not retry ambiguous writes.
- `frontend/components/screenshots.tsx` independently loads screenshot detail, original image and current Expected Strings. A storage failure does not hide screenshot metadata or expected strings. This independence should extend to OCR history/result failures.
- `frontend/components/common.tsx` already distinguishes missing translation (`null`) from a present empty string (`""`), renders multilingual text as text rather than HTML and uses `dir="auto"`.
- `frontend/lib/navigation.ts` provides stable hash deep links for one screenshot `id`, but has no selected verification-run identity.
- `frontend/components/workspace.tsx` scopes requests by the parsed navigation state. A selected run must become part of this identity so stale responses cannot replace the currently selected history item.
- the existing screenshot image uses a responsive rendered size. Overlay coordinates cannot be placed directly in CSS pixels; the overlay needs the contract's original image coordinate space and a matching SVG `viewBox` or equivalent scale transform.

The largest semantic boundary is current versus historical expected data. `ExpectedStrings.catalog_mode` is `current`, and the Web explicitly states that it is the current Build catalog rather than an upload-time snapshot. A verification history view must never use `screenshotExpected()` as its historical input. Every run detail must return its immutable expected snapshot together with its immutable OCR/verification output.

## Contract input for Architect02

### Separate resources and minimum operations

Keep OCR and verification as separate screenshot-scoped resources instead of embedding changing arrays in `Screenshot`. The Frontend needs contract-equivalent operations for:

- page through append-only run summaries for a screenshot;
- retrieve one exact run by immutable run ID;
- request a rerun asynchronously and receive a durable run identity, normally HTTP 202;
- retrieve or safely repeat an uncertain rerun request with an idempotency key/client rerun ID;
- poll only the selected nonterminal run and stop on terminal state, navigation change or unmount.

Illustrative paths are `GET/POST /api/v1/projects/{project_id}/screenshots/{screenshot_id}/verification-runs` and `GET .../verification-runs/{run_id}`. The exact names and response codes belong in the reviewed contract.

### Processing status, quality outcome and errors

Use independent fields:

- processing status: the exact contract enum corresponding to pending, running, succeeded and failed;
- quality outcome: `PASS | REVIEW | FAIL | null`;
- persisted processing error: structured code, safe message, retryability and correlation/request identity, or null;
- request/API error: the existing `ErrorEnvelope`/`ApiError`, separate from a persisted failed run.

Nonterminal and processing-failed runs must have `quality_outcome: null`. A worker/engine failure must not render as quality `FAIL`. Likewise, expected translation missing, OCR no-text/missing-observed and no scorable expectations require explicit reason fields and nullable scores rather than fabricated matches. The exact aggregate treatment of those conditions remains a contract decision below.

The Web should display processing and quality in different labelled columns/badges. Historical processing errors are ordinary run data and should not announce as a new live `role="alert"` on every page load. Current request failures continue through `ErrorBox` with retry and request ID.

### OCR region and coordinate wire requirements

Each run detail must identify the engine, engine version, model/version, requested and detected languages, preprocessing/orientation version and source Screenshot ID/hash. Each region needs:

- stable region ID and deterministic reading order;
- original observed Unicode text without display-time normalization;
- finite recognition confidence with an exact documented range distinct from match score;
- a versioned coordinate-space declaration: original decoded image width/height, pixel unit, origin/axis direction and orientation handling;
- a bounded geometry representation that can be overlaid without guessing transformations.

The accepted Phase 1 outline uses `{x,y,width,height}` in original decoded pixel coordinates. Rotated multilingual text may require a four-point polygon. Architect02 should select one exact representation, ordering/winding rule, numeric precision and clipping/bounds rule. The Web will preserve raw coordinates in an accessible table and scale the same points over the original image. Color alone must not carry status; selecting a row/region needs a textual label and keyboard-reachable equivalent.

Recognition confidence and match score need different names, units and formatting. A confidence `0` and match score `0` are valid values and must not be treated as absent by truthiness checks.

### Immutable expected, observed and item results

Every run must freeze expected inputs at a contract-defined transaction boundary before asynchronous worker processing. The proposal is the rerun-request transaction, not lease acquisition, so queue delay cannot change the expected catalog. The snapshot needs:

- Screenshot ID/hash plus build, locale and situation identity;
- ordered string key and string ID;
- translation state `present | missing`;
- entry ID when present;
- exact expected text when present, preserving `""`, whitespace, line endings and Unicode code points;
- normalization/matching algorithm version and threshold/configuration snapshot.

Observed regions and Verification items remain append-only with the run. A later OCR model, configuration or catalog change creates a new run and never edits old data.

Each item needs explicit expected and observed objects, match method, nullable match score, nullable quality outcome and a machine-readable comparison reason/state. Required distinctions include:

- expected translation missing;
- expected present but empty;
- observed region missing or OCR returned no text;
- compared exact/normalized/fuzzy;
- processing failed before comparison;
- no scorable expectations.

Displayed text must preserve multilingual content and use `dir="auto"`/isolation for Korean, Japanese, Arabic/RTL, combining characters and emoji. It must never be interpreted as HTML.

### Threshold precision

The server owns classification; the Web displays the server outcome and threshold snapshot and must not recompute status from a rounded display score. Architect02 should choose an exact wire precision. Integer basis points `0..10000` are one unambiguous option:

- `>=9500` PASS;
- `>=8500` and `<9500` REVIEW;
- `<8500` FAIL.

If the contract keeps decimal `0..100`, it must define accepted precision, serialization and rounding before classification. Boundary fixtures must include exact 95/85 and immediately adjacent representable values.

### Rerun and history behavior

A rerun request needs a client-supplied idempotency identity. Same identity and same fingerprint returns the same run without adding history; reuse with different input returns an explicit conflict. A new identity creates a new append-only run with `rerun_of` or equivalent lineage.

The history response must not use an ambiguous single `latest`. It should expose or define both latest requested run and latest successfully completed/scorable run, because the newest run may still be processing or may have failed. The UI defaults to the latest requested run while preserving visibility of the last completed quality result.

The selected run ID belongs in the hash URL, for example a `run` query field on the existing Screenshot Detail route. Reload, back/forward and bookmarks must reopen that exact run. History paging needs a deterministic ordering and stable cursor/offset behavior.

Unknown future enum members need a safe fallback label with the raw value; consumers must not silently map them to PASS or FAILED.

## Decisions required from Architect02

1. Exact endpoints, HTTP status codes and list/detail/create schemas.
2. Exact processing enum names and terminal states.
3. Geometry: axis-aligned rectangle or ordered four-point polygon; origin, axes, orientation, precision and bounds.
4. Recognition confidence range/precision and match score range/precision.
5. Expected snapshot transaction boundary.
6. Semantics and aggregate effect of expected missing, expected empty, OCR no-text/missing observed and no scorable expectations. Current architecture says these must not masquerade as ordinary quality PASS/FAIL; the Web needs explicit states and nullable score/outcome.
7. Whether an empty expected string means “excluded/unverified” or a region-constrained absence assertion. Absence cannot be established from an unscoped empty string alone.
8. Aggregation rule when some items are comparable and others unverified.
9. `latest_requested` and `latest_completed` selection semantics.
10. Idempotency identity, request fingerprint, conflict/replay response and recovery from an ambiguous network/5xx result.
11. Poll interval/backoff/Retry-After and terminal retention/history paging rules.
12. Safe persisted processing-error fields and whether retryability is authoritative.

## Architect02 draft direction received during preparation

Architect02 supplied the following draft direction after the initial inspection. It is incorporated as interface preparation, not treated as an accepted contract:

- `POST /screenshots/{id}/verification-runs` uses a stable `client_run_id`, returning 202 for a new run and 200 for replay;
- run history/detail plus expected snapshot, OCR regions and verification items are separately paged resources;
- processing is `PENDING | RUNNING | RETRY_WAIT | SUCCEEDED | FAILED`;
- quality is `PASS | REVIEW | FAIL | UNVERIFIED`, while an engine-processing `FAILED` run has no quality value;
- run creation freezes the immutable expected snapshot; the existing expected endpoint remains current-catalog only;
- regions use the stored raw raster coordinate space with EXIF ignored;
- the result table is mandatory; an overlay is optional until orientation mapping is proven;
- OCR profiles are listed from `/projects/{id}/ocr-profiles`;
- expected missing and expected empty are `UNVERIFIED`; successful OCR with no observed text against a nonempty expected value is `FAIL`; engine failure remains processing `FAILED` with quality null.

The current Frontend has the following concrete gaps against that draft:

- `types.ts` needs `RETRY_WAIT`, `UNVERIFIED`, nullable run quality on failed processing, profile summaries, run summaries/details and four paged child models;
- `api.ts` needs 202-new/200-replay handling. Its current `expectedStatus` accepts only one status, so rerun cannot use the generic success assertion unchanged;
- the rerun request must preserve one generated `client_run_id` across an ambiguous transport/5xx outcome and must not silently create a replacement ID;
- history/detail and child-page loading need independent error/loading/pagination state so one failed page does not hide Screenshot metadata, original image or other completed pages;
- `RETRY_WAIT` needs retry time/reason fields to avoid speculative client countdowns and must remain processing, not quality;
- profile selection needs a stable profile ID/version and must be frozen into each run summary/detail so a later profile edit does not rewrite history;
- raw-raster coordinates with EXIF ignored can diverge from browser-decoded JPEG orientation. The table can always show authoritative raw geometry; overlay must remain disabled or clearly unavailable until the contract supplies a proven display transform or normalized display artifact;
- URL state needs selected run ID and, if child paging is user-visible, stable page/cursor state or a documented reset-on-run-change rule;
- unknown processing, quality, reason and profile enum values need raw fallback rendering without accidental PASS/FAIL mapping.

The exact contract remains pending and may supersede these names or paths. Owner04 will implement only the independently accepted revision.

## Proposed later implementation claim

After exact contract acceptance, Owner04 requests an exclusive coordinated claim for only these existing files:

- `frontend/lib/types.ts` — OCR/run/result wire types;
- `frontend/lib/api.ts` — run history/detail/rerun operations;
- `frontend/lib/navigation.ts` — selected run deep link;
- `frontend/components/screenshots.tsx` — current catalog, history, selected result, accessible overlay and rerun UI;
- `frontend/components/workspace.tsx` — run-aware page/request identity;
- `frontend/app/globals.css` — responsive overlay, table and status presentation;
- `frontend/tests/api.test.ts` — routes, 202/replay/conflict, null/zero and unknown enum behavior;
- `frontend/tests/components.test.tsx` — lifecycle, error/quality separation, multilingual/empty/missing/no-text, overlay/history/deep-link behavior;
- `frontend/tests/integration/contract.test.ts` — OpenAPI and real client contract;
- `tests/frontend/run_integration.py` — isolated actual OCR-to-production-Web evidence mode.

No new top-level navigation view is required. `frontend/components/common.tsx` is not requested initially because its current `TextValue`, `ErrorBox`, `Loading` and request-cancellation behavior can be reused. If the final contract demonstrates a shared component change, Owner04 will request that addition from PM before editing.

Several requested files contain existing Phase 2 work in the shared dirty tree. Later implementation must preserve it and use PM's exact source boundary; this preparation does not revert or rewrite any existing change.

## Completion condition for FRONTEND-OCR-001

The later implementation is complete only when:

- accepted exact wire types and API methods are implemented without altering Phase 2 screenshot/upload semantics;
- one screenshot displays current catalog separately from immutable run history;
- a chosen run displays processing state, persisted error, quality outcome, expected/observed/method/score/reason, region text, raw coordinates and confidence;
- rerun creation is idempotent and append-only, and exact runs survive reload/deep link/history switching;
- pending/running/failed, PASS/REVIEW/FAIL, expected missing, expected empty, no text and request errors remain visibly distinct;
- original screenshot rendering remains available when OCR/history/result requests fail;
- automated API/component/type/build/integration checks pass and a real or contract-approved deterministic OCR path is shown in the production Web;
- Reviewer08 independently disposes AC-P3-01 through AC-P3-04.

## Verification matrix and planned commands

| AC | Required later evidence | Current status |
| --- | --- | --- |
| AC-P3-01 | Korean, Japanese, Arabic/RTL, combining characters and emoji survive API and rendering; exact region geometry and confidence match the source image at multiple rendered sizes; accessible table matches overlay | `NOT_RUN` |
| AC-P3-02 | exact, normalized and fuzzy cases; expected missing/empty, observed missing/no-text, score zero; catalog mutation after run does not alter the selected historical snapshot | `NOT_RUN` |
| AC-P3-03 | exact boundary and adjacent values for 95 and 85; Web shows server outcome and config snapshot without client reclassification | `NOT_RUN` |
| AC-P3-04 | no-run, pending, running, succeeded, failed; same idempotency replay, conflicting reuse, new rerun, failed latest plus prior completed selection; history paging, refresh, deep link, late-response suppression and actual production Web evidence | `NOT_RUN` |

Planned implementation-gate commands, adjusted to the final contract:

```powershell
npm.cmd --prefix frontend run test -- tests/api.test.ts tests/components.test.tsx
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe tests\frontend\run_integration.py --isolated-postgres
```

An OCR Web mode such as `--verify-ocr-web` is only a proposal and does not exist. It must not be reported as executed. The actual OCR path must use Owner05's accepted engine/model/language artifacts and Backend03's accepted durable run API.

No product test, typecheck, build, integration, OCR execution or browser verification was run for this read-only preparation. All ACs and product verification remain `NOT_RUN`.

## Actual preparation commands and environment

Actual read-only work used PowerShell in `C:\Dev\qa-visual-automation` on `Microsoft Windows NT 10.0.26200.0`, Node `v24.19.0`, npm `11.17.0`. The project `.venv\Scripts\python.exe` path exists; it was not launched for this preparation.

Commands performed:

- `Get-Content` for `AGENTS.md`, role prompt, Phase 3 activation, Phase 2 acceptance, Phase 3 phase/architecture and Frontend source/test files;
- `rg` over TASKS/ACCEPTANCE/state and Frontend/architecture symbols;
- `Get-FileHash -Algorithm SHA256` over source and activation inputs;
- `node --version`, `npm.cmd --version`, OS/version and venv-path existence inspection;
- final scoped `git diff --check` for the two Owner04 preparation artifacts.

A broad report discovery search encountered access denial for existing Reviewer temporary directories. Per project rules it was not bypassed or repeated; those directories are unrelated to this preparation, and all required canonical inputs were readable.

Key inspected source hashes:

- `frontend/lib/types.ts` `050e57b9691fe70555d5af5d71e051519587e9f41101a660f81e79c609867894`
- `frontend/lib/api.ts` `d878049044a2a2f51f774e9101a9fb7337df1193d376094627d1662db0f5b04c`
- `frontend/lib/navigation.ts` `374dc65df409a50ea353c9d53ed4efc498703eff55b48864f16426e627e2c2c6`
- `frontend/components/common.tsx` `c92d73a68150297da8e74b10358f6887eb00bc839a44178d911d3aa1c4de4d16`
- `frontend/components/screenshots.tsx` `f0bb3b21081269ae7fa4c7132a766505ac634738e47dc356bad9bdd7a8ed8c9d`
- `frontend/components/workspace.tsx` `509c36a532612ffe69105d4f4c4f272130762056d25813b4175a29988788cf93`
- `frontend/app/globals.css` `62cdf7877404b6b3c93f9bedd5b92aee1f527c2d85dff7eda9d42786f4c5a3f6`
- `frontend/tests/api.test.ts` `79ad3cfc27be8e0994761531a8184ae42be596c3a5e4d6bc8f1d24c026a801f7`
- `frontend/tests/components.test.tsx` `1755be9b3c61ed7783433c99cf45795d004b3af61b9540bf5bcc985bdd21e74f`
- `frontend/tests/integration/contract.test.ts` `a30e873a2ee7f6b3163a048efa5407cbb183ab695cfb1164c990fbb93ca2373c`
- `tests/frontend/run_integration.py` `3d4952eb33bf6c4c928563a128d7b6fa7d19305ce4005096fdce61fbbe69ee1c`

## Delegation and model rationale

The parent retained integration and the immediate contract synthesis. Two disjoint read-only medium-risk slices were delegated because the active task explicitly requested independent subagents:

- Hume `01a0d64a-f92f-7b31-9265-e226765a249a`: current API/type/view compatibility and exact file claim; requested `gpt-5.6-sol / medium`.
- Newton `01a0d64a-f9d6-7510-9b9b-8227fcdaba83`: lifecycle/error/rerun/history semantics and AC verification matrix; requested `gpt-5.6-sol / medium`.

They had non-overlapping focus and changed no files. Actual model IDs were not exposed and remain `unverified`. The task's requested parent model is `gpt-5.6-sol / medium`; actual parent runtime identity is also recorded as `unverified` per project policy.

## Risks and unresolved items

- `docs/architecture/phase-3-ocr-contract.md` was not present at inspection time; endpoint/enums/precision/geometry/snapshot timing are not final.
- Mutable current Expected Strings can invalidate historical evidence if reused for run details.
- Recognition confidence and match score can be confused unless names, ranges and units are distinct.
- Latest failed/processing run can hide the previous completed outcome unless both identities are exposed.
- Axis-aligned boxes may lose rotated-text geometry; polygons add ordering/precision complexity. Contract resolution is required.
- Empty expected text has no testable “absence” region without additional contract data.
- Client-side threshold recomputation can disagree with the server at precision boundaries.
- Dirty shared Frontend files require PM source pinning before implementation.

Next owners: Architect02 incorporates or resolves the contract questions; PM01 reviews the proposed file claim. Owner04 waits for exact contract independent acceptance and PM implementation activation.
