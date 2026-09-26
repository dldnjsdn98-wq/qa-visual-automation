# REVIEW-ARCH-OCR-001 revision 2 / Reviewer 08 focused contract review

Date: 2026-09-25 KST  
Reviewer: 08 Senior Reviewer  
Issue: `P3-OCR-DEP-001`  
Activation: `.orchestration/handoffs/REVIEW-ARCH-OCR-001-01.md`

## Disposition

**ACCEPTED — exact P3-OCR-v1 document revision 2, focused contract amendment only.**

The revision 2 header and section 10.3 amendment correctly replace the revision 1 headless-OpenCV assumption with the upstream resolver-required `paddlex[ocr-core]==3.7.2` and single `opencv-contrib-python==4.10.0.84` qualification candidate. The wording closes dependency-override shortcuts and makes actual Windows/Linux native, display-free, offline, resource and license qualification mandatory before a profile may be `AVAILABLE`.

No required-change finding was established in the bounded amendment. This acceptance does not qualify the package set, authorize installation/model acquisition by itself, accept implementation, or mark any Phase 3 product criterion PASS. `AC-P3-01` through `AC-P3-04` remain `NOT_RUN`.

## Exact reviewed artifacts

| Artifact | SHA-256 | Result |
| --- | --- | --- |
| Canonical `docs/architecture/phase-3-ocr-contract.md` revision 2 | `478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44` | MATCH |
| Archived `docs/architecture/phase-3-ocr-contract-revision-1.md` | `46940dd1dd7775422213b2ba422b63650f4e83740e034cf29dc83f23970acb82` | MATCH; byte-exact accepted revision 1 |
| `.orchestration/reports/ARCH-OCR-001-revision-2-02.md` | `8d1dafe33f9384315d5086aade4283f25eda2a205b813dfdb7edacda8f236f0a` | MATCH |
| `.orchestration/handoffs/ARCH-OCR-001-revision-2-02.md` | `2bb8bcf8d59acfc21290436dab05b87c36a6e2b76f0dc63ac7946151ee9fd82f` | MATCH |
| `.pytest_cache/phase3-ocr-05/windows-resolver-report.json` | `dce46dc6dc9434a00a0137d8ea484e3e9f44a34ca02a21d82beb0f049a9cdb57` | MATCH; static resolver evidence only |

Revision 1 Reviewer report/handoff remain unchanged and authoritative for all unaffected contract sections.

## Focused findings

No open finding.

### Resolver evidence and selected distribution

- The resolver JSON identifies Windows 11 AMD64, CPython 3.12.14.
- `paddleocr==3.7.0` selects `paddlex[ocr-core]>=3.7.0,<3.8.0`; the resolved PaddleX version is `3.7.2`.
- PaddleX 3.7.2 metadata contains the exact requirement `opencv-contrib-python==4.10.0.84; extra == "ocr-core"`.
- The selected Windows wheel is `opencv-contrib-python==4.10.0.84`, with resolver-recorded SHA-256 `47ec3160dae75f70e099b286d1a2e086d20dac8b06e759f60eaf867e6bdecba7`.
- This proves the revision 1 headless-only assumption conflicts with the observed upstream dependency metadata. It does not prove Linux resolution, wheel-byte integrity beyond the resolver record, native import, inference or runtime suitability.

### Dependency integrity and bypass prevention

Revision 2 requires the upstream metadata-selected non-headless contrib distribution and exactly one `cv2` distribution. It expressly forbids co-installing another OpenCV family, headless substitution, dependency suppression and pip-check exceptions. `pip --no-deps` is therefore prohibited by the broader explicit dependency-suppression rule; there is no allowed path to replace the required distribution merely because another package exports the same `cv2` module.

Each OS must have its own complete hash-locked resolution and clean `pip check`. The Windows resolver cannot be reused as Linux, native-loading or actual-inference proof. Incompatible resolution requires a separately reviewed baseline rather than an unrecorded version change or fallback wheel.

### Runtime qualification and fail-closed availability

Before `AVAILABLE`, the candidate must pass all of the following in approved disposable environments:

- unattended Windows and display-server-free Linux resolution and native `cv2` import;
- real offline OCR with process startup and shutdown;
- the existing 300-second whole-attempt, 2 GiB child RSS and one-inference-thread baseline limits;
- application and adapter call-path inspection for HighGUI/window/display APIs, plus ordinary worker execution without an interactive desktop or display server;
- exact wheel/native-library/model artifact identities, hashes and license provenance;
- clean failure to `UNAVAILABLE` when native libraries, platform resolution or qualification evidence is missing.

