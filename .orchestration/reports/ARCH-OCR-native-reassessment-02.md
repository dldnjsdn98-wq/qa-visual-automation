# ARCH-OCR native reassessment / Architect02

Date: 2026-09-26 KST. Scope: read-only reassessment under PHASE-3-native-reassessment-01. Requested model/effort: highest Astra/medium; actual unverified. Branch/commit: null/null.

Disposition: decision-ready proposal, not implementation or native-test authorization. Windows remains PAUSED at three same-cause native-accounting failures; prior cleanup count two remains separate. Linux shortpeak remains unproved. No counters reset, thresholds waived, production admission granted, AC accepted or 04/08 gate advanced.

## Decision for PM

1. Retain accepted revision2. Its 2GiB memory and 300s execution obligations do not name a 250ms native-test threshold, a Windows process-count API, or a launch flag.
2. Preserve the earlier runtime clarification as an implementation/evidence interpretation. Its requirement for short-peak coverage does not establish a universal 250ms termination SLA. The concrete existing sub250ms test still has not passed and must not be relabeled.
3. A minimal Windows implementation candidate is a no-console detached launch using the same python executable and pipes, with all existing hard-working-set, Job active-process-limit1, no-breakaway, suspended setup and owned cleanup rules preserved. This is an unproven candidate requiring static API/flag review and separate PM resumption before any edit or execution. Current code already uses CREATE_NO_WINDOW; adding it again is not a changed hypothesis.
4. The Linux test needs an observer-owned timing/causality protocol that survives target OOM, plus a declared fixed pressure construction. Keep the existing250ms criterion in the proposed replacement test. Do not rerun the unchanged allocation until it happens to be fast.
5. Neither identifying conhost nor the passing Linux slices closes Windows qualification or the skipped Linux shortpeak case. Implementation stays with03; independent review and PM resumption remain prerequisites.

## Evidence identity and inspection limits

The first requested handoff read returned file-not-found. PM subsequently supplied the file and corrected its earlier dispatch: the current report differs from the initially announced842dbdeb... hash after an owner documentation correction, and PM did not complete verification of all56 artifacts. The following current inputs were independently read/hash-checked by02:

| Input | SHA-256 |
| --- | --- |
| docs/architecture/phase-3-ocr-contract.md | 478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44 |
| .orchestration/reports/ARCH-OCR-runtime-clarification-02.md | 8eed0822dee5781b8fb23187f1a24a1d1ff1014a14f5bee59e2bc99f42795375 |
| .orchestration/handoffs/PHASE-3-native-reassessment-01.md | 4055fd040ffaa76a91effec60517e1ea70957a50299d68659bbf8b6fad2e3476 |
| .orchestration/reports/BACKEND-OCR-001-native-diagnostic-03.md | 86557e995cf5ec1ad8906253a9abb438cc3da2aae83bddd1d3729461e0981ef2 |
| .orchestration/handoffs/BACKEND-OCR-001-native-diagnostic-03.md | 4e8972bcb705debbc9e047e5c2133921f4b97cd226a66a1e752af648c2f794ed |
| .orchestration/reports/BACKEND-OCR-001-native-diagnostic-artifact-index-03-02.json | 0300b6c8c3fd8185603652fafac4811cbf0166dddd5d9c4379217308e2546261 |
| backend/app/workers/ocr_containment.py | ef7d7ffe6dbc0b8f620ae9416818614cf9aa9dc5ceb822fdee11d4feca76bec5 |
| tests/backend/test_ocr_containment.py | 382257cfb9747b2fe9d7aa87fedd5d50d5f853745c483be5b1764c3c958ade1b |
| .orchestration/reports/BACKEND-OCR-001-native-diagnostic-windows-03.py | e0650cbc135da408b589c1765bc7aaa67f2db1e2f62174c339f3549426210133 |

