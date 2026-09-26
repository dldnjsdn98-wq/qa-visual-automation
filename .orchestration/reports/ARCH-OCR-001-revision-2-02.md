# ARCH-OCR-001 revision2 / Architect02

Date: 2026-09-25 KST
Issue: P3-OCR-DEP-001
Status: READY_FOR_REVIEW requested, focused contract amendment only.
Difficulty: high, bounded runtime/dependency policy. Requested Sol/high; actual model unverified.
Branch / commit: null / null.

## Authorization and scope

PM explicitly reactivated ARCH-OCR-001 to resolve the concrete OpenCV dependency conflict. Preserve accepted revision1 byte-for-byte; amend only canonical contract header and section10.3 OpenCV policy; write revision-specific report/handoff. No product/shared packaging/PM files changed. No installation, model acquisition, services, security changes, commit/push/deployment or DB actions.

Artifacts:
- docs/architecture/phase-3-ocr-contract-revision-1.md (new exact archive)
- docs/architecture/phase-3-ocr-contract.md (revision2 candidate)
- .orchestration/reports/ARCH-OCR-001-revision-2-02.md
- .orchestration/handoffs/ARCH-OCR-001-revision-2-02.md

Accepted revision1 SHA256: 46940dd1dd7775422213b2ba422b63650f4e83740e034cf29dc83f23970acb82.
Revision2 SHA256: 478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44.
Prior author/reviewer reports and acceptance evidence remain unchanged. Revision2 is not independently accepted.

## Evidence and reason

Independently read .pytest_cache/phase3-ocr-05/windows-resolver-report.json and verified SHA256 dce46dc6dc9434a00a0137d8ea484e3e9f44a34ca02a21d82beb0f049a9cdb57. Report environment is Windows11 AMD64 CPython3.12.14. PaddleOCR3.7.0 resolves PaddleX3.7.2; its requires_dist explicitly contains opencv-contrib-python==4.10.0.84 for ocr-core. The report selects that distribution. This is a real dependency-versus-contract conflict, not a sandbox/permission failure.

Reported artifact SHA256 values:
- PaddleX3.7.2: f1678bf650bbaccfd8f0d4e49d0ae631b4685c829fdae6e802ccd90d4fcb9a7f
- Windows OpenCV contrib4.10.0.84: 47ec3160dae75f70e099b286d1a2e086d20dac8b06e759f60eaf867e6bdecba7

These were verified as resolver report contents; this task did not independently fetch or hash the wheel bytes or run the resolver. Windows evidence is not Linux compatibility or native import/inference evidence.

## Decision and alternatives

A selected: use the upstream metadata-required single official opencv-contrib-python==4.10.0.84 distribution with paddlex[ocr-core]==3.7.2 as a qualification candidate. This resolves the unnecessary headless packaging requirement without creating an inconsistent dependency graph. Non-headless packaging does not require application GUI usage, but its native dependencies and actual display-free execution must be proven.

B rejected: substituting a headless distribution, suppressing dependencies, or allowing pip-check exceptions. A similarly named package sharing cv2 does not satisfy the distinct declared distribution requirement.

C deferred: alternative engine/PaddleX baseline only if candidate A fails concrete platform/native/resource/real-inference qualification. No current evidence justifies expanding this amendment into an engine redesign.

## Qualification conditions and impacts

After independent exact revision2 acceptance and PM activation:
- Resolve/hash-lock each OS separately and require clean pip check; install exactly one cv2 distribution.
- On unattended Windows and display-server-free Linux, prove cv2/native import, actual offline OCR, startup/shutdown and existing300s/2GiB/CPU-thread limits.
- Inspect application/adapter call paths for HighGUI/window/display usage and verify normal worker execution needs no interactive desktop/display server. Merely selecting a package cannot guarantee this.
- Record native libraries and all artifact licenses/digests in the approved disposable runtime; no unapproved global dependency/security changes.
- Missing native libraries or incompatible platform resolution leave that platform/profile UNAVAILABLE. No fallback wheel, mutable profile repointing or false AVAILABLE.
- The affected installation/model-acquisition lane remains stopped until review+PM activation. Already-authorized independent matching/geometry/backend/frontend work may continue.

Impact is limited to10.3 package policy and its qualification requirements. Header identifies revision2 and links the exact archive. No changes to engine versions/model pair, locale scope, Unicode15, normalization, rational thresholds, matching assignment, geometry, API, persistence/fencing, frontend behavior, resource limits or acceptance matrix. These existing rules still apply. Actual runtime qualification is NOT_RUN by Architect02.

## Actual checks

