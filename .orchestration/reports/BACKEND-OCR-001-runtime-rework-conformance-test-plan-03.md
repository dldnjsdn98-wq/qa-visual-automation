# P3-RUNTIME-001 conformance test lane

Status: API coordination pending; no test execution in this lane.
Basis: PHASE-3-runtime-conformance-resume-01.md and ARCH-OCR-runtime-clarification-02.md, read in full.

## Ownership and execution

Exclusive tests: test_ocr_runner.py, test_ocr_source_read.py, test_ocr_runtime_integration.py, new test_ocr_runtime_db.py and test_ocr_containment.py, all under tests/backend.
Parent captures every execution. Do not repeat the two observed cleanup failures before product fix and review. Preserve prior failure artifacts and expectations. Oversized test helper currently uses MAX_RESULT_BYTES + 2; no change needed.

## Required matrix after API freeze

- DB-free child: observe serialized arguments and child environment/module state using harmless sentinel credentials; no DB URL, password, parent mutation service or session factory. Report only sentinel presence booleans, never environment values. Verify the actual spawn/import path, not just source text. Containment must precede workload execution.
- Source and deadline: actual loader blocked in open/read/close, bounded immutable metadata, size/hash/same buffer, shared claim-origin productive deadline across phases. Record productive elapsed time separately from containment tail. Confirm process/tree and receiver termination before one ENGINE_TIMEOUT fail under a live fence. Unproven stop must quarantine; proven normal cleanup must not be accepted as quarantine.
- Parent DB wait: a blocked operation must not block child termination. One outstanding operation only. No renew/stage/finalize/new claim after deadline. No compensating fail while operation outcome remains uncertain.
- Claim acknowledgement: unresolved claim creates no child or second identity. Confirmed recovered claim retains its identity and productive budget origin; delayed acknowledgement must not silently reset the budget.
- Finalize: successful already-issued fenced commit remains success after deadline. Lost acknowledgement recovers the same result identity. Proven rollback after deadline must not cause the service's internal second finalize. Unresolved commit quarantines without fail or another claim; do not assert zero results when COMMIT may have succeeded.
- Timeout bookkeeping: stopped workload + no outstanding mutation + current live fence permits one ENGINE_TIMEOUT fail, preserving RETRY_WAIT/cause. Stale fence cannot be revived. An uncertain timeout-fail commit cannot produce a second mutation.
- Native containment: use real process-local available facilities with a reduced test limit and real touched allocations, including a sub-poll short peak and combined descendant load. Record configured limit, backend identity, observed outcome/exit and complete owned-tree cleanup. Unsupported facilities must fail closed; report native enforcement NOT_RUN when unavailable rather than substitute mocked RSS evidence. No host security/cgroup delegation/dependency changes.
- Integration: retain actual isolated DB name, profile identity, source hashes, supervision/containment identity and measured cleanup as JUnit properties; no secret values. Real model run remains parent-controlled.

## Existing service seams inspected

VerificationJobService._transaction exposes BEFORE_COMMIT and AFTER_COMMIT fault hooks, invalidates uncertain connections, and invokes recovery. recover_claim, recover_finalize and fenced fail already define durable identity semantics. finalize currently retries up to twice after proven rollback; the deadline-aware guard for that retry is an explicit interface dependency, not assumed present.

No new test imports or product API assumptions are introduced by this plan. Prior draft child-write probes are not conformance acceptance.

## Windows conditional candidate, subsequent Architect02 adjudication

Require HARDWS_MAX_ENABLE through SetProcessWorkingSetSizeEx, effective page-rounded maximum at/below budget, Job ActiveProcessLimit=1, no breakaway, and suspended/gated attachment before any workload. Job private-commit limit is defense-in-depth only. Query effective working-set flags/maximum before startup and again before accepting a result; failed query or uncertain continuity leaves containment unavailable.

Native tests must include file-mapped/shared working-set pressure, native threads, a short peak, attempted descendant creation, effective flags/page rounding, and confirmed owned-resource cleanup. A denied allocation or containment event cannot be followed by accepted output. Completion notifications are best-effort and cannot alone prove absence of a breach. The qualified child/import path must be reviewed for limit-changing calls; a pre-result query alone does not prove no transient change. Actual pinned Windows OCR remains separate parent-controlled evidence.

Current implementation status: test_ocr_runtime_db.py now contains unexecuted existing-service PostgreSQL settlement tests plus mutation_guard boundary tests. Runtime/source/containment-dependent tests remain pending concrete files/protocol; no test execution by this lane.
