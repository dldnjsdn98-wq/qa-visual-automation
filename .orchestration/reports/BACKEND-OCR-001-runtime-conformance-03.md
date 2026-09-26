# BACKEND-OCR-001 conformance correction / Backend03

Status: BLOCKED_NATIVE_QUALIFICATION_NOT_READY_FOR_REVIEW. Local validation complete for this checkpoint; not independent acceptance. Branch/commit: null.

PM activation: `.orchestration/handoffs/PHASE-3-runtime-conformance-resume-01.md`.
Architect clarification report SHA-256 `8eed0822dee5781b8fb23187f1a24a1d1ff1014a14f5bee59e2bc99f42795375`, handoff `eba017cc6d925bbaaf2477d358131e9a9c04a000e78462b3d72a8220c5c4cfee`. Accepted revision2 remains `478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44`.

## Work and ownership

Existing agents reused: Einstein (requested Astra/medium) owns runner/source/optional parent runtime and minimal verification-job guard; Galileo (requested Astra/medium) owns only containment helper; Fermat (requested Sol/high) owns five focused test files. Requested settings are known from tool creation; independent actual-runtime model attestation is unavailable. Parent03 owns interface integration, captured execution and evidence. No duplicate writer. Terra evidence resumption hit concurrency limit and did not edit this report; parent maintains it.

A usage/rate-limit interruption occurred before most changes landed. On explicit user resumption, each existing agent was resumed once. Preserve this as execution interruption, not a failed product test. No automatic model downgrade.

The agreed helper interface is `launch_contained(argv, *, env, cwd, memory_limit_bytes)`, returning binary stdin/stdout, pid, poll(), memory_exceeded(), stop(absolute containment deadline), close(). Earlier prepare/attach interface proposals were superseded before integration.

Parent owns all DB credentials, metadata reads, mutations and fresh-primary recovery. Child is a standalone isolated Python script with explicit safe environment, clean working directory, immutable bounded JSON DTO and framed pipe protocol; no DB configuration imports or credentials. One productive300s budget is separate from a measured bounded containment tail. Already-issued valid COMMIT may settle later. Uncertainty forbids compensation/new claims. One timeout failure requires confirmed stopped workload, no outstanding/uncertain mutation and a valid fence.

## Containment scope and pending evidence

Linux uses existing dedicated read-only cgroup-v2 runtime facilities; no cgroup delegation/host edits. `linux-memory-preflight-01` observed `memory.max=2147483648`, `memory.swap.max=0`, namespace membership `0::/`. This is configuration evidence only. The cap includes parent, DB executor, child and descendants; parent OOM death must be distinguished from a surviving parent's classified child failure and recovered by durable lease semantics.

Windows focused Architect02 follow-up conditionally admits a verified hard working-set maximum plus child-only Job ActiveProcessLimit1 and no breakaway. Job committed-private memory cap alone is not RSS conformance. Effective limits must be established before useful work and rechecked before output acceptance. Qualification must include shared/file-mapped pages, threads and attempted descendants; no inferred PASS from sampled peaks or prior OCR05 qualification.

OCR05 supplied known Windows pinned venv/model-root provenance, not current Backend03 access authorization. Historical shell model-cache traversal denial is preserved. No repeated traversal, copying, reacquisition, ACL or host-security change. Any current execution needing approval follows the ordinary tool approval boundary; a denied action is not bypassed through another runtime/path.

## Verification ledger

| Required slice | Status |
| --- | --- |
| Parent authority / credential-free actual child | Deterministic authority checks PASS; actual corrected child NOT_RUN |
| Productive deadline, blocked source and complete owned cleanup | Deterministic deadline checks PASS; native blocked-source/cleanup NOT_RUN |
| Valid pre-deadline commit acknowledged late / locked recovery | Service slice PASS; actual runner integration pending |
| Uncertain commit: no compensating mutation or new claim | Service + runner scheduling slices PASS; native integration NOT_RUN |
| Timeout failure stop/uncertainty/fence prerequisites | Scheduling and real PostgreSQL slices PASS; native stop prerequisites NOT_RUN |
| Windows real reduced-limit short peak/mapped/thread/descendant | NOT_RUN |
| Linux real reduced-limit short peak/tree/parent-OOM scope | NOT_RUN |
| Unavailable containment fail-closed behavior | Typed safe/unknown launch fault tests PASS; Windows actual count violation FAIL/UNAVAILABLE |
| Corrected Linux/Windows affected real runtime | NOT_RUN |
| Fresh source manifest, Worker42 match, raw evidence inventory | PASS integrity only; new image build BLOCKED |

Existing cleanup same-cause count is2 from the prior draft. Do not run the unchanged failed suite. The next relevant execution requires reviewed corrective changes; a third same-cause failure stops that path for reassessment. No prior result is promoted to corrected-runtime qualification.

