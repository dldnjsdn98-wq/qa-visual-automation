# PREP-OCR-001 — OCR engine and multilingual fixture preparation

- Date: 2026-09-25 KST
- Owner: 05 OCR / Verification
- Status: preparation complete; Architect 02 consultation incorporated and PM 01 consultation requested
- Difficulty: high — engine/model/language compatibility and multilingual false-positive/false-negative behavior affect every Phase 3 result, while the real engine, models, and target environments are not yet installed or measured
- Requested model: `gpt-5.6-sol` / `high`
Actual model: unverified; the dispatch requested this value but no auditable execution metadata proves the active model
Branch / commit: null / null

## Goal, scope, dependencies, and evidence boundary

`PREP-OCR-001` is READY after Phase 2 acceptance. This preparation assesses PaddleOCR, PaddlePaddle, OpenCV, RapidFuzz, locale/model mapping, output semantics, resource/licensing constraints, and a reproducible multilingual fixture plan. It does not implement OCR or verification behavior.

`OCR-001` remains BLOCKED on exact `REVIEW-ARCH-OCR-001` acceptance and PM implementation file ownership. No files under `worker/ocr/`, `worker/verification/`, `tests/ocr/`, `pyproject.toml`, Backend, Frontend, Phase 4, or the mobile proposal were changed. No package was installed, no wheel or model was downloaded, no OCR/fuzzy test was run, and no acceptance item is claimed PASS.

The current source of truth records Phase 3 IN_PROGRESS only for contract/preparation and leaves AC-P3-01..04 NOT_RUN. The preparation completion condition is met by the compatibility and validation proposal below; product completion is not implied.

## Current repository/runtime facts

| Fact | Current evidence | Consequence |
| --- | --- | --- |
| Project Python contract | `pyproject.toml`: `>=3.12,<3.13`; Backend images use `python:3.12-slim` | Phase 3 must prove CPython 3.12 on Windows x86-64 and Linux x86-64. |
| Existing OCR dependencies | None in `pyproject.toml`; no OCR worker/test tree exists | Dependency selection and all runtime evidence remain future work. |
| Project venv | `.venv/Scripts/python.exe` exists but cannot start because its referenced user Python is absent | Do not use this venv as evidence; rebuild a clean environment only after approval. |
| Read-only probe | Bundled CPython 3.12.14, 64-bit Windows, Unicode database 15.0.0 | Unicode examples below are preparation evidence only, not target-worker validation. |
| RapidFuzz | `importlib.util.find_spec("rapidfuzz")` returned false | Fuzzy scores and threshold boundaries are NOT_RUN. |
| Docker | One read-only inventory attempt was permission denied | No repeat/override was attempted; Linux package/runtime checks remain NOT_RUN. |

## Version and compatibility proposal

Official package/documentation facts observed on 2026-09-25:

| Component | Observed current release/support | Proposed Phase 3 baseline before lock generation |
| --- | --- | --- |
| PaddleOCR | 3.7.0; Python >=3.8; `py3-none-any` wheel 146.8 kB; Apache-2.0 | Pin `paddleocr==3.7.0`; basic OCR capability only, no `[all]` extras. |
| PaddlePaddle CPU | 3.3.1; CPython 3.12 Windows x86-64 wheel 104.8 MB and Linux x86-64 wheel 194.8 MB; Apache-2.0 | Start with `paddlepaddle==3.3.1`, CPU, `paddle_static`, FP32. GPU/HPI is out of the initial reproducibility baseline. |
| PaddleX | Current PyPI 3.7.2; Python 3.8–3.13; OCR extras exposed; Apache-2.0 | Let PaddleOCR's exact dependency constraint resolve it; record the resolved version and lock hashes. Do not independently float to latest. |
| RapidFuzz | 3.14.6; Python >=3.11; Windows/Linux wheels; MIT; Windows needs VC++ 2019 runtime | Pin `rapidfuzz==3.14.6`; use an explicitly named scorer and no implicit processor. |
| OpenCV Python headless | 5.0.0.93 observed; Python 3.12 wheels; package scripts MIT, OpenCV Apache-2.0, bundled FFmpeg LGPL-2.1; only one `cv2` wheel family may be installed | Use a headless build for worker/server use, but do not select 5.0.0.93 until PaddleOCR/PaddleX dependency resolution proves it compatible. Never install `opencv-python*` and `opencv-contrib-python*` variants together. |

