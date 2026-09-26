# REVIEW-UPLOAD-001 / Reviewer 08 independent implementation review

Date: 2026-09-25 KST  
Reviewer: 08  
Activation: C:\Dev\qa-visual-automation\.orchestration\handoffs\REVIEW-UPLOAD-001-activation-01.md  
Contract: P2-UPLOAD-v1 document revision 2, SHA-256 e47d3dca18fef169600bf6bebe78a31432105e5a1ae5b80a9934e1bf4ee8f843

## Disposition

CHANGES_REQUESTED.

The submitted implementation cannot be accepted. Independent inspection found four new product defects: unbounded Backend request-body concurrency, unconditional acceptance of network-backed spool filesystems on non-Windows platforms, divergent origin canonicalizers, and a finalize-time reference deletion race that returns the wrong contract response. The required real-PostgreSQL receipt/fencing matrix, corrected Backend regressions, uploader runtime matrix, current-harness live Web flow, and cross-service lost-response replay could not be independently executed in this review environment. Owner results are retained as owner evidence and are not relabeled independent PASS.

PM remains the sole owner of .orchestration/ACCEPTANCE.yaml, TASKS.yaml, PROJECT_STATE.yaml, and phase status. This review does not edit those files.

## Acceptance matrix

| Criterion | Reviewer result | Independent evidence and limit |
| --- | --- | --- |
| AC-P2-01 Durable offline queue preserves originals | FAIL / not acceptable | Static inspection found that agent/screenshot_upload/durable_fs.py:50-53 accepts every non-Windows filesystem without identifying NFS/SMB/network mounts, contrary to contract lines 165, 167, and 310. Origin initialization/worker canonicalization also diverges for http://0x and http://0X. No independent uploader crash/restart suite ran. |
| AC-P2-02 Retry/backoff and terminal failures | NOT_RUN / not acceptable | No static retry/backoff defect was established in the bounded review, but the independent uploader suite never entered collection and the live restart/replay flow could not be provisioned. Owner Windows 63 PASS and Linux 62 PASS + 1 opt-in live skip remain owner evidence only. |
| AC-P2-03 Idempotency and duplicate prevention across restart | FAIL / not acceptable | The required real-PostgreSQL concurrent reservation, exact-expiry takeover, stale fencing, ambiguous commit, lock-timeout, atomic Screenshot+receipt, and restart matrix was not independently executed. The three preflight findings remain open pending runtime closure. Backend request concurrency is unbounded, and finalize has a confirmed reference-deletion race that returns 503 instead of the required existing 404/422. |
| AC-P2-04 Uploaded screenshots and metadata appear in Web | NOT_RUN / not acceptable | Reviewer Vitest execution passed 2 files / 26 tests, covering component/API behavior. The owner live JSON was produced with tests/frontend/run_integration.py hash d74a05..., while the submitted current harness is ae5b90.... Docker/WSL restrictions prevented a current-harness agent-to-Backend-to-Web rerun. |

Required criteria are therefore not independently established, and two criteria have current product blockers.

## Exact source and evidence identity

All reads used explicit root C:\Dev\qa-visual-automation. The inherited writable workspace was not treated as product source.