Prior blocked report/handoff/97-file manifest/27-file inventory remain immutable. New captures live only in `BACKEND-OCR-001-runtime-conformance-evidence-03`; command JSON includes timestamps, exact argv, exit status, relevant source hashes and configuration hashes without values. AC-P3-01..04 remain NOT_RUN. No Frontend04 or Reviewer08 activation, commit, push, deployment, shared DB reset or user-data deletion.

## Captured incremental execution

`windows-db-boundary-01`: 10 passed, one existing deprecation warning, 1.10s. Real isolated PostgreSQL commit/recovery with an explicitly synthetic local-clock boundary; includes confirmed commit acknowledged late, lost acknowledgement, unresolved recovery without compensation, guard before database access/after begin, and proven rollback after deadline without a second finalize. No child or native cleanup execution. Test-file SHA-256 `67b9894bde088b36c712cfb4aaf24061a0f22039b17074949edfbad1b9a5f1e4`; service SHA-256 `060fab9f69e60500d92b1f5b4e295bd26a1fdde33b48f50f50fee90f2e0518c3`; both stable across capture. Log SHA-256 `5c02de9b4ecd09fbaf0a9448e56bd798c908fff2b49144b2ecd2caaaefb5ee66`; exact command, timestamps, context hashes and JUnit are adjacent to the log.

Windows pre-execution review also identified the venv executable redirector risk: a redirector that spawns the real interpreter is incompatible with ActiveProcessLimit1. The proposed direct base interpreter with exact pinned-venv bootstrap must prove executable/prefix/site/package/native identity and absence of an extra process; this is not permission to change dependencies, relax the process limit, or bypass model access denial. Native tests remain pending that correction and review.

## Continuation corrections and preserved failures

The shared admission provider is `backend/app/workers/ocr_admission.py`, with bounded raw-byte content pinning and exact profile/digest/target/release checks. API listing and new creation consult one request-scoped snapshot; replay/conflict precedes admission and unknown profiles stay422. Canonical qualification status QUALIFIED, canonical production eligibility, and document eligibility remain mandatory independently of admission. API-local platform mismatch is not worker-deployment qualification. The unchanged Worker05 adapter independently rejects unqualified/non-production immutable manifests before native engine work. Synthetic test admission is never a production assertion.

Parent `_launch` distinguishes typed prelaunch failure with `cleanup_confirmed=True` AND `workload_started=False` from unknown cleanup or any attempted workload. Only the former can become durable ENGINE_UNAVAILABLE after the launch slot is consumed; all remaining DB/fence guards apply. Generic exceptions retain unknown-owned scratch and quarantine. Windows whole-Job cleanup proof requires direct process signaled plus a valid query showing zero active processes; a direct-PID wait alone is insufficient. Galileo independently reviewed these corrected handoffs. In-process retention is not durable cleanup proof at interpreter exit.

Protocol corrections preserve consumed-operation uncertainty against secondary memory observations, check deadlines before initial I and V messages, and use a separate16MiB UTF-8 input envelope while retaining the8MiB result cap. Claim mutation guards follow blocking selection/fence reads. No useful-work budget is renewed by late claim acknowledgement.

Windows native boundary captures01 and02 each FAIL (same native-accounting cause count2, separate from historical cleanup count2). On02, ActiveProcesses2 and the own-Job PID list `[31428,109892]` corroborated a second live process despite ActiveProcessLimit1, flags8712 and verified hard working-set max268435456/flags6. Startup count was1; stop confirmed count0 in about0.016s. Accounting layout48 bytes/ActiveProcesses offset40/returned48 matches. Static PE inspection identifies the intended base interpreter as107312 bytes, SHA `dcc090a13a5efa06e2b5ad659d18831d6a72cb3d4c2bd83201df7aa69cad856d`; actual launched image and second-PID identity are not proven. No limit relaxation, third unchanged probe, model execution or permission change occurred. Windows remains UNAVAILABLE.

`linux-diagnostic-build-01` returned exit1 before producing an image: Docker could not read its user config/buildx instance directory (AccessDenied). This is an environment/permission command failure, not a product-test failure. No repeated build, alternate config location, identity change, escalation workaround or old-source-image substitution was attempted. Corrected Linux native and actual model evidence remain NOT_RUN. Previous Linux cgroup preflight is only configuration evidence.

| Capture label (all under runtime-conformance-evidence-03) | Actual result and scope |
| --- | --- |
| windows-deterministic-01 | 34PASS,5deselected; historical scheduling/source snapshot only |
| windows-claim-guard-02 | 12PASS; isolated PostgreSQL selection waits cannot mutate after policy loss |
| windows-admission-db-01 | 3PASS; queued admission revoked/digest mismatch durably fails without child; metadata session already closed |
| windows-admission-provider-01 | 11PASS; malformed/missing/oversized/pin/target/release fail closed |
| windows-protocol-regression-02 | 10PASS; uncertainty, I/V deadlines, large UTF-8 and frame/write boundaries |
| windows-admission-api-01 | 22PASS,3FAIL; fixed synthetic profile ID collided with earlier historical profile rows |
| windows-admission-api-02 | 25PASS; unique per-test ID fixes isolation and full-file order interaction; product service unchanged after01 |
| windows-prelaunch-db-01 | 5PASS; real PostgreSQL with synthetic launcher only; test file changed during capture, explicitly not final source qualification |
| linux-diagnostic-build-01 | BLOCKED,exit1; no image/no Linux native execution |

