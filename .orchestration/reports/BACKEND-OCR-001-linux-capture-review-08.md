# Linux capture08 independent saved-evidence review

Disposition: HOLD for L1 enforcement qualification; actual test FAIL at the fixed headroom precondition, before incremental pressure. Image-internal source verification and owned cleanup are supported. Preserve the harness's recorded UNPROVED_OBSERVER_EXIT status, but do not interpret that broad status as observer crash/death or OOM. Requested reused Mill Sol/high role; actual model unverified.

Authority: PHASE-3-linux-capture-02.md. Parent executed the separate candidate once; reviewer examined completed files only. No retry, tuning or correction is authorized by this report.

## Invocation, source and image

Outer command/result identify the approved interpreter with -E -B, optimize0, separate candidate e669d74fc1f683ad57cf3792860910f65198cbed3f6d0dee91232c36e36d082c, pins d92e20493eb42a3d4d2702b17c3d5559c17cad78e31b364387039e649146f2bc, image sha256:a1337c5556ab00f01dac45075f6bbf71ba9198c1b179a83d0210e5879a426d0a and fresh08 evidence path. Preflight records113 host raw/LF matches and absent output. Outer result records one attempt and capture-process exit2; parent's separate shell-tool exit1 is not that exit or the container exit. Both outer logs are zero bytes; container.log contains the actual pytest failure.

Independently compared all113 raw/LF pairs in source_before, source_after and inner-inputs.source_hashes against the exact pin snapshot: each set has113 members and every pair matches. Manifest source_unchanged=true; outer script/pins unchanged=true. Inner evidence identifies PID1 and precisely tests/backend/test_ocr_containment.py::test_native_pressure_and_owned_tree_cleanup[shortpeak]. Frozen inner code verifies image source bytes before execing pytest; saved inner record and subsequent JUnit support image-internal equality, unlike06. The copied capture/pin hashes match their authorized identities.

## Actual failure and causal boundary

JUnit is complete: exactly one expected testcase, one failure, zero errors/skips. Container log agrees. Failure is tests/backend/test_ocr_containment.py:328: headroom20561920 bytes (about19.61MiB), below required64MiB; allowed interval is64..160MiB. No cause for the extra memory consumption is established by these artifacts; no blame is assigned to imports/cache/model/runtime without further evidence.

Independently read the current test and verified its raw hash e72c2fb79a9bc3b0c0e08f155b5c78f16173d8e02ecc9f8349f2ecab3674af45 matches the pin. Ordering is decisive: child allocates/touches320MiB, emits ready and blocks awaiting G; observer validates ready/PID/nonce, process identity/cgroup membership and baseline anonymous residency, then asserts headroom at328. Only after that assertion do lines339-340 obtain t0 and send G. Child emits attempt and allocates224MiB only after receiving G. Thus the failing assertion prevented the increment attempt and timing gate in this invocation.

JUnit l1_evidence contains only ready from childPID7 with touched335544320 and configured increment234881024, observerPID1 and cap536870912. Increment in ready describes intent, not completed/attempted pressure. There is no attempt message, t0/t1/elapsed bound, causal outcome/events_delta, identity_valid completion or l1_verdict. The strict250ms enforcement oracle was not reached. Neither total testcase duration nor cleanup duration substitutes for its interval.

Freshness/resource assertions preceding328 passed along this test path: PID1-only initial membership, zero initial pressure/OOM counters, cgroup memory.max512MiB and memory.swap.max0; ready baseline checks then passed. Saved containment properties also show zero current max/oom/oom_kill counters. These facts do not prove over-limit enforcement because the pressure attempt never occurred.

The harness audit_result returns UNPROVED_OBSERVER_EXIT immediately for nonzero terminal exit, before reading JUnit; that explains the broad manifest label. Actual evidence is an ordinary completed pytest assertion failure with natural container exit1 and OOMKilled=false, not an observer OOM death, exit137, lost JUnit or measured containment enforcement failure.