The safe packaging path is a clean disposable CPython 3.12 environment for each OS, resolver dry-run/report first, then a hash-locked CPU environment after PM/owner03 approval. The lock must include all transitive packages and hashes. Record Python/OS/architecture, package freeze, wheel filenames/hashes, model source URLs, model file hashes, environment variables, CPU thread count, and engine options. A successful import is insufficient; both `paddle.utils.run_check()` and real model inference are required after installation approval.

PaddleOCR downloads official models automatically, from Hugging Face by default and BOS when `PADDLE_PDX_MODEL_SOURCE="BOS"`. Production/test jobs must not depend on an unversioned first-run network download. After approval, prefetch a declared model set into an immutable cache, record every artifact hash/size/source, run offline from that cache, and fail with a separate engine/configuration error if an artifact is absent or mismatched.

## Required locale/model mapping

The latest PP-OCRv6 unified recognition model does **not** cover Korean. Official documentation lists Chinese (simplified/traditional), English, Japanese, and 46 Latin-script languages for PP-OCRv6. Korean appears under PP-OCRv5 and earlier language mappings.

Recommended initial locale map:

| Product locale family | Detection | Recognition | Reason / constraint |
| --- | --- | --- | --- |
| `en`, `zh-Hans`, `zh-Hant`, `ja` | `PP-OCRv6_medium_det` | `PP-OCRv6_medium_rec` | One 59.4 MB detector plus one 73.3 MB recognizer; v6 medium is the current accuracy-oriented server baseline. |
| `ko` | Prefer the same versioned v6 detector only after mixed-pipeline evidence; otherwise approved v5 detector | `korean_PP-OCRv5_mobile_rec` | Korean model is 14 MB, reported average accuracy 88.0, and supports Korean, English, and digits. It is the documented current Korean path. |

Model choice must be an immutable job input derived from a canonical application locale, never inferred silently from recognized glyphs. The contract should store requested locale, resolved locale family, engine/version, detector model/version/hash, recognizer model/version/hash, and configuration version in every OCR result. Unsupported locale must be an explicit configuration outcome, not fallback to English or PASS/FAIL quality.

Questions for Architect 02:

1. Is the first supported locale set exactly `en`, `ko`, `ja`, `zh-Hans`, and `zh-Hant`, or every catalog locale? Define fallback as forbidden unless explicitly configured.
2. May a v6 detector feed the v5 Korean recognizer? If so, the exact pair is a versioned pipeline identity and requires real-engine evidence. If not, declare a Korean v5 pipeline separately.
3. Does the expected catalog snapshot carry BCP-47 locale, a project locale UUID plus immutable language tag, or both? OCR locale selection must not depend on mutable display names.
4. Is PP-OCRv6 medium acceptable for the initial CPU budget, or must small/mobile be benchmarked as a separate approved profile? Model tiers must not change behind one algorithm version.

## Output, coordinates, confidence, resize, and rotation

Official general-pipeline output exposes `dt_polys`, `rec_polys`, axis-aligned `rec_boxes`, `rec_texts`, and per-recognition `rec_scores`. The standalone detection module also exposes `dt_scores`, but the documented general-pipeline example does not include detection confidence. The contract must therefore distinguish:

- recognition confidence: `rec_scores[i]` in `[0,1]` for recognized line `i`;
- detection confidence: nullable/absent unless the selected integration path exposes and preserves `dt_scores[i]`;
- verification match score: RapidFuzz-derived `[0,100]`, never confused with either engine confidence.

Each region should retain the four-point polygon and recognition confidence. Axis-aligned boxes may be derived for display but must not replace the polygon. Preserve numeric precision received from the engine; do not round before persistence or matching. Reject length mismatches among polygons, texts, and scores as an engine-result error.

Paddle detection can resize according to `limit_side_len`, `limit_type`, and `max_side_limit`; the docs describe `min`/`max` behavior but do not establish in the reviewed text that every returned coordinate is already mapped to the untouched screenshot after all optional preprocessing. Contract requirement: every persisted polygon is in the original screenshot pixel coordinate system, origin top-left, x right, y down, with the original width/height and an explicit coordinate-space version. Implementation must prove the mapping with synthetic corner/edge fixtures at multiple resolutions; it must not assume library internals.

