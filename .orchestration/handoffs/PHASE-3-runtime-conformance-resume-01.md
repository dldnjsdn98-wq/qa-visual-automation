# P3-RUNTIME-001 conformance resume / PM01

Architect clarification report8eed0822dee5781b8fb23187f1a24a1d1ff1014a14f5bee59e2bc99f42795375 and handoffeba017cc6d925bbaaf2477d358131e9a9c04a000e78462b3d72a8220c5c4cfee read/hash matched. Canonical rev2 remains478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44. PM adopts clarification as implementation guidance, not independent product acceptance. Prior partial97-source/27-artifact checkpoint preserved.

BACKEND-OCR-001 READY to resume. Highest difficulty Astra/medium requested for parent authority, DB uncertainty/deadline and containment design/integration; actual model unverified. Use existing subagents where possible: one implementation owner for runner/source/parent DB operations; a disjoint high-or-higher containment implementation lane; Sol/high for focused fault tests with exclusive test files; Terra/high for evidence inventory. Parent03 integrates and reviews interfaces before parallel edits; no two writers on shared runner. Windows/Linux native containment complexity may warrant Astra/medium. No new app task.

Child gets bounded immutable metadata/source specification and no DB credentials or mutation API. Parent owns claim/renew/stage/finalize/fail and recovery. One300-second productive budget; no useful work/renew/new stage/finalize/claim after expiry. Small bounded containment tail is measured separately, not extra compute allowance. Previously issued valid fenced COMMIT may settle later. Uncertain mutation forbids compensating fail; fresh-primary locked recovery remains authoritative. One timeout fail only after confirmed stop, no outstanding/uncertain mutation and live fence. Parent-controlled DB wait must not block child supervision or launch additional mutations while quarantined.

Memory must be continuously bounded at/below2GiB with descendant coverage unless all-path no-descendant behavior is demonstrated. Sampled RSS alone does not qualify AVAILABLE. Implement only process-local owned-resource containment or existing permitted isolated runtime facilities. Do not change host-wide security, cgroup delegation, account privileges, shared services or dependencies. Unavailable containment must fail closed/unavailable; record environment limitations without bypass. Any extra runtime/Docker/dependency/profile files require a concrete PM claim before editing. Existing recipes may be rebuilt; isolated synthetic runtime commands within current authorization remain allowed.

Exclusive additional claims (optional, necessity justified in report):
- backend/app/workers/ocr.py
- backend/app/workers/ocr_source.py
- backend/app/workers/ocr_runtime.py (optional parent DB operation/containment helper)
- backend/app/workers/ocr_containment.py (optional Windows/Linux owned-process containment helper)
- backend/app/services/verification_jobs.py (only existing fence/uncertainty/server-timeout integration if necessary)
- tests/backend/test_ocr_runner.py
- tests/backend/test_ocr_source_read.py
- tests/backend/test_ocr_runtime_integration.py
- tests/backend/test_ocr_containment.py (new focused platform tests)
- tests/backend/test_ocr_runtime_db.py (new focused parent authority/uncertainty tests)
- own reports/handoff/manifests

Required new evidence: DB-free child; productive deadline/blocked acquisition/owned cleanup; late ACK of valid prior COMMIT; uncertainty/no compensating mutation; timeout fail preconditions; no new claim while quarantined; real short-peak/descendant memory enforcement and unavailable path; Windows/Linux focused tests. Preserve first failures, skipped transport/integration cases and exact run-specific hashes. Cleanup same-cause executions2; do not run unchanged failing suite. Fix and review before next attempt; third same-cause failure pauses affected lane and triggers reassessment. Diagnostic image and earlier tests are not final production qualification.

Completion: corrected parent-integrated source manifest, current Worker42 match, platform evidence/raw logs/JUnit and final image/realrunner evidence. Only then PM activates affected04 Web rerun, followed by08 independent review. AllP3AC remain NOT_RUN. No Phase4/commit/push/deploy/shared DB reset or user-data deletion.