## Lifecycle and cleanup

Ten recorded Docker commands: image inspect, exact-name pre-create list, create, created inspect, start, wait, terminal inspect, logs, pre-removal inspect, plain rm. Exactly one create/start; all CLI commands returned0, including wait whose stdout reports container exit1. No Docker stop/kill/forced removal/retry is recorded. Requested read-only root,128MiB tmpfs, network none and512MiB memory/swap flags match the activation. Whitelisted inspections corroborate image/memory/swap/network and ownership; read-only root is an argv fact rather than an inspected field in this capture.

Full container ID e09a6dde9cdf0ea91be9c3b2ea00abe646f96c77ba2aaec3deeca9f328f296a6, name /qa-l1-9174a321142f4951852a2fe026e02a32, owner BACKEND-OCR-001-L1-capture-03 and nonce9174a321142f4951852a2fe026e02a32 consistently match. Natural terminal and pre-removal records show running=false/status=exited/exit1/OOMfalse. terminal.json agrees; reviewed code publishes it before cleanup, and terminal inspection precedes removal in the command chronology.

JUnit owned_tree_stop_confirmed=True and owned_pid7 support child cleanup, with observed cleanup0.03088249099528184s. Container cleanup is separately supported by exact-ID plain rm exit0 and stdout equal to that full ID. Manifest cleanup_confirmed=true, launch_uncertain=false, stop_requested=false are consistent. No post-removal absence query was performed or required by this capture; removal acceptance is based on the successful exact-owned rm receipt, not inferred absence. This does not claim a new live daemon observation.

## Evidence hashes

Independently hashed files. Inner names are relative to BACKEND-OCR-001-native-apply-linux-evidence-03-08; outer names to BACKEND-OCR-001-linux-capture-outer-08, both under .orchestration/reports/.

| Artifact | SHA-256 |
| --- | --- |
| inner manifest.json | f0181c98ceb794d25d76bf6fb38692cffac9309ffb3f5f1bd183e4f13469e0dd |
| inner inner-inputs.json | 86ca0ce4e60b92a6582a6053e9aa428cff56283764e0136a3e87b889f265a755 |
| inner result.xml | 2dd0078d5f4dc71542f0835f13f9aea796115c77e20ed1a9e2744dbe10d084cb |
| inner terminal.json | 2441c977ae2de6a476ca1bc66f371e448d9ddfdda9a819f6c035417a9886f545 |
| inner container.log | 48e8de4be84e793ba17108fd172cd291e1a5fbf8a7b6bae0dce0af0da44a5166 |
| outer command.json | b2838a3727bb453f0f195103bf51843bb146278f027433b2ba4d50b4863bff0b |
| outer preflight.json | ea9c8bbdf5890606f69850ccdb8b10ae5947ac0eb75eb4ba91f31d24d88c927c |
| outer result.json | 1e1a80931fef3c5dee02254815f89045233f29cc6441d125ce1248bcd428e50f |

All four manifest artifact hashes match computed values. Both zero-byte outer logs hash e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.

## Preservation and remaining gates

Independently rehashed original capture d0a8e756cdd4cafc394d12a68e527632365aeaf43f6d9ca8cc063763db21d7fd,06 manifest cd519e114459fe5ee07967b9a536fd8ae4660a6514762f183df61e4008381eb5 and07 recovery result47522de102a140b7ca2d6263f87406d9d1499a7586e1c715f75a8ca37489d177: unchanged. The06 orchestration failure,07 recovery and08 headroom failure remain distinct events.

No PASS_SCOPED_L1 or native qualification follows. Windows3/historical cleanup2,04/08 gates, AC and production admission remain unchanged. Any new containment/contract assessment follows PM's read-only escalation requirement before changes; no auto rerun or headroom/resource tuning.

Only this new review was written. Read-only saved artifact inspection, source-order review, recorded113 hash comparisons and file hashing performed. No Docker, native/tests/import, source edits, candidate changes, DB or model calls by reviewer.