The index contains56 entries. That count is metadata, not an assertion that02 revalidated every artifact. The denied nested windows-identity-03-mokoyye2/identity.json was not accessed, retried or bypassed. Owner56/56 and PM103-source checks remain attributed to their respective reporters; this task did not repeat a full inventory audit.

Selected readable raw evidence was checked against the index: windows-owned-identity-facts-01.json (61d2f1955a3ee7531533cf92758ce0425a8ea1d017a1824ce127130203de1ad0), linux-shortpeak-pressure-02.json (e2e9394e86f253cf7f8da0f00c9480118cdbbecfa2966df2aa5fe4d60c87f3fc), linux-descendant-pressure-02.json (0112cfbcbf381a898f4f4cd6b234e9a3280f51c57c126979c710fc0d18234408), and linux-mapped-pressure-02.json (1466cb339d5fa01f675cb8bf918e18ed9668146cde7420d3fe90925e546a991f). All are under .orchestration/reports/BACKEND-OCR-001-native-diagnostic-evidence-03/. The shortpeak XML was read for its actual properties/skip reason. Facts copied into the readable Windows diagnostic remain useful evidence but do not replace access to the denied original marker.

## Contract, previous interpretation and test-specific conditions

| Layer | Actual obligation | What it does not establish |
| --- | --- | --- |
| Revision2 sections3/10.2 | One300s budget covering source/model/OCR/matching; parent supervision/commits, DB-free child,2GiB child RSS budget, terminate on observed exceedance, UNAVAILABLE when bound cannot be enforced/observed | No250ms poll/kill deadline, no named cgroup/Job implementation, no mandatory ActiveProcesses1 field |
| Revision2 sections3/10.2 recovery | Already validated short commit and fresh-primary ambiguity recovery; failed-stop quarantine | No strict server-COMMIT cutoff at local300s; no speculative compensating mutation |
| Earlier02 clarification | Sampled PID RSS alone cannot qualify the bound; continuous enforcement or equivalent; descendants must be bounded unless absent; short-peak evidence needed | An architectural interpretation is not a new numeric SLA or independent runtime acceptance |
| Earlier conditional Windows advice | Direct-process hard working-set cap is admissible only with proven no-descendant behavior and maintained effective limits | Applying flags successfully does not prove the condition; current two-process observation defeats it |
| Current Windows helper | ActiveProcessLimit1 and one-process accounting are the selected proof strategy | Not permission to ignore conhost, increase limit to2, enable breakaway or equate Job private commit with RSS |
| Current Linux test lines347-353 | Requires child duration below0.25s plus attributable OOM/denial, otherwise SKIP | No250ms value in accepted contract; no automatic PASS from a memory.max event or an unbounded timing estimate |

A kernel cap may prevent an allocation or reclaim pages without ever allowing RSS above2GiB. Absence of an actual over-budget RSS sample is therefore not itself a failure. Conversely, an exit or counter alone does not prove the full resource, classification and cleanup contract. Existing hard-cap interpretation remains; no sampling-only waiver is proposed. The stricter cgroup total-charge boundary is the existing accepted evidence strategy, not a claim that cgroup accounting and process RSS are universally identical (especially for shared pages charged elsewhere). Retain the qualified dedicated-runtime/layout restrictions and do not generalize the proof to arbitrary shared mappings or deployments.

## Windows: what is known and what remains unknown

The readable raw facts establish initial own-Job ActiveProcesses1 before resume and later class1 ActiveProcesses2/TotalProcesses2, with class3 assigned/listed2. Direct python PID111908 and conhost PID106636 have retained creation identities and revalidated membership; conhost's NT parent is111908. A single TerminateJobObject reached ActiveProcesses0 and confirmed cleanup. This identifies the second process for that run; it does not explain why the OS accounting included it despite ActiveProcessLimit1, nor prove effective memory protection of that second process.

The diagnostic identity_complete=false arose because STARTED parent/image events without values were included in a RETURNED-value classifier. Fixing that classifier would clarify evidence only. It cannot change ActiveProcesses2, erase the failed result or reset count3. Original raw records and helper remain frozen.