The immutable profile rule remains intact: qualified manifests identify exact package/native artifacts, and an existing profile identity cannot be repointed. Package inclusion alone is explicitly insufficient evidence that GUI APIs are unused or that the runtime works headlessly.

### Scope and compatibility

Independent line-boundary comparison confirmed that only the revision header/archive link and the section 10.3 OpenCV baseline paragraph changed. All text before and after that paragraph is byte-equivalent to the accepted revision 1 after accounting for the declared header insertion/replacement.

No locale, model pair, Unicode 15 normalization, rational threshold, global assignment, geometry, API/Web, persistence/fencing, resource limit or acceptance-matrix meaning changed. The archive link resolves, seven local document links resolve, and revision 1 remains preserved at its accepted hash.

## Actual static verification

Environment: Windows PowerShell and Node `v24.19.0`, explicit root `C:\Dev\qa-visual-automation`.

| Check | Result |
| --- | --- |
| Read current `AGENTS.md`, Reviewer08 prompt, focused activation, revision 2 contract, revision 1 archive and Architect amendment report/handoff | PASS |
| Hash all five reviewed artifacts | PASS; exact values above |
| `git diff --no-index --unified=8` between revision 1 archive and canonical revision 2 | Expected exit 1 for differences; only header/archive-link and section 10.3 paragraph hunks observed |
| Independent Node boundary comparison | PASS; unchanged contract segments before/after the amendment are exact |
| Resolver JSON parse | PASS; PaddleX 3.7.2 `ocr-core` exact OpenCV requirement and selected OpenCV 4.10.0.84 record confirmed |
| Qualification-clause inventory | PASS; single distribution, no co-install/headless/dependency suppression/pip-check exception, per-OS hash lock, clean pip check, display-free/native/offline/start-stop/resource/HighGUI/license/UNAVAILABLE/immutable-profile gates present |
| Local links | PASS: 7 links, 0 missing |

Independent static-check output:

```json
{"result":"PASS","scope":"header and section10.3 only","archive_sha256":"46940dd1dd7775422213b2ba422b63650f4e83740e034cf29dc83f23970acb82","revision2_sha256":"478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44","resolver_sha256":"dce46dc6dc9434a00a0137d8ea484e3e9f44a34ca02a21d82beb0f049a9cdb57","paddlex":"3.7.2","opencv":"4.10.0.84","links":7,"unchanged_before_and_after":true,"qualification_terms":18}
```

## NOT_RUN and remaining gates

- Package installation, fresh resolver execution, wheel download/hash verification, `pip check`, native-library inspection and `cv2` import: `NOT_RUN` by focused contract-review scope.
- Model acquisition, Paddle runtime check, real offline OCR, startup/shutdown, network-disable validation, Windows/Linux parity, HighGUI runtime instrumentation and license approval: `NOT_RUN`.
- 300-second timeout, 2 GiB RSS enforcement and CPU-thread/resource measurement: `NOT_RUN`.
- Product source/tests, PostgreSQL, Backend API, Frontend/browser and end-to-end Web: `NOT_RUN`.
- `AC-P3-01`, `AC-P3-02`, `AC-P3-03`, `AC-P3-04`: `NOT_RUN`.
- Resolver metadata and contract static checks are not product or model qualification PASS.

## Scope, changes and next gate

Changed files are this report and `.orchestration/handoffs/REVIEW-ARCH-OCR-001-revision-2-08.md` only. Revision 1 review artifacts, contract/archive, product source, dependencies, tests and PM state were not modified. Branch/commit: `null` / `null`. No installation, model download, DB action/reset, service execution, Commit, Push, deployment, security/account change, IP check, Phase 4 or mobile work occurred.

Requested model was `gpt-5.6-sol` / high; actual model identity was not exposed and remains `unverified`. The amendment was sufficiently localized and the existing evidence complete, so no duplicate sidecar was started.

PM01 may record revision 2 as the accepted canonical contract and resolve the contract-text portion of `P3-OCR-DEP-001`. PM must separately reactivate the affected runtime acquisition lane. Owners 03/05 must then produce the clean per-OS lock, actual native/import/offline OCR/resource/license evidence before any affected profile is `AVAILABLE`. Final implementation review and all four product ACs remain pending.

