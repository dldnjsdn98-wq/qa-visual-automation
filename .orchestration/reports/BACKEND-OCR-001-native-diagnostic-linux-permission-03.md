# BACKEND-OCR-001 Linux permission analysis — role 03 sidecar

## Scope and disposition

This is read-only permission-context analysis for the Linux lane resumed by `.orchestration/handoffs/PHASE-3-native-diagnostic-resume-01.md`. No Docker command, container, build, denied-path probe, credential/config read, permission escalation, ACL/security/identity change, `DOCKER_CONFIG` change, source edit, or test was performed by this sidecar. Linux native qualification remains **APPROVAL_PENDING / NOT_RUN**. The parent can continue its disjoint Windows work independently.

## Evidence classification

The immutable failed capture is:

- `.orchestration/reports/BACKEND-OCR-001-runtime-conformance-evidence-03/linux-diagnostic-build-01.json`
- `.orchestration/reports/BACKEND-OCR-001-runtime-conformance-evidence-03/linux-diagnostic-build-01.log`
- recorded command: `docker build -f backend/Dockerfile.test -t qa-backend-ocr-conformance-diagnostic:20260925a .`
- start/end: `2026-09-25T13:58:27.942481Z` / `2026-09-25T13:58:28.212721Z`
- exit: `1`; log SHA-256: `59cf229a5fa5e5eaeeccb8421e8ec999fb23a852c51adea4a7e24b564762dcf3`
- all 15 captured source hashes matched before/after; no image-build step is evidenced as having started or succeeded.

The exact denied targets, quoted only as paths from the existing log, are:

1. `C:\Users\dldnj\.docker\config.json` — Docker emitted two read warnings: `open ...: Access is denied.` The file contents were not read or inspected.
2. `C:\Users\dldnj\.docker\buildx\instances` — Docker terminated with `CreateFile ...: Access is denied.` No directory inspection or retry was performed.

This is an **OS filesystem denial surfaced by the already-started Docker CLI**. The JSON capture's timestamps, argv, exit code and Docker-authored log prove that the command crossed command dispatch and that Docker attempted normal configuration/buildx filesystem operations. It is therefore different from:

- a sandbox/tool pre-dispatch denial, where the Docker child would not start and this Docker-authored capture would not be produced; and
- an approval-reviewer rejection, where the requested elevated operation would be withheld rather than return Docker's exit code and Win32 `Access is denied` messages.

The available evidence does **not** establish whether the Win32 denial arose from host ACLs, the sandboxed process token/access boundary, or another host filesystem policy. Determining that would require forbidden inspection or security changes. No current auto-review rejection is evidenced for this Docker build. If the ordinary approval request below is rejected before execution, that future event must be recorded separately as an approval/reviewer rejection and must not be relabeled as this filesystem failure.

## Exact minimal ordinary approval operation for the parent

From repository root `C:\Dev\qa-visual-automation`, request normal product approval for exactly this one command, outside the restricted filesystem sandbox, with no reusable prefix inferred or claimed:

```powershell
.\.pytest_cache\agent-clean-win\Scripts\python.exe .orchestration/reports/BACKEND-OCR-001-native-diagnostic-capture-03.py linux-diagnostic-build-01 -- docker build --pull=false --file backend/Dockerfile.test --tag qa-backend-ocr-native-diagnostic:20260925a .
```

Suggested approval question: `Allow this one captured Docker build to use Docker's existing user configuration/buildx state and build a new diagnostic image from the current repository source with backend/Dockerfile.test?`

This is the smallest operation that preserves the original authorized purpose while producing reviewable evidence:

- existing recipe: `backend/Dockerfile.test`;
- current source/context: repository root `.` at the moment the approved command starts;
- new image tag: `qa-backend-ocr-native-diagnostic:20260925a`, distinct from the historical successful `qa-backend-ocr-rework-diagnostic:20260925` and the failed conformance tag;
- new immutable capture namespace: `.orchestration/reports/BACKEND-OCR-001-native-diagnostic-evidence-03/` via the existing capture script;
- capture label: `linux-diagnostic-build-01`, currently absent in that new namespace;
- source/context hashes and source-before/source-after are recorded by the wrapper; stdout/stderr go to the new log.

The request must contain no `DOCKER_CONFIG`, alternate identity, ACL, ownership, security setting, credential operation, or denied-path probe. It authorizes only the captured build. Image inspection, container execution, native tests, pressure/timeout/cleanup checks, and actual OCR remain separate unexecuted operations requiring the parent to assess and request only after a successful current-source build.

## Known, unknown, and historical authorization caution

Known: a historical captured build of `qa-backend-ocr-rework-diagnostic:20260925` using `backend/Dockerfile.test` succeeded earlier, and historical Docker image inspection/run evidence exists. That image predates the current source hashes and cannot substitute for a new build. The failed current build reached Docker but was blocked before useful build evidence by the two filesystem targets above.

Unknown until the approved command actually runs: whether ordinary out-of-sandbox execution can access Docker's existing config/buildx state; whether the daemon/build backend is available; whether the current context builds; the resulting image ID/digest; and whether later Linux native or actual-OCR qualification passes. A successful approval decision alone proves none of these.

Historical successful Docker executions, user continuation of the diagnostic scope, and any saved or displayed command-prefix grants are context only. They do not authorize this exact new command, do not waive product approval, and do not prove access to the denied paths. The parent should request the exact operation above through the normal approval mechanism and preserve an approval rejection, filesystem denial, build failure, or success as distinct outcomes.

## Sidecar checks actually performed

- Read `AGENTS.md`, `docs/prompts/03_backend.md`, and `.orchestration/handoffs/PHASE-3-native-diagnostic-resume-01.md`.
- Read the existing failed JSON/log and historical capture metadata/scripts without reading Docker credential/config contents.
- Compared prior successful build/image capture metadata with the failed current-source attempt.
- Tests/builds/containers: **NOT_RUN** by this sidecar.