Relevant implementation locations:

- backend/app/workers/ocr_containment.py::_launch_windows, lines640-697: Job limit1/private cap; explicit pipe handles; CreateProcessW flags at677-682 already include CREATE_NO_WINDOW, CREATE_SUSPENDED, CREATE_UNICODE_ENVIRONMENT and EXTENDED_STARTUPINFO_PRESENT; Job assignment/hard WS query happen before ResumeThread.
- The same file::_WindowsContainedProcess._check_limits: rejects unexpected process count and validates direct-process hard working-set flags/maximum. This check must remain strict.
- The same file::_WindowsContainedProcess.stop and _launch_windows failure cleanup: retained ownership, bounded termination and handle cleanup. A launch-mode correction must preserve these paths.
- .orchestration/reports/BACKEND-OCR-001-native-diagnostic-windows-03.py: startup-only observation uses the existing helper; identity classifier at394-401; no pre-resume executable identity/parent-Job boolean/post-identity count series was collected. Snapshots are non-atomic.

### Proposed smallest conforming correction (not applied)

Candidate W1: replace the CREATE_NO_WINDOW console-start policy with DETACHED_PROCESS for the same absolute console python executable, keeping suspended creation, explicit inherited stdin/stdout/null-stderr handles, Unicode environment, startup attribute list, Job1/no-breakaway, hard WS limit and pre-resume checks. Do not combine contradictory console policies or switch to pythonw, a shell or another interpreter. The goal is to avoid creating/attaching a console from the outset, not merely hide a window. This is a hypothesis, not a demonstrated cure: the frozen diagnostic does not identify an AllocConsole/AttachConsole caller, and later native libraries could still request a console.

Prerequisites before authorizing even an execution-bearing diagnostic:

1. Independent read-only review of the exact proposed CreateProcessW flag combination and redirected-handle behavior against the applicable Windows API contract; confirm no incompatibility with STARTUPINFOEX, suspended launch or the installed console Python build. This task did not fetch new external API documentation and does not claim that check has already passed.
2. Audit the relevant child/bootstrap/native paths for console creation/attachment and subprocess use. Static absence alone is not qualification, but a known explicit console request must be resolved in the bounded proposal rather than hidden by count exceptions.
3. Specify a gated startup test in a new immutable evidence namespace: requested and actual executable identity, pre-resume handle identity/Job count, post-startup and post-import own-Job class1/class3 identities, effective hard WS flags, configured Job flags, attempted descendant denial, final cleanup. Bind PIDs to retained handles/creation time. Never kill a PID merely because its name is conhost.
4. Treat native diagnostic queries as potentially blocking. The observer may not hold locks needed for the sole owner to terminate its own Job. A blocked query must leave uncertain evidence and quarantine, not an unbounded cleanup wait.

After PM separately authorizes the exact diff,03 may implement only the reviewed launcher change and new targeted tests/capture. Independent static review must precede the first approved changed native execution. The first startup-only result must prove one owned live process throughout the sampled gates, intact effective limits and cleanup; no model run yet. Actual no-descendant and hard-cap qualification still requires the later approved attempted-descendant, mapped/native-thread, timeout and real-profile matrix. A repeated ActiveProcesses2 or any unproven stop returns immediately to PM with existing count history retained; no automatic second candidate or retry is authorized.

Candidate W2 is not a minimal fix: accepting conhost as a second process, exempting it by image name, or increasing ActiveProcessLimit to2 leaves the direct-process WS cap unable to prove total supervised RSS. A future genuine tree-wide resident-memory solution would need a separate concrete design and review. If it preserves all existing guarantees it may be an implementation change; if it weakens/redefines the resource subject or bound it requires exact contract revision and independent acceptance. It is not authorized here. Leaving Windows UNAVAILABLE is the correct outcome if W1 cannot be proven.

