# Backend03 corrected exact Linux L1 capture 08

Task BACKEND-OCR-001 / P3-RUNTIME-001; owner03. Status: **HEADROOM_PRECONDITION_FAILED; L1 enforcement UNPROVED; cleanup confirmed**. Raw harness disposition UNPROVED_OBSERVER_EXIT is preserved. Authority PHASE-3-linux-capture-02.md explicitly activated one new run after reviewed two-expression correction; no automatic retry followed. Branch/commit null.

## Actual execution and source identity

Parent invoked the separate candidate directly once, through ordinary require_escalated approval, using approved interpreter -E -B/optimization0. Frozen original was not patched. Candidate SHAe669d74fc1f683ad57cf3792860910f65198cbed3f6d0dee91232c36e36d082c; image sha256:a1337c5556ab00f01dac45075f6bbf71ba9198c1b179a83d0210e5879a426d0a; pins d92e20493eb42a3d4d2702b17c3d5559c17cad78e31b364387039e649146f2bc; fresh evidence native-apply-linux-evidence-03-08. Preflight confirmed all113 host raw/LF pairs, exact candidate/original/pins and absent output. Outer wrapper AST PASS SHA3290c447649ab313854c2a1779d6579d5171fb0b936b7cb096e91c6d634fb502.

Image-internal raw AND LF verification **PASS113/113 before pytest**, now supported by inner-inputs.json with observerPID1, exact node and candidate/pin identities. Parent compared all113 pairs across inner inputs, frozen pins and host before/after: exact equality. Source/candidate/pins stayed unchanged. Original d0a8e756cdd4cafc394d12a68e527632365aeaf43f6d9ca8cc063763db21d7fd remains unchanged;06 failure and07 recovery stay immutable.

Actual captured process exit2, elapsed3.860s; encompassing PowerShell tool exit1 (chunkec8cb6). These are not the container exit. Outer stdout/stderr are zero bytes because the harness keeps command diagnostics in its manifest. Container naturally exited1 and OOMKilled=false. Docker CLI wait itself exited0 with stdout1. No process exit137 or observed OOM death is recorded.

## Actual selected test and failure boundary

Exactly one selected test `tests/backend/test_ocr_containment.py::test_native_pressure_and_owned_tree_cleanup[shortpeak]` executed: **1 FAILED,0 errors,0 skipped;1 dependency deprecation warning;0.38s**. Actual JUnit suite time0.377s, testcase0.287s; the longer outer time includes Docker lifecycle. Warning concerns anyio.abc.BlockingPortal deprecation via Starlette; no dependency edit attempted.

Failure at test line328: fixed headroom precondition requires64..160MiB, but the assertion reports20561920 bytes =19.609375MiB. The cap is536870912 bytes (512MiB). ChildPID7 sent one ready message with touched335544320 bytes (320MiB), intended increment234881024 bytes (224MiB) and nonce. No increment attempt message exists. Static ordering establishes the headroom assertion occurs before t0 and writing G to grant the additional allocation; the224MiB attempt was NOT_REACHED. No t0/t1/elapsed enforcement witness or l1_verdict was recorded.

The failure output supplies actual headroom; memory.current was not separately included in structured l1_evidence because facts.update follows the failed assertion. Subtracting reported headroom from fixed cap yields516308992 bytes; this is explicitly a derived value, not a separately captured measurement. No attribution to observer imports, child overhead, file cache or a particular component is justified from that number alone. No threshold/cap/baseline tuning was performed.

The raw capture classifier checks natural nonzero exit before JUnit and therefore labels UNPROVED_OBSERVER_EXIT. That generic label does not establish abrupt observer death, OOM, missing JUnit or containment failure: completed JUnit and log show the specific setup assertion. The test failure is real, but the timed over-limit enforcement question remains unproved. Saved events before setup and in cleanup show no oom/oom_kill increments; no killed/denied-attempt PASS can be inferred.

## Ownership and cleanup

Exactly one create, one start, one wait and one ordinary rm; no stop or forced stop. Container ID e09a6dde9cdf0ea91be9c3b2ea00abe646f96c77ba2aaec3deeca9f328f296a6; name qa-l1-9174a321142f4951852a2fe026e02a32; owner BACKEND-OCR-001-L1-capture-03; nonce9174a321142f4951852a2fe026e02a32. Corrected formatted inspections succeeded and matched exact ID/name/labels/image, memory=swap536870912/networknone before start and before cleanup. Requested read-only root and128MiB tmpfs remain in create argv.

JUnit confirms owned child cleanup=True in0.03088249099528184s. Natural terminal exit1/OOMfalse/nonrunning was recorded in terminal.json before removal. Final exact ownership inspection matched; ordinary docker rm fullID returned0/fullID. Manifest cleanup_confirmed=true, launch_uncertain=false, stop_requested=false. This is reviewed lifecycle cleanup evidence; no additional post-removal absence probe was performed or claimed. No residual is reported by the completed owned lifecycle.

## Review and scope

Reused Mill requested Sol/high independent actual-result review and Boole requested Terra/high artifact packaging. New headroom/containment interpretation was referred to reused Galileo requested Astra/medium for read-only assessment before any change, as activation requires. Parent retained existing model for execution coordination; actual model identities unverified. Agents did not duplicate native execution.

All08 raw output is preserved in linux-capture-outer-08 and native-apply-linux-evidence-03-08. Parent own audit linux-capture-parent-audit-08.json distinguishes test failure, broad raw classifier, source verification and proven cleanup. Final independent review/headroom assessment/artifact index accompany this report and final own manifest.

No repeat capture, rebuild, resource/threshold tuning, source/predicate/pin change, DB/model execution, full279/pure12 rerun, Windows hook/probe,commit/push/deploy/security change. Windows same-cause3/historical cleanup2,04/08/production admission/allP3AC stay held. This invocation's observed failure cannot establish native L1 qualification; PM decides any next explicit scope after this frozen packet.

Final Mill independent review HOLD for enforcement, SHA8c1571bd9359dc550df3fa3b5d11fbd9b9b6a9130415ab960b705a157bd21fba; confirms inner113 and cleanup without treating generic status as death. Galileo fact/attribution-only assessment SHA8893cff8bd6473bf3d5f75119ad265afb5088cec7270938cee402067a0a720b2 concludes no containment-breach/contract conclusion from this precondition failure and no overhead attribution. PM separately assigned architectural fixture/observer/equivalence reassessment to02; this parent's assessment supplies facts only and does not duplicate design work. Supporting code/evidence ordering was sent to02.

Boole12-file index SHAddb71bde473b427aff882c45fdcbd8dec1e5d7c4f2851db0aa9c9635be484a22; audit23418c83e0ee0331fa369e90026612d72fe712a6a2648418cfa14132610bbce2. All expected08 files present; no fabricated result. Final own linux-capture-manifest-08.json includes actual evidence, wrapper, audits/reviews and report/handoff, excludes itself. PM also directly confirmed JUnit/code order/inner113/four artifact hashes. Authorized08 run and evidence completion are finished; PM/Architect02 own next explicit decision. No further native work here.