For screenshots, initial profile recommendation:

- disable document orientation classification and image unwarping, which can transform the full frame and complicate original-coordinate guarantees;
- choose one fixed detector resize profile and persist it; do not vary thresholds or resize values to make a failing fixture pass;
- evaluate text-line orientation separately. The documented classifier supports only 0° and 180° classes. It does not establish 90°/270° or arbitrary-angle support;
- classify 90°/270°/vertical layouts as explicit supported fixture cases only if the complete pipeline succeeds with original-coordinate evidence. Otherwise report unsupported/engine limitation, not missing-text FAIL;
- preserve the original screenshot bytes and hash; preprocessing outputs are derived artifacts only.

Questions for Architect 02:

5. Must detection confidence be part of AC-P3-01, or is per-region recognition confidence sufficient? If detection confidence is required, mandate an adapter path that exposes it.
6. What polygon order and numeric domain are canonical? Proposed: four vertices in engine order plus validated finite coordinates clipped only for display, never silently modified in stored raw result.
7. Are coordinates required before or after optional whole-image preprocessing? Proposed: only original screenshot coordinates are public/persisted; any transformed coordinates are internal and separately labeled.
8. Are 90°/270° and vertical Japanese first-release requirements? The engine's line-orientation classifier is only 0°/180°.

## Matching and normalization proposal

Store raw OCR text and raw expected snapshot exactly. Matching operates on derived strings and records `normalization_profile`, `normalization_version`, `scorer`, scorer version, and both derived strings or their safe reproducible representations.

Recommended conservative v1 flow, aligned with Architect 02's 2026-09-25 draft decision:

1. `exact-v1`: raw Unicode scalar sequence equality. No trim, case fold, width conversion, punctuation removal, or whitespace collapse.
2. `normalized-nfc-space-v1`: reject invalid persisted Unicode; normalize to NFC; map Unicode whitespace runs to one ASCII space; trim outer comparison whitespace. Do not case-fold, apply NFKC, transliterate by locale, or remove punctuation/digits in v1.
3. `fuzzy-levenshtein-v1`: apply `normalized-nfc-space-v1`, then `rapidfuzz.distance.Levenshtein.normalized_similarity` with `processor=None`, scaling its `[0,1]` result to `[0,100]`. Do not use `fuzz.ratio`, `partial_ratio`, `WRatio`, or token-set scorers for acceptance.

RapidFuzz 3.x performs no default preprocessing. Relying on defaults is still unsafe: pass `processor=None` explicitly and persist `rapidfuzz==3.14.6` plus the fully qualified scorer name. Compare the underlying integer Levenshtein distance and denominator as a rational threshold test equivalent to `score >= 95 => PASS`, `85 <= score < 95 => REVIEW`, `score < 85 => FAIL`; round only for presentation. This avoids a platform-sensitive decision at a floating boundary. Exact and normalized equality should retain their distinct match method.

Missing expected translation, empty expected text, empty recognized text, or a normalized-empty value must produce `UNVERIFIED` with a null score. No OCR candidate with a nonempty expected value is an unmatched `FAIL`. Unsupported locale/model and processing/engine failure require separate outcomes with null quality. None may be converted to a synthetic fuzzy score. Candidate matching is one-to-one: reserve exact matches first, then normalized matches, then perform deterministic global assignment for remaining fuzzy candidates. Any one-to-many region assembly must be contract-defined before implementation.

The read-only CPython probe demonstrated why NFC and NFKC must remain distinct: NFC composed `e + U+0301` to `é` and decomposed Hangul Jamo to `한`, while preserving full-width `ＡＢＣ １２３`; NFKC changed the latter to `ABC 123` and changed NBSP to ordinary space. This probe did not execute RapidFuzz.

## Fixture and real-engine validation strategy

### Committed fixture package

Use synthetic, non-user screenshots only. Commit small PNG inputs plus UTF-8 JSON ground truth under the future approved `tests/ocr/` scope. Each manifest records fixture ID, SHA-256, width/height, locale tag, exact expected text, polygon ground truth, render source description, font name/version/license, and allowed geometric tolerance. No actual QA data or production screenshots enter Git.

