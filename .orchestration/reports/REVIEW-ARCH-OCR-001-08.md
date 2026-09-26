# REVIEW-ARCH-OCR-001 / Reviewer 08 independent contract review

Date: 2026-09-25 KST  
Reviewer: 08 Senior Reviewer  
Task: `REVIEW-ARCH-OCR-001`  
Activation: `.orchestration/handoffs/REVIEW-ARCH-OCR-001-01.md`

## Disposition

**ACCEPTED — exact P3-OCR-v1 document revision 1, contract only.**

The reviewed contract is sufficiently deterministic, bounded and testable for PM to issue implementation file claims. It closes the preparation questions for immutable input capture, enqueue identity, durable job ownership, stale-worker fencing, ambiguous-commit recovery, OCR provenance, original-raster geometry, conservative normalization, rational threshold comparison, global one-to-one assignment, processing-versus-quality semantics, scoped read APIs and Web retry/history behavior.

No contract-blocking defect or unresolved high-impact ambiguity was established. This judgment does not accept an implementation, qualify a model or dependency set, or mark any Phase 3 product acceptance criterion PASS. `AC-P3-01` through `AC-P3-04` remain `NOT_RUN`.

## Exact reviewed artifacts

| Artifact | SHA-256 | Result |
| --- | --- | --- |
| `docs/architecture/phase-3-ocr-contract.md` | `46940dd1dd7775422213b2ba422b63650f4e83740e034cf29dc83f23970acb82` | MATCH |
| `.orchestration/reports/ARCH-OCR-001-02.md` | `27af58b950cd2f6487480d79b0efaf14329febd7a028785d6c126ff02eb9f69d` | MATCH |
| `.orchestration/handoffs/ARCH-OCR-001-02.md` | `1cb09f7f4faf36b1f8ac30d038ba75e7289da02772b3543653739814ab4784d8` | MATCH |
| `.orchestration/reports/PREP-BACKEND-OCR-001-03.md` | `253d8821fb5111db2e217401be7c1edd60a0d86456ee4ab75b81b18aba5a7105` | MATCH |
| `.orchestration/reports/PREP-FRONTEND-OCR-001-04.md` | `8bbf33936d463f854ee414277ce02db78aadb5bd109ed272c4aeff700ad622f0` | MATCH |
| `.orchestration/reports/PREP-OCR-001-05.md` | `556a29eef0cfb486e44f1896c4b6ff4f720198072215178bad711dc087a0630e` | MATCH |
| `.orchestration/reports/REVIEW-OCR-PREP-001-08.md` | `310c2a6bef3a929de7b9fc5293cb53896df9a31ab333f7371ab310d6c6468a8d` | MATCH |

The current PM state independently identifies this exact revision as review-ready and keeps OCR/Backend/Frontend implementation blocked. The contract has 55,163 UTF-8 bytes, 10 top-level numbered sections, 22 O-matrix rows and six resolvable local document links.

## Independent review findings

No required change finding is open.

### Immutable creation and idempotency

- One `REPEATABLE READ` creation transaction defines the snapshot at its first MVCC data query, copies exact Screenshot/context/expected values, profile and effective configuration, and commits the run plus one durable job atomically.
- Missing, present-empty and nonempty translations remain distinguishable. Copied mutable-catalog identifiers have no live FK that would rewrite or newly prevent catalog history changes, while the source Screenshot remains protected by a scoped restrictive FK.
- `(project_id, client_run_id)` plus a canonical request fingerprint gives one replay identity. Existing-ID replay precedes current profile availability checks, and ambiguous first insert is resolved by unique arbitration on a fresh primary transaction rather than an unlocked absence read.
- Snapshot/config canonical bytes and digests, size limits and fail-closed corruption behavior make later catalog/profile changes unable to alter a run.

### Durable job, fence and ambiguity rules