## Architect02 Windows focused follow-up

Conditional admissibility only: SetProcessWorkingSetSizeEx hard WS maximum <=2GiB with child-only Job ActiveProcessLimit1 and no breakaway. Job private-commit cap alone is not RSS containment. Before model/native/source work, parent must establish/query containment through a safe startup gate. Prove effective hard flags/max (conservative page rounding), descendant denial across all paths, and no child relaxation of limits; requery before accepting output. Actual touched sustained/shortpeak/file-mapped/shared/native-thread/descendant tests and pinned Windows runtime at2GiB are required. Record API return/GetLastError, OS build, effective limits, process counts, observed peak, exit/cause and cleanup. Any inability to establish or demonstrate enforcement leaves the platform UNAVAILABLE. Do not infer resource failure just from paging/trimming; report observed semantics and contract error handling. Linux parent+DB+tree cgroup cap is an admissible stricter scope, with parent-death/lease-recovery implications tested. No host setting or permission changes authorized.02 changed no files or tests;PM received this as focused interpretation and delivered to03; independent acceptance unchanged.


## Profile availability integration claim

03 additionally owns verification_runs.py runtime-eligibility integration and test_ocr_api.py focused regression. New semantics await02 focused interpretation: do not infer runner containment from a separate API process/container, preserve identical-ID replay/history/immutable profile identities, and avoid new public/schema/fleet machinery. File ownership approval is not approval of an invented readiness protocol. Other runner/containment implementation remains active. Requested high Sol/high for bounded integration tests, Astra parent retains uncertain boundary integration.


## Deployment admission scope activated

02 focused interpretation received: AVAILABLE describes a qualified worker deployment execution class for exact profile ID/digest+target/release, not API-local capability or worker heartbeat. PM now explicitly authorizes the minimal shared deployment readiness input, superseding the earlier no-new-config limit only for this purpose.03 owns ocr_admission.py, test_ocr_admission.py and the relevant backend/README.md section plus already claimed API service/tests/runner. One immutable external release assertion supplied identically to API/runner; bounded schema/exact identity validation and missing/malformed/mismatch fail closed. No fleet service/schema/public route/signing infrastructure or mutable profile edits. Real assertions only after qualification, never elevate synthetic injection or historical sampled-RSS smoke into runtime admission.03 documents concrete interface and source provenance; report any additional file claim first.

List and new create share predicate, runner revalidates admission and actual runtime after claim. A readiness race yields durable unavailable failure, not silent skipping. Existing identity/fingerprint arbitration precedes current registry/readiness: replay200/conflict409 even after removal or readiness loss. Fresh known-unready503 RetryAfter5 without run/job/snapshot/reservation; unknown422; exact qualified admission permits202. Preserve historical profiles/results and exact digests. Tests cover digest/target mismatch, false->true retry with same unreserved newID, true->false replay/conflict, unknown profile, false admission at claim and live containment failure. Independent final review and affected Web gates remain unchanged.

PM clarification after crossed delivery: the shared pure admission provider may live in already-owned ocr_runtime.py instead of optional ocr_admission.py; do not duplicate providers. Import from API must not start worker/native/model work. Isolated qualification of an unadmitted target is allowed to produce evidence; do not fabricate production admission to bootstrap qualification. The explicit shared immutable input authorization above is active.

PM admission schema review: Descartes proposed strict JSON v1 with exact schema_version/worker_target/release_id/profiles fields, bounded65536 bytes and256 exact profile ID/digest entries, duplicate/unknown keys rejected, four explicit path/hash/target/release inputs and no readiness boolean. Approved within existing scope subject to03 parent interface integration. Apply bounded max+1 read and hash/parse the same bytes; exact types and existing profile-token rules; ordinary invalid configuration fails closed. The content pin protects integrity, not proof of qualification. Only actual qualified release assertions may enable production; tests inject synthetic readiness explicitly. API replay precedence remains mandatory.