| Item | SHA-256 / result |
| --- | --- |
| Accepted contract | e47d3dca18fef169600bf6bebe78a31432105e5a1ae5b80a9934e1bf4ee8f843 |
| Backend canonical 75-file source manifest | 1464c7678cf044f0da996c19cc0174dc31581306e7c011ba98ff1e5d1dc754e5 |
| Backend manifest verification | PASS: all 75 current hashes and ordinal inventory matched |
| Uploader current source-manifest aggregate | 593e1925a36e55b667c752be7cc10ea944f14cf81f034f5d112d23358f7a563e |
| Backend rework report | b83e53bbc787020b6c81b0b32b57dff3e8a65d3d49d8152911d70b529edac968 |
| Backend rework handoff | 68335accb905f4efafc0545a2ecce7d7c94a9c5cd41c93dea1c44c7fd8a19c8a |
| Backend rework raw log | a31e384c36e8f0caa28f1102496bc27bb0c4f9216622a4d8b1 |
| Backend manifest addendum | e89185a0c8f036d5bcb3a28f048167cc3bbe1c63ecb076b6dfd20e1ec6aa43c5 |
| Uploader cross-service report | a6b0c34fefefba6949117067e0f862dd1e0f085cda57da42d12d5b276b2601e0 |
| Uploader manifest correction | fbfb34dc2e9f9c65ec4e6f665cafb61fbb3455abef9f3047b6e377c5041ad00c |
| Uploader reproducibility addendum | c81bd8c5d4544f135d6d43c45e1ef0066be0214c30d6625e5b05cd697cd6c865 |
| Final Linux uploader report | 9f0822f563e493650eab23ec8d3fd8e1d819f093e331cc1e56bd3f3ab6643ab6 |
| Web report | caa5bd1d03b74f044b86017c13884c97dd272c1b6baf8bfbd3c594280708edcc |
| Web handoff | 9a4f4fc358d1d14688bad68f4b5d8b5185b1708c57ed2f0143534eda031c1b19 |
| Corrected Web JSON | 8bcd4d64a36239f6d7dacad8b669b816681e4469f91da66f612161b1844ece71 |
| Web JSON recorded harness | d74a05c9d897fbefe4b85a08626e78c20169f7c91072eae4346d912750970efd |
| Current tests/frontend/run_integration.py | ae5b901de8a8e41caeca62aa2bf982a7f56e2269538dfbe47c3a3fa74713862e |
| Preflight report | 888aa5245bc9b46bd99ef21080412f5b7dd8f35ee3ab797c4216d0c7d835fadf |

The Backend report's historical d1799260941c7396c4e3931f21eb07e4857e90f7075d84fba962a1f5b672a0fe aggregate reflects culture-sensitive ordering and is superseded by the canonical ordinal manifest above; it is not source drift. Product hashes recorded in the corrected Web JSON match the current product files. The live harness hash alone does not match.

Relevant current file hashes:

| File | SHA-256 |
| --- | --- |
| backend/app/api/middleware.py | c6c5e894dc1d91bc7eb4dcffa09c03619514af20d40568874f984804f4b4abad |
| backend/app/main.py | b01b9e03bd7097941ea63dfbb2ff9899a29965a74cf18d2726fe30f15955353b |
| backend/Dockerfile | 239178bc679d5106ccf4dead48d736a45d30c9c8ad09565a852d96e232768951 |
| backend/app/services/screenshots.py | 3c5e36450160f57f732071f8c9bf4eed5684c978e887f499264eee1f50dc7a2b |
| backend/app/services/upload_receipts.py | 287a5f2eecd6269e79b2a5440e9a2381cb9625036fc711192b7b1d9f2298c0c4 |
| backend/app/services/catalog.py | ea155218a183ddc9effed34864e8521cde68c502333001838439ee43f30058eb |
| backend/app/repositories/catalog.py | 478f6dbc3d2cbb41ce4af00525b56cc74c5b8dae9f1d9bac6fba4ad30df16752 |
| backend/app/repositories/upload_receipts.py | 804dd0073af6369227f36e83d5b43d7a1870cecaae1f00ed36e9c3b0db693d55 |
| tests/backend/test_screenshots.py | cc59cefb41b372e51608ea1afc1cec8af69f9a7e3fb0b8773922604b2aca68d2 |
| tests/backend/test_reconcile_upload_receipts.py | 692b5bf25ac92da50e60df8a2a52c26ad4ce021eff775fc7ab059301409c3bc2 |
| tests/backend/test_migrations_storage.py | e7b122e0045c16d6015d8819bd488e8460df85b3cbfa4cdc9650f91e283c8bda |
| agent/screenshot_upload/durable_fs.py | 762e1f6426f77a81191de5908b95a4f2347635b922eeb66224f1ea93e0eb2bf3 |
| agent/screenshot_upload/origin.py | 740a4453eabdee17ead080a4d6ca1586a2a68975d0e06980bdb2870ecb9bbdf8 |
| agent/screenshot_upload/config.py | 5385fd90f751d9f5bc5c53e7fcdd7f166b83771ed775c6098e06bbbe70863b89 |
| agent/screenshot_upload/__init__.py | 3a1e99173d7efe67005b34ff02e85752199c5d4a093166e784e6a076b9a0d5d2 |

## Finding dispositions

### R08-P2-PREFLIGHT-001 — MAJOR — OPEN, corrected-source candidate not independently closed

The corrected content path now hashes the exact bytes read from one handle and returns 503 for mismatch at backend/app/services/screenshots.py:225-241. tests/backend/test_screenshots.py:154-218 now covers normal, missing, different-length, and same-length corruption, one open, and retained DB/receipt/object state. This is directionally sufficient source and test design.