Use redistributable fonts, preferably Noto family under SIL OFL-1.1, with license attribution and exact font-file hash recorded at generation time. Generated PNGs are the stable test inputs; generation scripts are provenance aids and must not make ordinary tests depend on host fonts.

Minimum fixture matrix:

- every core locale: English, Korean, Japanese, Simplified Chinese, Traditional Chinese;
- mixed script and digits: locale text plus ASCII numbers, decimal/percent/time/currency examples;
- normalization: NFC/NFD Latin accents, composed/decomposed Hangul, full-width Latin/digits, NBSP/tab/newline, case, punctuation and variation-sensitive examples;
- layout: one line, multiline, two close regions, edge/corner boxes, 720p/1080p/high-resolution scale, low contrast, antialiasing, small glyphs, partial crop;
- orientation: 0° and 180° required; 90°/270° and vertical Japanese as capability probes with explicit expected support/unsupported disposition;
- negative cases: blank/no-text image, decorative texture that must not become text, visually similar `0/O`, `1/I/l`, and one low-confidence sample;
- locale mismatch: run each locale profile against at least one neighboring-script fixture to expose silent fallback and false positives.

### Deterministic verification fixtures independent of OCR

Feed stored synthetic OCR records directly into verification tests so threshold and normalization failures are isolated from model drift. Include raw/normalized/fuzzy paths, missing expected translation, missing OCR, raw-empty and normalized-empty strings, duplicate candidates, one-to-one global assignment, and engine-error separation.

Boundary vectors for `Levenshtein.normalized_similarity` should include equal-length 20-character strings with 0, 1, 2, 3, and 4 substitutions. With the documented maximum-length normalization these target 100, 95, 90, 85, and 80 and exercise both inclusive boundaries. Confirm the exact API values and the equivalent rational comparisons against pinned RapidFuzz on Windows and Linux before recording PASS. Also include scores just above/below 95 and 85 using longer strings; do not compare rounded UI values.

### Real-engine acceptance runs

After contract acceptance and PM ownership approval:

1. Resolve and hash-lock the CPU dependencies in clean CPython 3.12 environments on Windows x86-64 and Linux x86-64.
2. Prefetch only the declared detector/recognizer/orientation artifacts, record source, size, SHA-256 and license, then disable network for test execution.
3. Run each committed image through each declared locale profile. Record raw JSON, package/model hashes, elapsed time, peak memory, CPU/thread settings, and original screenshot hash.
4. Assert text, per-region polygon within declared tolerance, confidence domain and region-array alignment. Do not require byte-identical floating output across OS unless measured evidence supports it.
5. Run deterministic verification fixtures against pinned RapidFuzz and exact threshold boundaries.
6. Re-run the full matrix after process restart and model-cache reuse; missing/corrupt model cache must produce explicit engine/configuration errors.
7. Preserve failures and review false positives/negatives. Do not relax detector, confidence, or match thresholds to convert a failing locale fixture into PASS.

Suggested resource gate before choosing medium models: measure cold-start model load, warm single-image latency, peak resident memory, and 10-image sequential throughput on the actual Windows and Linux CPU environments. Documentation benchmark numbers use different hardware and are planning inputs only. A reasonable initial download/storage estimate is at least the PaddlePaddle wheel (about 105 MB Windows or 195 MB Linux) plus PaddleOCR/PaddleX/transitives and roughly 147 MB for v6 medium detection+recognition, 14 MB Korean recognition, and optional orientation weights; actual installed size and cache size remain NOT_RUN.

## Licenses and supply-chain evidence

- PaddleOCR, PaddlePaddle, and PaddleX: Apache-2.0 according to their official package pages.
- RapidFuzz: MIT.
- `opencv-python-headless` build scripts: MIT; OpenCV: Apache-2.0; bundled FFmpeg: LGPL-2.1; inspect `LICENSE-3RD-PARTY.txt` for the selected wheel.
- Fixture fonts: record and ship the relevant SIL OFL-1.1 text when using Noto assets.
- Model weights: official pages provide downloads but the reviewed material did not establish a separate per-model license statement. PM/Architect must require model-artifact license/provenance review before redistribution or image publication. Do not infer that library Apache-2.0 automatically covers every hosted weight.

