# P3-RUNTIME-001 Sol/high test handoff

Date: 2026-09-25 (Asia/Seoul)

## Owned changes

- `tests/backend/test_ocr_runner.py`
- `tests/backend/test_ocr_source_read.py` (new)
- `tests/backend/test_ocr_runtime_integration.py`

No product, storage, API, profile, dependency, Docker, Worker, frontend, or PM state file was edited by this test role.

## Frozen independent coverage

`test_ocr_source_read.py` exercises the concrete `ocr_source.load_attempt` path for:

- exact returned source buffer identity and SHA-256 facts;
- durable size validation before storage open, including non-integer values, 0, negative, and 20 MiB + 1;
- accepted 1-byte and exact 20 MiB boundaries with an `expected_size + 1` guarded read;
- short/long returned payloads, declared-size mismatch, hash mismatch, and stream close;
- actual storage open/read `OSError` propagation;
- permanently blocked open/read inside a spawned child, with actual elapsed time, child exit, receiver exit, no parent heartbeat residue, and an unreachable post-load marker.

`test_ocr_runner.py` retains adapter-only supervisor coverage for deadline, measured RSS, oversized IPC, and receiver cleanup on both platforms. Partial/truncated length-prefix frames are POSIX-only because Windows `multiprocessing.Pipe` uses message-mode `PipeConnection`; those two tests carry an explicit Windows skip and must run in the captured Linux image.

`test_ocr_runtime_integration.py` adds JUnit properties for the actual isolated database name, profile digest, child PID/exit code, child/receiver cleanup, runner quarantine, supervisor/source identities, and SHA-256 of `ocr.py` and `ocr_source.py`. Its execution remains subject to the accepted architecture disposition and the opt-in real model environment.

## Diagnostic test execution (not final evidence)

Exact command:

```powershell
.\.pytest_cache\agent-clean-win\Scripts\python.exe -m pytest tests/backend/test_ocr_source_read.py tests/backend/test_ocr_runner.py -q --tb=short -p no:cacheprovider --basetemp .pytest_cache\p3-runtime-tests-sol-a
```

Result before the final helper corrections:

- 16 passed
- 5 failed
- 1 warning
- elapsed 13.81s

This diagnostic command did not specify shell redirection or `--junitxml`. Therefore it has no raw stdout/stderr file and no JUnit path. Its console result is retained in the originating task transcript and summarized here. The test sources were edited after the failed run, so their exact pre-correction SHA-256 values were not retained and cannot be reconstructed honestly from the current workspace.

Failure findings:

1. Very short adapter deadlines exhausted Windows spawn/cleanup time and produced `OutcomeUnknown("Attempt termination is unproven; runner quarantined")` instead of the expected timeout/resource error.
2. The first partial IPC helper incorrectly treated Windows message-mode `PipeConnection` as POSIX length-prefixed transport. Partial/truncated frame tests were restricted to POSIX; oversized messages remain portable through `send_bytes`.
3. A cleanup failure left a receiver thread observable by a later lifecycle assertion.

After this diagnostic run, the blocked-source test was changed to call the real `load_attempt` path, source short/long and open/read failures were added, and IPC helpers were made cross-platform. Per PM direction, no second test execution was performed by this role. The captured Windows/Linux evidence runner must execute the frozen files and retain stdout/stderr, exact argv, timestamps, source hashes, and JUnit.

The main evidence runner separately reported `windows-source-01`: 16 passed in 4.12s against the unchanged final source-test content. That evidence belongs to the main runner's captured directory; this role did not rerun or duplicate it.

## Architecture-dependent drafts and open gaps

The accepted contract assigns DB mutations to the parent, while the current frozen product draft moves heartbeat, stage, fail, and finalize into the single attempt child. The three `run_once` probes tied to that design are retained with explicit `pytest.mark.skip` reasons; their presence is not acceptance of the child-write design.

The following remain unverified until PM resolves DB ownership and a contract-conforming product API is frozen:

- claim origin and lost claim acknowledgement recovery;
- timeout quarantine followed by durable lease recovery while preserving the required retryable cause (`ENGINE_TIMEOUT`, not only `LEASE_EXPIRED`);
- stage/finalize commit and lost IPC where COMMIT may already have succeeded;
- stale fence recovery with no late finalize or parent mutation;
- retry state compatibility after source timeout;
- no false assumption that IPC loss implies zero result rows.

`git diff --check` passed for the three owned test files. No completed qualification suite was rerun.