Environment: C:/Dev/qa-visual-automation, Windows PowerShell, Node v24.19.0.
- Get-FileHash -Algorithm SHA256 .pytest_cache/phase3-ocr-05/windows-resolver-report.json: exit0, expected digest matched.
- Node JSON parse/filter of resolver environment, selected metadata/requires_dist and archive digests: exit0, direct OpenCV requirement confirmed.
- Guarded Node archive/write: exit0; refused overwrite of any existing archive and required exact accepted source hash before mutation. Archive retains original bytes.
- Node exact reverse-diff/static script below: exit0 PASS; reversing only declared header/OpenCV replacements reproduces all revision1 text exactly, archive hash matched,7 links resolve,22 fault rows/4 AC markers unchanged, JSON fence valid.
- git diff --no-index -- docs/architecture/phase-3-ocr-contract-revision-1.md docs/architecture/phase-3-ocr-contract.md: exit1 expected because files differ; output contains only header and10.3 paragraph hunks. Git emitted future LF-to-CRLF warnings; no conversion applied by this read-only comparison, exact byte hash verified.
- No product tests rerun because this is dependency-policy documentation only. Actual pip resolver/pip check/package installation/native import/real OCR/model acquisition/Linux parity/resource/GUI tests: NOT_RUN in this task.
- AC-P3-01..04 remain NOT_RUN; static document checks do not establish product acceptance.

Exact check program executed through node -e, with PowerShell single-quote escaping:
```javascript
const f=require('fs'),c=require('crypto'),a=require('assert/strict'),p=require('path');const root='docs/architecture/',old=f.readFileSync(root+'phase-3-ocr-contract-revision-1.md'),current=f.readFileSync(root+'phase-3-ocr-contract.md','utf8');a.equal(c.createHash('sha256').update(old).digest('hex'),'46940dd1dd7775422213b2ba422b63650f4e83740e034cf29dc83f23970acb82');const reverse=current.replace('Document revision 2.','Document revision 1.').replace('Status: revision2 candidate; independent focused review and PM activation required for the changed runtime baseline. Revision1 remains the accepted historical baseline; no product acceptance.\nRevision1 archive: [exact accepted original](phase-3-ocr-contract-revision-1.md), SHA256 46940dd1dd7775422213b2ba422b63650f4e83740e034cf29dc83f23970acb82.','Status: proposed executable contract; independent REVIEW-ARCH-OCR-001 and PM file claims required before implementation. No product acceptance.').replace("Candidate PaddleX baseline is paddlex[ocr-core]==3.7.2 with exactly one OpenCV distribution, opencv-contrib-python==4.10.0.84, as required by its dependency metadata. Do not co-install any other opencv-python/opencv-contrib-python/headless distribution. Headless substitution, dependency suppression and pip-check exceptions are not permitted for this baseline. Fully hash-lock each OS-specific resolution and require clean pip check; the Windows resolver report does not qualify Linux, native-library loading or actual inference. Qualify the non-headless wheel in unattended Windows and display-server-free Linux execution: cv2 import/native-library readiness, real offline OCR, process startup/shutdown, existing 300s/2GiB/CPU-thread limits, and artifact/native-library license provenance must pass. Application and adapter code must not invoke HighGUI/window/display APIs; qualification must inspect those call paths and verify that ordinary worker execution needs no interactive desktop or display server. Package inclusion alone is not a guarantee that GUI calls cannot occur. Record required native libraries and qualify them within the approved disposable runtime; no unapproved global library/security changes. Missing native libraries or incompatible platform resolution leave the affected platform/profile UNAVAILABLE; no silent alternate wheel or unreviewed baseline substitution. Every qualified manifest must identify the exact selected package/native artifacts; never repoint an existing immutable profile identity. These changed baseline provisions take effect only after independent acceptance of document revision2 and PM activation; until then the affected installation/model-acquisition lane remains stopped. Other already-authorized, unaffected implementation work may continue.","PaddleX and exactly one OpenCV headless wheel family/version must be determined by clean resolver evidence and fully hash-locked; do not preselect an incompatible latest OpenCV. Resolver incompatibility requires reported new profile/baseline review, never a silent version substitution.");a.equal(reverse,old.toString('utf8'));const links=[...current.matchAll(/\]\(([^)]+)\)/g)];for(const m of links)a.ok(f.existsSync(p.resolve(root,m[1])));a.equal((current.match(/^\| O\d\d \|/gm)||[]).length,22);for(let i=1;i<=4;i++)a.ok(current.includes('AC-P3-0'+i));for(const m of current.matchAll(/```json\n([\s\S]*?)```/g))JSON.parse(m[1]);console.log(JSON.stringify({result:'PASS',archive_exact:true,only_header_and_OpenCV_replacement:true,links:links.length,fault_rows:22,ac_markers:4,revision2_sha256:c.createHash('sha256').update(current).digest('hex')}));
```

## Submission and outstanding work

Submit exact revision2/archive/report/handoff hashes to PM01 for existing Reviewer08 focused review. Do not re-audit unaffected sections or infer baseline qualification from contract acceptance. Outstanding: independent amendment acceptance, PM activation, then03/05 runtime/dependency/native/library/license/offline/resource qualification. No new app task or subagent was created for this localized evidence-backed wording change. Parent independently verified the evidence and exact scope.