The required targeted PostgreSQL execution did not start because the independent environment could not access Docker/WSL and the repository virtual environment launcher is broken. Owner 29 PASS and full 119 PASS are supporting owner evidence, not Reviewer execution. Disposition remains OPEN pending a matching independent runtime result.

### R08-P2-PREFLIGHT-002 — MAJOR — OPEN, corrected-source candidate not independently closed

tests/backend/test_reconcile_upload_receipts.py:32-273 now contains a real-PostgreSQL F14 matrix covering live/expired receipt references, durable FAILED transition, refreshed inventory, fresh-reference barrier, age boundary, and fail-closed paths. Static inspection found no replacement blocker in that bounded correction.

The matrix was not independently executed. The implementation contains an explicit pg_is_in_recovery() fail-closed path, but neither the submitted matrix nor this review executed it against an actual recovery/standby PostgreSQL server. Owner results cannot close the finding, so it remains OPEN.

### R08-P2-PREFLIGHT-003 — MAJOR — OPEN, corrected-source candidate not independently closed

tests/backend/test_migrations_storage.py:44-140 now snapshots the complete populated 0002 row, nested Unicode metadata, relationships/timestamps, and referenced object bytes through 0003. Static inspection found the corrected fixture directionally adequate.

The PostgreSQL migration case was not independently executed. It remains OPEN.

### R08-P2-REVIEW-004 — MAJOR / P1 — OPEN evidence gap: required receipt/fencing transaction matrix absent from independent execution

No concrete static receipt-service defect was established, and focused in-memory probes supported exact-expiry takeover, stale-fence denial, and Retry-After rounding. Those probes are not database or transaction evidence.

The acceptance-critical real-PostgreSQL matrix remains unproved independently: simultaneous first insert arbitration; DB-clock just-before/equal/after expiry; generation/token/candidate-key freshness; stale-owner denial through persisted transactions; ambiguous first-insert, takeover, and finalize outcomes; confirmed rollback mutation constraints; lock timeout and HTTP Retry-After; exact same-generation recovery; and atomic Screenshot plus receipt completion. This blocks AC-P2-03.

### R08-P2-REVIEW-005 — MAJOR / P1 — OPEN product defect: Backend buffering has unbounded request concurrency

Contract line 26 permits bounded in-memory buffering only when request concurrency is bounded. backend/app/api/middleware.py:88-98 buffers every POST/PUT/PATCH body into a bytearray up to 22,020,096 bytes. backend/app/main.py has no application semaphore. backend/Dockerfile:9 and the README launch commands start Uvicorn without --limit-concurrency. The installed Uvicorn configuration default is limit_concurrency=None.

Counterexample: N simultaneous slow uploads can each retain approximately the wire-limit body plus parser/decoder copies before receipt arbitration or storage fencing. Memory therefore grows with unauthenticated connection count and can exhaust the service. The implementation violates the explicit accepted condition for retaining whole-body buffering.

Required correction: impose and test a documented bounded request concurrency limit at the deployed server/application boundary, including overload behavior and memory-bounded slow concurrent uploads.

### R08-P2-REVIEW-006 — MAJOR / P1 — OPEN product defect: Linux network-backed spools are accepted

Contract lines 165 and 167 require one local volume and rejection of network shares/unsupported locking or atomic operations; line 310 requires unsupported filesystems to fail closed. agent/screenshot_upload/durable_fs.py:50-53 returns immediately whenever os.name is not nt. A Linux NFS/SMB/network mount that appears as an ordinary directory therefore passes ensure_local_filesystem without any filesystem-type or capability decision.

The owner's Linux evidence used a local /tmp filesystem and does not cover this boundary. Required correction: detect and reject unsupported/non-local Linux filesystem types or perform a support/capability check that fails closed, with representative network-mount coverage.

### R08-P2-REVIEW-007 — MAJOR / P2 — OPEN product defect: origin canonicalizers disagree

agent/screenshot_upload/origin.py:53-64 and 82-127 accepts bare DNS host 0x/0X and canonicalizes it to 0x. agent/screenshot_upload/config.py:21-35 rejects the same host because all(char in hex for char in final[2:]) is true for the empty suffix. RuntimeConfig applies the latter at lines 125-140; initialize_binding applies the former at origin.py:250-305 and is exported publicly by agent/screenshot_upload/__init__.py.