- PENDING/RUNNING/RETRY_WAIT/SUCCEEDED/FAILED transitions, maximum three claims, attempt evidence, DB-clock lease equality, generation/token predicates and overflow handling are explicit.
- Every worker mutation—including stage, renew, retry, fail, attempt close and finalize—uses a locked primary row and a fresh unexpired fence. Takeover/reaper is the explicit expired-lease exception and closes the predecessor under the same lock.
- OCR/matching occurs outside database transactions. Final OCR/result/item inserts and terminal success commit atomically under the live fence; stale generations cannot publish partial or terminal state.
- Lost claim, renew and finalize acknowledgements use connection invalidation and fresh-primary locked resolution. Unresolved outcomes are not converted to guessed failure or a fresh identity. This is sufficient for at-least-once computation with at-most-one committed result set.

### OCR, provenance and geometry

- A registered profile is immutable by identity/hash and records package, model, dictionary, license, preprocessing, device/thread and determinism facts. Candidate Paddle versions and model pairs are explicitly qualification candidates, not accepted availability evidence.
- Locale resolution is exact, pinned and no-fallback. Unsupported or unavailable behavior is typed and distinct from quality failure. Korean mixed-version compatibility, Windows/Linux dependency resolution, model artifacts and licenses remain implementation gates.
- The runner verifies one bounded source-byte buffer before decode and passes those same bytes to the adapter. Original bytes and accepted upload evidence remain read-only.
- Original-raster coordinates, EXIF policy, invertible transforms, geometric clipping, canonical polygon order, six-decimal projection, unrounded AABB derivation, raw preclip audit and separately named recognition/detection confidence are fully specified. A browser that cannot prove orientation must omit the overlay rather than display false geometry.

### Normalization, threshold and global assignment

- `norm-v1` pins Unicode 15.0 NFC, exact CR/LF handling and the enumerated Unicode White_Space set. Raw strings remain available; no casefold, NFKC, punctuation removal, transliteration or implicit locale rule is introduced.
- Levenshtein operates on Unicode scalar sequences with unit costs and `processor=None`. Classification compares exact integer numerator/denominator values against exact decimal thresholds before six-decimal display rounding.
- The one-to-one objective is fully ordered: maximize EXACT count, then NORMALIZED count, real-edge cardinality, micro-score sum, then the smallest region-index vector. The deliberate exact-first `[[100 EXACT,90 FUZZY],[90 FUZZY,80 FUZZY]]` outcome is explicit and testable, not an accidental greedy result.
- Complexity is bounded by 1,000 expected items, 1,000 regions, 65,536 real edges, one million normalized scalars, a 50,000,000 scalar-distance work budget, 8 MiB adapter output and the 300-second whole-attempt limit. Over-limit work fails closed without a greedy fallback. Owner05 must still demonstrate that its selected deterministic algorithm meets these limits in both target environments.
- Missing/empty/normalized-empty expected values produce explicit `UNVERIFIED` items with null score; successful no-text against evaluable expected values produces `FAIL/NO_MATCH`; engine/input failures remain processing `FAILED` with null quality. Aggregate precedence and counts prevent partial evidence from appearing as full PASS.

### API and Web behavior

- Scoped create/detail/history/expected/regions/items/summary routes, closed bodies/queries, `202` new versus `200` replay, typed conflict/unavailable/error states, CORS-exposed headers and deterministic pagination are specified.
- Latest requested and latest successful processing are distinct server selections. Failed/newer runs cannot rewrite or erase prior immutable history.
- The client retains one pending request and `client_run_id` across ambiguous transport/5xx outcomes, retries that same identity, creates a new ID only for an explicit new run, deep-links the selected run and rejects stale poll responses by selection lifecycle.
- Processing status, persisted error and quality outcome remain separate. Confidence zero, null score, empty text/pages and unknown enum values require explicit UI branches without PASS/FAIL inference.

## Preparation disposition audit

Backend03 questions B01–B18 are explicitly resolved by sections 1–4 and 10.1–10.3, including snapshot instant, copied fields/FKs, retry versus rerun, attempt history, append-only enforcement, cleanup/retention, claim identity and ambiguity recovery. Frontend04 questions F01–F12 are resolved by sections 2, 5–7 and 10.4, including geometry, precision, UNVERIFIED aggregation, latest selections, ambiguous submission, polling and safe errors. OCR05 questions E01–E08 are resolved by sections 4–6 and 10.3, with unqualified package/model choices correctly left as post-contract evidence gates.