For every selected wheel/model/font, capture artifact URL, version/name, SHA-256, byte size, license source, retrieval date, and whether redistribution is permitted. Trusted-publishing status is not a substitute for hashes; the PaddleOCR 3.7.0 PyPI wheel page reports SHA-256 `c0f0a81ad4112727f30c6fcf986ac0ef6a120d31ee0991a01fae0357ee32d338`.

## Commands and results

| Command/check | Environment | Result |
| --- | --- | --- |
| Read `AGENTS.md`, role prompt, Phase 3 activation, PROJECT_STATE/TASKS/ACCEPTANCE/DECISIONS, phase doc, current packaging/Dockerfiles | Current root | PASS; prep READY, OCR implementation blocked, all Phase 3 AC NOT_RUN. |
| Focused `rg` scans for existing OCR/normalization/runtime references | Current root | PASS; no OCR implementation/dependencies found. |
| Bundled Python 3.12.14 `unicodedata` NFC/NFKC probe and `find_spec("rapidfuzz")` | Windows 64-bit, Python 3.12.14 | PASS for probe; RapidFuzz absent. This is not OCR or fuzzy validation. |
| `.venv\Scripts\python.exe --version` | Existing project venv | FAIL to launch: referenced user Python path absent. Environment limitation, not product/model failure. |
| Docker image inventory | Current host | Permission denied once; not repeated. Linux runtime remains NOT_RUN. |
| Official package/docs read for PaddleOCR 3.7.0, PaddlePaddle 3.3.1, PaddleX 3.7.2, OpenCV headless 5.0.0.93, RapidFuzz 3.14.6 | Background browser, read-only | PASS as compatibility research; no external write/download/login. |
| Package install, resolver lock, model download, Paddle run check, OCR inference, RapidFuzz threshold tests, Windows/Linux parity, resource benchmark | Not authorized before contract/ownership gate | NOT_RUN. |

Input hashes at preparation time:

| Input | SHA-256 |
| --- | --- |
| `AGENTS.md` | `060df1fb9c37e93306d0bae6d6aa085214fd9f7cd55663f483924751b8148bc6` |
| `docs/prompts/05_ocr_verification.md` | `564238023e5c7ae3de5c4f1fe76ee107394516d4a58b36540ee3e493ebfe8e17` |
| `.orchestration/handoffs/PHASE-3-activation-01.md` | `4c502c3abdec9a51b953c3c71d0f18a0b68a01613cd42f791b7a715dd9ed6588` |
| `.orchestration/TASKS.yaml` | `c3f407e83272257529e870103cad3fa71a7e94408b9a18c2da8310f925a4efb6` |
| `.orchestration/ACCEPTANCE.yaml` | `6a13c6a36f21891a3a1d72af8a2475d8512374571f47019f3f7a99e3530ab9ae` |
| `pyproject.toml` | `0024490e4faf1ca7bb21a25ec0c19fe72486229dd82f394fb157366de43bc003` |

Official sources consulted:

- https://pypi.org/project/paddleocr/3.7.0/
- https://pypi.org/project/paddlepaddle/
- https://pypi.org/project/paddlex/
- https://pypi.org/project/opencv-python-headless/
- https://pypi.org/project/RapidFuzz/
- https://www.paddleocr.ai/latest/en/version3.x/installation.html
- https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html
- https://www.paddleocr.ai/latest/en/version3.x/module_usage/text_detection.html
- https://www.paddleocr.ai/latest/en/version3.x/module_usage/text_recognition.html
- https://www.paddleocr.ai/latest/en/version3.x/module_usage/textline_orientation_classification.html

## Completion and next condition

Preparation is complete: compatibility, model/language split, coordinate/confidence constraints, normalization/threshold fixture design, resource/licensing risks, and reproducible post-gate validation are submitted. AC-P3-01..04 remain NOT_RUN and `OCR-001` remains BLOCKED.

Architect 02 should incorporate or explicitly disposition the eight contract questions and pin the result schema/coordinate/confidence/locale/model identities. Reviewer 08 must independently accept the exact contract. PM 01 must then approve file/dependency ownership, including owner03's `pyproject.toml` edit path. Only after both gates should role05 install in disposable environments, generate the lock/model manifest, implement under `worker/ocr/`, `worker/verification/`, and `tests/ocr/`, and execute the real-engine matrix.