## Linux: evidence reassessment and replacement design

Current preserved facts:

- Descendant test: each requested payload322122547bytes below512MiB; readiness before parent allocation; combined pressure produced OOM/kill evidence and confirmed cleanup. This is aggregate cgroup evidence, not victim-specific RSS attribution.
- Mapped test: four threads completed with no reported errors; max297/oom0/kill0. This proves workload completion under reclaim pressure with cleanup, not an OOM kill or a standalone continuous RSS trace.
- Shortpeak: child facts object empty; exit-9; memory events present; before-allocation monotonic39616.688330965 to observed exit39617.100270405 gives0.41193943999678595s. This is an upper bound including allocation/zero-touch, marker publication, scheduling and observer latency. It neither proves the pressure lasted more than250ms nor proves it lasted less. JUnit SKIP is correct because the test requires a child completion duration that cannot be emitted after OOM.
- Real Linux runner/model passed with UNVERIFIED/NO_EXPECTATIONS and test-only admission. Parent-OOM recovery passed in a controlled job-service harness with real60s lease. These separate results remain useful; neither is a scored Web result or shortpeak proof, and neither should be rerun just to replace the failed/skipped classification.

Current test limitations in tests/backend/test_ocr_containment.py::_PRESSURE_CHILD and test_native_pressure_and_owned_tree_cleanup:

1. One bytearray(limit+8MiB) faults/zeroes over512MiB and may enter reclaim/OOM before it can write a completion record.
2. The start marker is emitted before allocation, and the only successful shortpeak branch requires pressure_elapsed_seconds in a child record. A killed child is always skipped even if a separate observer could prove a short interval.
3. The parent calls memory_exceeded/poll and sleeps10ms. The start-to-observed-exit upper bound is useful but the current0.4119s cannot satisfy250ms. Reducing the comparison to0.5s would change the criterion and is not proposed.

### Proposed L1: survive the target's death and keep the250ms criterion

Design before implementation/execution:

1. Use one fresh dedicated disposable cgroup per pressure case, frozen image/source, same declared total cap and no extra swap. Retain baseline events before pressure and before the gate. No counter resets, drop-caches, host cgroup writes or previous-case reuse.
2. Separate setup/readiness from the measured pressure action. Establish a fixed, predeclared touched baseline below the limit with enough observed headroom for the supervisor; reject the setup if pressure events already invalidate causal attribution. Then issue one predefined incremental allocation/touch request large enough to exceed the remaining headroom. Exact byte amounts and admissible baseline range must be fixed in the reviewed plan, not tuned across failures until passing. Do not assume virtual mmap reservation equals touched resident allocation.
3. Keep timing evidence in a surviving observer. Record monotonic t0 before releasing the pressure gate and t1 after a direct child completion/explicit allocation-denial acknowledgement OR handle-bound exit notification. Include process/cgroup identity, event deltas and independent exit/kill evidence. Clocks must be demonstrated comparable; use one observer clock around both endpoints where possible. Marker I/O and observer delay then make the interval conservatively larger, never subtract guessed overhead.
4. If the pressure target dies, a t1-t0 upper bound below0.25s plus pressure-correlated OOM/kill/explicit denial is a valid short-attempt witness; report prevented request/kill, not a completed over-limit RSS allocation. An exit137/-9 alone or memory.max counter alone is insufficient attribution.
5. If the target survives, record completed touch/free interval or explicit denial and corresponding cgroup evidence. A legal below-cap burst without evidence of an attempted violation is useful calibration only, not the enforcement test.
6. If the supervising parent can be an OOM victim, retain its evidence through the existing outside-container capture/owned-container observation route; distinguish container death from direct child death. Do not fabricate a child duration. Start with the existing reduced-limit isolated fixture, not a production load.
7. Below250ms with causal evidence can pass the new test; missing duration/ambiguous cause/interval>=250ms stays unproved. Retain old skipped evidence. No blind unchanged retry; review a new cause-specific plan if the first authorized redesigned case cannot discriminate.
8. Preserve mandatory cleanup even on skip/fail: identity-bound owned process/container teardown, receiver/observer disposition, no result writes, and all launch/partial-IPC paths. Rebuild the exact-source image after an approved test change, do not reuse image b with changed tests.

