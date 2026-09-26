# Linux single08 headroom assessment

2026-09-26 KST. Galileo, requested highest Astra/medium; actual model identity unverified. Read-only ambiguity assessment under PHASE-3-linux-capture-02; no execution or corrective authority. Mill separately audits the complete record; this is not a duplicate artifact-manifest certification.

**Disposition: the fixed test setup failed its headroom precondition before the timed pressure attempt. Shortpeak containment remains unproved; this record establishes neither a containment breach nor contract nonconformance.** Preserve JUnit FAIL, not PASS or SKIP. No rerun, tuning, source change or contract waiver follows.

## Evidence and execution boundary

Read `manifest.json`, `result.xml`, `inner-inputs.json` and `container.log` in `.orchestration/reports/BACKEND-OCR-001-native-apply-linux-evidence-03-08/`, plus the selected test and relevant import declarations. The manifest records image `sha256:a1337c5556ab00f01dac45075f6bbf71ba9198c1b179a83d0210e5879a426d0a`, fixed536870912-byte cap, equal Docker memory-swap setting, network none, PID1 observer and the single shortpeak node. Inner inputs identify candidate `e669d74f…`, pins `d92e2049…` and selected test raw hash `e72c2fb7…`/LF `52349c96…`; the selected local test hash matches. Full113-source/artifact validation is left to the record audit.

- JUnit: **1 test, 1 failure, 0 errors, 0 skips**. Log and traceback locate `tests/backend/test_ocr_containment.py:328`: required64..160MiB headroom, observed20561920 bytes (**19.609375MiB**).
- Recorded child PID7 sent one nonce-matched `ready` message: baseline335544320 bytes (320MiB), planned increment234881024 bytes (224MiB). Reaching line328 means preceding assertions accepted the direct child's identity/process group, shared cgroup membership and `RssAnon >=320MiB` (lines315-325). This establishes baseline readiness and an anonymous-resident lower bound, not an exact child RSS measurement retained in JUnit.
- Line326 reads cgroup `memory.current`; subtracting captured headroom from the fixed cap implies **516308992 bytes (492.390625MiB)** at that read. This value is arithmetic reconstruction from the assertion, not a separately saved memory-current property.
- The failure precedes `before_gate` event validation (329-330), persisted pre-gate identity/current/headroom facts (334-337), observer t0 (339), G write (340), and the child's incremental allocation after G (child code187-191). No attempt/denied/completed message, t0/t1, elapsed witness or `l1_verdict` exists. `_l1_oracle` at391 was not reached because the assertion propagated after cleanup. The0.377s JUnit duration/0.38s log duration is whole-test time, **not** the250ms pressure witness.
- JUnit records `owned_tree_stop_confirmed=True`, cleanup0.03088249099528184s, direct PID7; helper scope states direct-child-reaped/no residual runnable cgroup work. Manifest records natural container exit1, running false, OOMKilled false, then successful owned-container removal and `cleanup_confirmed=true`. These support cleanup of this failed setup, not pressure enforcement or universal descendant reaping.

## Attribution and interpretation limits

`memory.current` is an aggregate cgroup charge, not child-private RSS. It includes the observer, child/runtime allocations and charged file cache/kernel/other overhead. The selected test imports `child_environment` through the OCR runner; conftest imports FastAPI/SQLAlchemy/Alembic/application modules. Those are plausible contributors to observer/runtime charge, not measured explanations. Import declarations alone do not prove DB activity or quantify memory.

The implied total minus the320MiB requested baseline is not a valid observer-RSS estimate: exact child anonymous charge, other child memory, file/cache charge, kernel accounting and observer memory are not separately recorded at the sample. No saved `memory.stat` decomposition, paired observer RSS or retained exact RssAnon value identifies which component exhausted the setup allowance. The pre-gate `facts.update` never ran. The record therefore cannot establish a leak, blame a package/import, or show that the child alone exceeded its allowed memory.

Initial and helper before/after-cleanup event snapshots record max/oom/oom_kill/oom_group_kill all zero. Docker OOMKilled is false. Together with the explicit assertion/JUnit, there is no observed OOM/kill/denial attribution for this run; these fields are not proof of every possible kernel event or a continuous RSS trace.

Manifest `status=UNPROVED_OBSERVER_EXIT` and generic `observer_death` text are coarse capture labels. They must not be restated as an observed crash/OOM loss: the available JUnit/log show ordinary pytest assertion failure with cleanup, followed by container exit1. The appropriate precise summary is **“headroom precondition FAIL; incremental pressure not attempted; timing/cause unproved; owned cleanup confirmed.”** Preserve the raw generic label alongside this interpretation; do not rewrite evidence.

This single run shows the approved fixed setup's headroom assumption was not satisfied in this captured environment. It neither invalidates the existing capped-cgroup strategy nor qualifies the required shortpeak/2GiB/300s runtime contract. The250ms criterion was not exercised. Existing Windows3/historicalcleanup2 and all admission/04/08/AC gates remain unchanged.

Only this new assessment was written. No native/API probe, Docker, pytest, package/application import execution, model/DB access, product/test edit or full hash-packaging audit was performed. No fixes or repeat invocation proposed.