Independent bundled-Python result:

    origin 'http://0x' RETURN 'http://0x'
    config 'http://0x' RAISE ConfigError 'hexadecimal host notation is unsupported'
    origin 'http://0X' RETURN 'http://0x'
    config 'http://0X' RAISE ConfigError 'hexadecimal host notation is unsupported'

This creates two different accepted-origin sets for immutable binding and runtime configuration and violates F29 canonicalizer parity/fail-closed continuity. Required correction: one canonicalizer or exhaustive parity tests across the F29 boundary corpus, including bare 0x/0X.

### R08-P2-REVIEW-008 — MAJOR / P2 — OPEN evidence gap: live Web evidence is not source-locked to the submitted harness

The corrected Web JSON identifies tests/frontend/run_integration.py as d74a05c9d897fbefe4b85a08626e78c20169f7c91072eae4346d912750970efd. The current submitted file hashes to ae5b901de8a8e41caeca62aa2bf982a7f56e2269538dfbe47c3a3fa74713862e. All listed product source hashes match current source, so the mismatch is isolated to the evidence harness, but a live run of the current harness did not occur.

The JSON demonstrates an owner-run agent upload and manual multipart upload with exact content/hash and multilingual nested metadata. It does not independently prove the current harness, and it does not contain an actual automation-source upload or empty-string metadata case; those are covered only by component tests. A current-harness isolated live rerun is required before AC-P2-04 can be accepted.

### R08-P2-REVIEW-009 — MEDIUM / P2 — OPEN product defect: finalize reference deletion race returns 503 instead of required 404/422

Contract lines 103 and 144 require scoped-reference revalidation in the short READ COMMITTED finalize transaction. Line 146 is explicit that reference disappearance during finalization yields the existing 404/422, keeps immutable receipt identity, and records FAILED only after confirmed rollback.

backend/app/services/upload_receipts.py:274 calls _references before inserting the Screenshot. _references delegates to validate_references, whose repository reads at backend/app/repositories/catalog.py:6-15 are ordinary SELECT statements unless lock=True; this path does not request a lock. A concurrent transaction can therefore delete and commit a Build, Locale, Category, or Situation after the successful validation read but before repo.insert_screenshot flushes at upload_receipts.py:281. The Screenshot foreign key then raises PostgreSQL 23503. The inner handler rolls back and performs fenced FAILED bookkeeping, but the outer SQLAlchemyError handler at lines 304-305 converts the error to 503 DATABASE_UNAVAILABLE. It never reaches the general database_error mapping and cannot return the contract-required reference-specific 404/422.

This is a deterministic transaction interleaving, not merely missing evidence. It does not create a duplicate or corrupt committed row, so severity is MEDIUM rather than MAJOR, but it violates finalize response semantics and delays correction behind an unnecessary infrastructure error. Existing tests do not place a concurrent parent delete between reference validation and Screenshot insert.

Required correction: keep every scoped parent stable through Screenshot insertion, for example by acquiring suitable PostgreSQL row locks during finalize revalidation, and add a two-connection test at the validation/insert barrier proving either successful finalize with the parent retained or the specified 404/422 plus same-generation FAILED after confirmed rollback. Preserve the five-second bounded wait behavior.

## Additional audit dispositions

- Renewal stop/join boundary: not confirmed as an acceptance-blocking defect. LeaseKeeper waits five seconds while receipt transactions use a five-second lock timeout. A renewal acquiring the lock at the boundary could commit shortly after the request returns 503, extending PROCESSING for up to approximately 60 seconds and causing a same-ID retry to receive temporary 409. This is a LOW liveness/diagnostic risk, but the next response carries the current lease delay, the original/published object is retained, fencing remains intact, and expiry permits takeover. No duplicate, corruption, or permanent loss counterexample was established. Add a boundary test or join margin during hardening; no separate blocking finding is opened.
- Recovery-primary guard: backend/app/maintenance/reconcile_storage.py contains the pg_is_in_recovery() rejection path, but no submitted direct test runs reconciliation against a real recovery server. This limit is retained under open preflight finding 002 rather than duplicated as a new finding.

## Independent commands, environment, and results

Environment: Microsoft Windows NT 10.0.26200.0; PowerShell 7.6.5; bundled Python 3.12.14; bundled Node v24.19.0; Vitest 5.0.0. Product root was read-only to this task. No IP connectivity check was performed.