Reviewer preparation alternatives were not copied silently: the contract explicitly chooses White_Space collapse in addition to NFC, `UNVERIFIED` rather than null item quality for successful unscorable items, geometric clipping with retained preclip audit, retained empty regions, and exact/normalized-first global assignment. Each deviation has observable wire data and a conformance requirement.

## Actual static verification

Environment: Windows PowerShell, explicit root `C:\Dev\qa-visual-automation`; Node `v24.19.0`, Node Unicode `17.0`. Node checks are reference semantics only and are not evidence for Python Unicode 15, RapidFuzz, PostgreSQL or PaddleOCR.

| Check | Result |
| --- | --- |
| Read current `AGENTS.md`, Reviewer08 prompt, PM activation/state/tasks/acceptance/decisions, all four preparation reports, exact Architect report/handoff and full contract | PASS |
| SHA-256 recheck of contract/Architect/preparation inputs | PASS; values above match |
| Contract local-link, byte-count, section-count and O-matrix inventory check | PASS: 6 links/0 missing, 55,163 bytes, 10 sections, 22 rows |
| Independent Node reference assertions for the enumerated whitespace/NFC examples, supplementary-scalar Levenshtein, rational 95/85 boundaries, exact-first assignment, normalized assignment, inverse resize/pad transform and strict lease equality | PASS: 10 assertions |
| Static current-source compatibility read of expected-string resolver, Screenshot/String models, upload fence repository, Frontend API and hash navigation | PASS; live-current catalog, missing/empty distinction, raw dimensions, DB-clock fencing and current client limitations match the contract assumptions |
| Scoped `git status` before review artifact creation | PASS: exact contract observed as pre-existing untracked submission; no prior Reviewer08 contract report/handoff existed |

Independent reference output:

```json
{"result":"PASS","assertions":10,"node":"v24.19.0","unicode":"17.0","scope":"independent reference only; no product, RapidFuzz, PostgreSQL, or OCR execution"}
```

## NOT_RUN and implementation gates

- `AC-P3-01`, `AC-P3-02`, `AC-P3-03`, `AC-P3-04`: `NOT_RUN`.
- OCR package installation/resolution, model or dictionary download, license verification, actual inference and Windows/Linux resource qualification: `NOT_RUN` by contract-review scope.
- Python 3.12 Unicode 15/RapidFuzz conformance, global-assignment worst-case performance and actual adapter schemas: `NOT_RUN`; required from Owner05 implementation evidence.
- PostgreSQL migration, real concurrency/lease/fence/ambiguous-commit/crash recovery and source-object integrity: `NOT_RUN`; required from Owner03 evidence and independent implementation review.
- Backend API/OpenAPI, Frontend tests/typecheck/build, browser lifecycle, actual production Web and end-to-end OCR history: `NOT_RUN`.
- Contract author Node 35 assertions were read as owner static evidence only and were not relabeled independent product PASS.

## Scope, changes and next gate

Changed files are this report and `.orchestration/handoffs/REVIEW-ARCH-OCR-001-08.md` only. Product source, tests, contract, dependencies, PM state/YAML and prior reports were not modified. Branch/commit: `null` / `null`. No Commit, Push, deployment, model installation, database execution/reset, user-data deletion, security/account change, IP check, Phase 4 or mobile work occurred.

Requested parent model was `gpt-5.6-sol` / high; actual model identity was not exposed and remains `unverified`. Prior preparation/Architect sidecars were recovered as inputs; this parent independently read the selected sources, ran the bounded static checks and owns the disposition.

PM01 may record `REVIEW-ARCH-OCR-001` as `ACCEPTED` for this exact hash and issue exact implementation claims. Implementation owners must preserve every qualification and evidence gate above. Final `REVIEW-OCR-001` remains blocked until matching OCR, Backend and Frontend submissions are ready; only that later review can disposition the four Phase 3 product ACs.