Alternative L2, if L1 remains inconclusive: propose a separate reviewer-approved argument that memory protection is independent of polling. With the qualified kernel limit continuously installed, gate a pressure request between two explicitly controlled monitor observations and later demonstrate persistent limit/denial evidence, intact cap and no publication. A finite scheduling interval cannot by itself prove a universal kernel bound; source/API semantics plus native evidence must support the argument. L2 addresses sampling independence, not a sub250ms latency claim. It is not a waiver or an automatic substitute: PM must approve an evidence-plan change and independent review must accept its coverage before it can replace any required test. The old250ms SKIP remains SKIP. No such substitution is made by this report.

## Exact prospective files, risks and review gates

| Cause / prospective files (03 owns; no edits now) | Principal risk | Prerequisite and next independent review |
| --- | --- | --- |
| Windows launcher in backend/app/workers/ocr_containment.py::_launch_windows | Detached startup may alter runtime/stdio behavior or fail to prevent later console creation | API/flag/handle review; exact small diff; PM correction and execution resumption; startup-only identity/limit/cleanup evidence before pressure/model qualification |
| Windows new capture and tests/backend/test_ocr_containment.py | False identity PASS, unbounded observer, PID reuse, cleanup regression | New capture namespace; RETURNED-only classifier; retained handle identity; separate stop owner; static review before native use |
| Linux pressure child and oracle in tests/backend/test_ocr_containment.py | OOM loses timing, prepressure contaminates cause, scheduling gets mistaken for peak length | Fixed gate/amounts and observer-owned timestamps; exact-image rebuild after approval; independent causal/oracle review; one authorized redesigned test |
| Existing own capture/image manifests | Evidence from a different source/image could be attached to a passing claim | Record before/after source and image identity; preserve all prior captures; no whole-suite claims from focused tests |
| worker profiles / deployment admission | Premature AVAILABLE from partial native evidence | No change in this scope; leave gating to PM after qualified evidence and independent review |

Three distinct gates must remain visible: (a) PM approves a correction plan and file claim; (b) independent static review accepts the exact implementation/test diff and PM authorizes the affected native execution; (c) evidence review establishes qualification before production admission/04/08 progression. This report achieves none of those future gates by itself.

## Actual actions and results

- Read-only PowerShell Get-Content, rg and targeted Node fs/crypto JSON inspection were run against the named local inputs. First handoff read exit1/file-not-found; reported to PM, then read successfully after PM stored it. This was not permission denial.
- Initial report hash disagreement was surfaced; PM corrected the dispatch to the86557... snapshot and clarified incomplete recursive verification. No unreadable marker read was attempted.
- Relevant current input hashes and four selected JSON/index matches passed. Raw Windows returned identities/accounting and Linux JUnit timing/skip fields were inspected. This is static evidence validation only.
- No subagent or new app task was created: existing03 Astra/Sol diagnostic and independent review findings already cover the bounded subproblems; parent02 integrated raw readable evidence without duplicating that work.
- No native API probe, test, container, build, model access or product/test/contract/profile/PM edit was run. All proposed W1/L1/L2 validations are NOT_RUN. Existing historical results remain attributed to03. All P3 AC stay NOT_RUN/gated.
- Only this report and paired handoff were authored. Requested highest Astra/medium is recorded separately from actual model unverified. No new429 occurred in this reassessment; the prior interrupted turn is not a test failure or a reset of native counts.

Next action: PM evaluates W1 and L1 plans separately. Until an explicit new scope/activation,03 may preserve and analyze evidence but Windows correction/native execution remains paused and no Linux redesigned native run is authorized by this document.