| Command/check | Reviewer result |
| --- | --- |
| Get-FileHash -Algorithm SHA256 over contract, submitted artifacts, manifests, Web JSON/harness, and finding files | PASS; hashes recorded above |
| PowerShell manifest parser: verify each of 75 Backend path/hash lines against current files and compare ordinal rg --files inventory | PASS; canonical manifest 1464c7..., files=75 |
| Bundled Node running frontend/node_modules/vitest/vitest.mjs run tests/api.test.ts tests/components.test.tsx --config C:\Users\dldnj\OneDrive\ドキュメント\ChatGPT\New project 2\r08-web-d\vitest.review.config.mts --no-file-parallelism | PASS; 2 files, 26 tests, duration 1.88s |
| Bundled Python import of canonicalize_origin and canonical_backend_origin for http://0x and http://0X | PASS as a counterexample; exact divergent output recorded in finding 007 |
| .venv\Scripts\python.exe --version | BLOCKED; launcher returned exit 101: Unable to create process using C:\Users\dldnj\AppData\Local\Programs\Python\Python312\python.exe |
| Docker API precondition for disposable PostgreSQL/Backend/uploader/Web environments | BLOCKED; Windows named-pipe access denied in this sandbox; no container or database was created |
| WSL enumeration/runtime fallback | BLOCKED; access denied in this sandbox |
| Corrected Backend targeted tests and full PostgreSQL suite | NOT_RUN; execution never started |
| Receipt concurrency/expiry/takeover/fencing/ambiguous-commit matrix | NOT_RUN against PostgreSQL; only non-DB focused probes/static inspection completed |
| Uploader Windows/Linux crash/restart/binding/live lost-201 suites | NOT_RUN independently; no test collection started |
| Cross-service discarded-201, Backend+uploader restart, exact 200 replay | NOT_RUN independently |
| Current-harness live agent/automation/manual Web flow | NOT_RUN independently; provisioning blocked before service start |

The review-local Vitest config was created outside product source only to redirect cache into the writable review workspace. Its SHA-256 is 0e9a9c9ecfe822a2b0ed9253bd109cbf1b9780bc00499c60a092f5fb7ca22739 and it does not replace tests/frontend/run_integration.py.

## Owner evidence retained without relabeling

| Area | Owner-reported result | Reviewer use |
| --- | --- | --- |
| Backend correction | 29 targeted PASS; 119 full Linux/PostgreSQL PASS | Artifact/source/test-design support only; independent execution absent |
| Uploader Windows | 63 PASS including live lost-201/restart/replay | Owner evidence only |
| Uploader Linux | 62 PASS + 1 opt-in live skip | Owner evidence only; local /tmp does not test network mounts |
| Corrected cross-service | 1 PASS | Owner evidence only |
| Web live JSON | agent and manual records, exact content/hash, nested multilingual metadata | Owner evidence only; harness hash mismatch prevents source-locked replay claim |

## Model attribution

Activation requested parent gpt-5.6-sol/high, high-risk gpt-5.6-sol/high, highest-risk gpt-6-astra/medium, medium gpt-5.6-sol/medium, and low gpt-5.6-terra/high routing. The review runtime did not expose auditable actual model identifiers for the parent or bounded subagents; actual models are therefore recorded as unverified rather than inferred from requested routing. Subagent work was bounded to receipt/fencing, Backend correction, uploader, Web, and static/hash slices; Reviewer 08 independently integrated and checked every finding reported here.

## Scope, changes, and next action

No product source, tests, contract, mobile proposal, owner artifact, PM YAML/state, database, service, shared environment, or user capture was changed. No Commit or Push was performed. Branch / commit: null / null.

PM notification to task 01a06f36-8c18-7e01-8783-34f726415b9b was attempted after artifact readback. After explicit user authorization, a second follow-up call was attempted with the updated finding 009 and artifact hashes. Both calls were rejected because the app requires approval while this review's enforced approval policy is never. The notification was therefore NOT_SENT and no bypass was attempted.

Because this task's filesystem policy did not permit writing C:\Dev\qa-visual-automation, the required report and handoff were staged byte-for-byte in the writable review workspace and the repository write was attempted but denied. PM should copy/hash-verify the staged artifacts into the required repository paths, retain CHANGES_REQUESTED, route findings 005/009 to Owner 03 and 006/007 to Owner 06, require the current-harness Web rerun for 008, and reactivate Reviewer 08 only after matching corrected submissions and an environment capable of isolated Docker/PostgreSQL/uploader/Web execution.