Every label links to immutable same-basename JSON/raw log and, for pytest, XML. JSON records exact argv/timing/source-before/source-after/config hashes; historical passes are not widened to newer snapshots. The capture helper now includes admission/API/README source identities. Warning from Starlette/httpx is retained; the first admission DB capture additionally warned about default pytest cache access and xunit2 record_property compatibility. Later captures disable cacheprovider and use legacy JUnit. No warning is portrayed as a test failure or suppressed evidence.

Descartes (Sol/high) owned admission/API/docs; Fermat (Sol/high) owned focused tests; Galileo (Astra/medium) owned containment and independent static handoff review. Boole (Terra/high) prepares the evidence inventory helper. Highest/high/low work was actually needed; no medium/lowest task was invented merely to use a model. Parent retained source integration and captured all tests. Requested model settings are not independent runtime attestation.

## Final local checkpoint

`windows-backend-final-01`: **279PASS,15SKIP,0FAIL,1 existing deprecation warning;17.90s**, exit0. Exact command:

```powershell
.\.pytest_cache\agent-clean-win\Scripts\python.exe -m pytest tests/backend -q --tb=short -p no:cacheprovider -o junit_family=legacy --basetemp=.pytest_cache/backend-conformance-final-01 --junitxml=.orchestration/reports/BACKEND-OCR-001-runtime-conformance-evidence-03/windows-backend-final-01.xml
```

Captured through `BACKEND-OCR-001-runtime-conformance-capture-03.py windows-backend-final-01 -- <command>`. Isolated real PostgreSQL fixtures include fresh migrations/downgrade/reapply/metadata parity and durable API/job/recovery tests. No shared DB reset. The15SKIP cases are8 native containment/pressure,5 native runner transport/deadline,2 actual OCR platform integration cases. None is counted as PASS. The four invalid-limit tests reject before workload and do not constitute native enforcement. All15 tracked capture source hashes were stable before/after. Frozen103-source manifest recheck found no subsequent drift.

Final raw evidence SHA-256:

- JSON `cc12df06daf652a9a9588b2d8f20a28fc60c35098ffe89490247cad1fc3426d2`
- Log `bbd02321425beb40f7a96ded6e2ea13210a11732c2b83170ac2d9c536a5167bf`
- JUnit `fb0f8e329c17e451b1145c04bc736e96906fb2dcab73eaf4f858df4afba3c6fc`

`BACKEND-OCR-001-runtime-conformance-source-manifest.txt`:103 files, SHA `73bcf6e6e9eee2069a84ffeb2b20a6902f47187794563e0a72d3aa6259f25e12`, ordinal path/hash-LF aggregate `8a83812f166bfa66d139071021ef6372cad936c05d0b5d31f498cc6f697bd115`. `source-scope-01.json` compares the prior baseline:7 changed existing files,8 added,0 removed,0 outside approved claims,0 frozen-source drift. Worker42 each size/hash matched unchanged; source-manifest SHA `98ea7e81109668dd073ef4f011b4d4c14eff3eea2a96340a00062f6850050b0a`, full-tab-row aggregate `058a445d90b7c50897f77f503a31e7dd425ea71f845a70a40666816e3c7a7b94`.

`final-inventory-01.json` validates14 captures, all referenced raw log hashes/JUnit counts and Worker42; SHA `8fd80076bc0bc72426c27b31cfd6404da76a2054ee2a3ae40dc6afd0dfa0f87a`. Inventory validity means evidence integrity, not product success. It records the prelaunch01 test-source change and does not infer current-source PASS from historical matches. Inventory and source-scope commands perform only read/hash/parse plus new own-evidence output; no tests or containers are run.

Pressure fixture corrections (atomic completion markers, touched descendant0.6cap handshake followed by parent0.6cap pressure, explicit SKIP when sub250ms timing is absent, scoped mapped-page evidence) passed independent static review, including the final atomic boundary/source markers. They remain **NOT_RUN**. Cgroup events cover parent/child/cache aggregate; parent OOM loss and durable lease recovery still require actual evidence. Windows actual executable/PID membership, all-path descendant denial, mapped/shared/native-thread behavior and pinned-runtime provenance remain unproven. No real deployment assertion was created.

Next owner is PM01 for this blocked checkpoint, with Backend03 retaining implementation ownership. Required resumption: authorized Docker access resolution without workaround; rebuild exact source; reviewed native Linux diagnostic/pressure/realrunner captures; separately investigate Windows process identity/root cause before any reviewed materially changed probe; then fresh manifest and PM-controlled affected Web/independent review. This submission does not request04/08 activation or promote any AC-P3 status.
