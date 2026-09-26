# Independent Linux L1 candidate static review / Backend03

Date: 2026-09-26 KST. Disposition: PASS for frozen preparation proposal only.
No concrete correctness blocker found in the reviewed candidate. This is not
source-application permission, native execution readiness, a test result, or
qualification/admission. Requested assignment: reused independent Sol/high;
actual model identity/effort is not independently verified by this report.

## Frozen author identity

Author Fermat confirmed final freeze directly from task
01a0d854-c4be-7931-b5bb-9a02c96b8a99. Reviewer subsequently read the completed
report and rehashed both author artifacts and their relevant unchanged sources.

| Input | SHA-256 |
| --- | --- |
| BACKEND-OCR-001-native-candidate-linux-03.patch | d15ebab5fc1a5c3b4bb6fdd8c5d06907216decbff087f9f7722b34f9669a6639 |
| BACKEND-OCR-001-native-candidate-linux-03.md | ea706e2f02ede9c9b6aed446127d85bdbb665cc73380e02a7738cad61ecf0f9 |
| tests/backend/test_ocr_containment.py | 382257cfb9747b2fe9d7aa87fedd5d50d5f853745c483be5b1764c3c958ade1b |
| backend/app/workers/ocr_containment.py | ef7d7ffe6dbc0b8f620ae9416818614cf9aa9dc5ceb822fdee11d4feca76bec5 |

Scope follows PHASE-3-native-correction-plan-01.md and Architect02's
ARCH-OCR-native-reassessment-02.md L1 interpretation. Only this review file is
written by this reviewer; author files, source and tests are not modified.

## Reviewed reasoning

- Fixed construction: touched 320MiB anonymous baseline plus one 224MiB request
  totals 544MiB against a 512MiB cap with zero extra swap. No guessed overhead
  is needed to establish requested pressure. RssAnon >=320MiB, measured
  headroom 64..160MiB inclusive, unchanged pre-gate event map and exact
  participants are prerequisites, not adaptive tuning or promised feasibility.
- Fresh scope: observer PID1 is the sole prelaunch member; before the gate the
  only members are observer and retained child. Child start ticks, PPID, process
  group, nonce/PID records and cgroup membership are checked. Existing poll()
  uses WNOWAIT, retaining the direct child identity until owned cleanup. No
  external reaper or newly guessed PID is introduced by the candidate.
- Conservative endpoints: the surviving observer records t0 before gate write
  and t1 after terminal acknowledgement or owned exit observation. The child
  acknowledges its fixed request before allocation. Draining queued attempt
  bytes after exit does not move t1 earlier. Protocol/scheduling overhead stays
  included; strict elapsed <250000000ns is preserved, including equality rejection.
- Cause: killed-attempt PASS additionally needs owned exit -9 and a positive
  post-gate oom_kill delta. Denied-attempt PASS needs the target's MemoryError
  record and positive oom delta. Max-only, completion-only, absent attempt,
  missing/negative/long timing and ambiguous cause cannot pass. These are
  controlled-cgroup short-attempt witnesses, not proof of completed over-limit
  resident allocation or universal victim attribution.
- Cleanup: nonblocking pipes and bounded select loops add no receiver thread.
  Nested finally invokes existing _finish even if evidence recording raises.
  _finish asserts stop success and child exit before closing. Its failure
  prevents reaching the oracle; therefore the literal cleaned=True passed
  afterward is backed by that control flow, not an ignored stop result.
- Conservative failure paths: invalid framing/order/identity, truncated protocol,
  inadmissible setup, counter reset and unexpected membership fail. A terminal
  record/exit race that cannot satisfy the parser may fail conservatively; it
  does not create a shorter fabricated endpoint or a false PASS. Twelve proposed
  pure oracle cases cover the stated basic decision boundaries; none was run.

## Remaining downstream gates and evidence limits

The report explicitly leaves outside-container capture unimplemented. A dying
pytest PID1 cannot publish a valid observer t1 or complete JUnit; no child timing
or PASS may be inferred. Before native execution, parent must separately review
the owned named-container ID/nonce capture route, retained terminal inspect,
timeout classification, and confirmed exact-container cleanup. No --rm before
evidence capture, no manufactured natural-OOM success after forced host stop.
This necessary execution prerequisite is not a blocker to this preparation-only
proposal and is not represented as completed here.

Parent owns patch applicability, prospective-source AST/hash checks, subsequent
PM source-application approval and exact-source image rebuild. The old image b
cannot validate changed tests. Actual runtime survival, headroom feasibility,
timing and enforcement remain NOT_RUN. Prior skipped/failed evidence and all
Windows counters/gates remain intact; no L2 substitution or 279-suite rerun.

## Actual verification

Read-only shell reads, targeted rg and Get-FileHash; direct author freeze
confirmation. Initial report was absent while authoring and was read after the
freeze message. A discovery search reported access-denied unrelated historical
directories; no denied content was read or bypassed. No Python/AST/pytest,
git-apply, probe, build/container, DB, model or native execution occurred.
No runtime PASS is claimed.
