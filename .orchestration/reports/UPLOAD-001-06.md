# UPLOAD-001 owner report

Date: 2026-09-25 KST. Contract: `P2-UPLOAD-v1`, document revision 2, SHA-256 `e47d3dca18fef169600bf6bebe78a31432105e5a1ae5b80a9934e1bf4ee8f843`. Requested status: `READY_FOR_REVIEW`.

Implemented the durable screenshot producer and uploader in `agent/screenshot_upload/` with tests in `tests/upload/`. It uses immutable `captures/binding.json`, explicit init, narrow canonical origins, an OS-owned process lock, marker-last producer publication, strict manifest/image validation, atomic `state.json` plus `initialized.json`, bounded no-redirect HTTP, RFC 8785 ACK matching, bounded retry epochs, retained originals, crash recovery, and explicit unchanged-intent requeue. It has no SQLite authority, implicit init, rebind/migration/force option, ID rotation, original deletion, or common `agent/__main__.py` change.

## Key behavior

- `python -m agent.screenshot_upload init|run|requeue` is packaged. Init publishes one canonical authority without overwrite and refuses corrupt, nonpristine, or differently bound roots.
- Producers require a valid binding and validate all immutable intent and metadata bounds before creating an item. Original, manifest, and ready marker are flushed and published in marker-last order.
- Queue state has a closed strict schema. State precedes `initialized.json`; valid state repairs a missing marker without resetting counters. Corrupt/missing owned state is never reconstructed.
- Binding checks precede startup discovery and every state/temp/marker/diagnostic write, attempt, HTTP request, retry/failure, ACK, move, recovery, and requeue. URLs use only the immutable startup origin plus fixed path and validated UUIDs.
- IN_FLIGHT and fallback deadline are durable before HTTP. Retry uses equal jitter and valid Retry-After minimums, accepts only specified retry classes, and ends after eight attempts per epoch while retaining evidence.
- Success requires 201/false or 200/true plus complete Screenshot identity/context/facts, JCS-equivalent metadata, Location/content URL, UTC time, and request ID. ACKED precedes the no-overwrite move; UPLOADED follows it.
- The unified hash lock keeps only the reviewed `rfc8785==0.1.4` wheel hash `520d690b448ecf0703691c76e1a34a24ddcd4fc5bc41d589cb7c58ec651bcd48`. Linux-only `uvloop==0.22.1` is pinned and hashed behind platform markers.

## Failure coverage

- F01-F03/F16-F20/F23: partial producer files, process lock, durable attempts/deadlines, retry/exhaustion, strict malformed ACK, state/marker corruption, ACKED/move/UPLOADED recovery, failed/requeue ordering, original retention, duplicate-root collision, strict JSON numbers/Unicode/duplicate keys, and RFC 8785 vectors.
- F25: canonical/idempotent/concurrent explicit init and crash after no-overwrite binding publication.
- F26: A-to-B restart refusal with byte-for-byte state/directory preservation for PENDING, RETRY_WAIT, IN_FLIGHT, ACKED, and UPLOADED.
- F27: absent/corrupt/noncanonical binding, exact stale-temp recovery, nonpristine refusal, and unknown bound-root inventory refusal.
- F28: binding replacement after a response and before ACKED recovery leaves IN_FLIGHT or ACKED unchanged and performs no false move/success.
- F29: canonical DNS/IPv4/IPv6/default-port aliases and rejection of parser repairs, paths, userinfo, query/fragment, IDNA, zones, numeric aliases, and invalid ports.
- F30: matching init is a no-op; different-origin init is refused even when empty; evidence is retained; no rebind/migration command exists.

## Validation

Windows clean environment, Python 3.12.10:

- New `.pytest_cache/agent-clean-win-2`: `pip install --require-hashes -r agent/screenshot_upload/requirements.lock` PASS; uvloop marker ignored as intended.
- `pip install --no-deps --no-build-isolation .` PASS; `pip check` PASS.
- `python -m agent.screenshot_upload --help` PASS; all three commands present.
- `python -m compileall -q agent/screenshot_upload tests/upload` PASS.
- `python -m pytest tests/upload -q --run-live-upload --basetemp=.pytest_cache/upload-all-submission`: **63 passed in 8.06s**.

Linux clean environment, local Python 3.12.14 image:

- New `/tmp/agent-clean` venv: hash-locked install and `pip check` PASS. The first Linux attempt exposed a missing uvloop pin; the lock was corrected, then clean Linux and second clean Windows installs both passed.
- Read-only workspace mount: uploader synthetic suite PASS. Before the final five F26 parameter cases were added, result was 57 passed, one opt-in live test skipped. The final F26 matrix passed on Windows and uses platform-independent state/binding logic.

Actual response-loss integration (`tests/upload/integration/test_live_response_loss.py`) passed using its own ephemeral `postgres:17-alpine` container, fresh disposable database migrated to Alembic head/0003, temporary storage, separate uvicorn process, and separate uploader child. The child completed a real POST, recorded then discarded the valid 201/`Idempotency-Replayed:false` response from the worker, and exited after durable RETRY_WAIT. Backend and uploader restarted. The exact intent/UUID replayed as 200/true with the same Screenshot ID, `uploaded_at`, and Location. Verification found one COMPLETED receipt, one Screenshot, one object, matching original SHA-256, and successful list/detail/content with multilingual metadata. No test-owned container remained.

Backend03's final report is `.orchestration/reports/BACKEND-UPLOAD-001-03.md`, SHA-256 `7d6fb450f5bfec711bcc633bc934722faf08f5e12d7749cadd86c9fcb0f0f75b`, reporting 94 clean Linux/PostgreSQL tests. A root configured-suite attempt from this task is not claimed because the default shared PostgreSQL service was absent; this task did not start/reset shared services or a user database.

Source whitespace scanning, bytecode compilation, and contract hash verification passed.

## Files and boundary

Production files are the complete `agent/screenshot_upload/` package and its `requirements.in`/`requirements.lock`. Test files are `tests/upload/conftest.py`, `test_origin_binding.py`, `test_producer_state.py`, `test_protocol_json.py`, `test_worker_recovery.py`, `support/fakes.py`, and `integration/{response_loss_agent.py,test_live_response_loss.py}`.

No README, PM YAML, contract, Backend, Frontend, common CLI, commit, push, IP check, real capture, user database, or shared service reset was performed. Two high-complexity subagents were requested as `gpt-5.6-sol/high`; actual applied models were not exposed and remain unverified.

AC-P2-01 through AC-P2-04 remain PM-controlled `NOT_RUN`. Frontend browser acceptance and independent implementation review remain outside this owner submission. Please perform independent implementation review. This report requests `READY_FOR_REVIEW` and does not self-accept `UPLOAD-001` or Phase 2.
