# BACKEND-OCR-001 runtime reproducibility addendum / Backend Engineer 03

- Date: 2026-09-25
- Trigger: PM accepted report `73919a4de478f1c85484f3388ac776b7a85e542cff316fea06d6ff89cb918afc`, handoff `a04677b98e76996020c98d54c1fbb2a61f7f85e2b4bdc7bd39d38f6878979d97`, and 95-file manifest `7b3bb7e5638f1e7cbda101bd2e5451f5453c0b547e410b3b9d7d06a3b8e2e23d`, then received `BACKEND-OCR-001` as `READY_FOR_REVIEW` and activated the Frontend04 live gate.
- Scope: reconstruct the exact commands used for the accepted result summaries and state the evidence limits. No suite was rerun. No product, test, profile, image, PM-state, Frontend04 snapshot or prior evidence file was changed.
- Source remains the accepted 95-file aggregate `bb9c86a548c31bfb69329024ad992e605c41d10f6e7258c9b81dd5cb2237187f`, matched to Worker aggregate `058a445d90b7c50897f77f503a31e7dd425ea71f845a70a40666816e3c7a7b94`.

## Exact commands from the Backend03 task tool-call record

All commands below ran with working directory `C:\Dev\qa-visual-automation`. They are transcribed from this task's command invocations. The command record is retained in the Codex task history, but no standalone argv transcript or content-addressed raw console log was written to the workspace.

### Windows configured suite: 202 passed, 3 skipped, 1 warning, 14.14 seconds

```powershell
.\.pytest_cache\agent-clean-win\Scripts\python.exe -m pytest -q --tb=short -p no:cacheprovider --basetemp .pytest_cache\backend-ocr-runtime-final-20260925-d
```

- Host: Microsoft Windows NT 10.0.26200.0; Python 3.12.14.
- Python executable SHA-256: `0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14`.
- Collection is defined by `pyproject.toml` SHA-256 `55aff766409ac914d161f7c42ddfda7e8a8f8d80213791af6b23fe595423ce57`: `tests/backend`, `tests/integration`, `tests/ocr`.
- `.env` was loaded by application settings. Its values are intentionally not reproduced; file SHA-256 at execution evidence time is `eccb0361531dfd7491051e2acd67aa3a125b987b95b38993d82f4743228596d1`.
- `tests/backend/conftest.py` SHA-256 `5561e5cd0d490b9385075b9d8a34b725752223ffda695c8bf51c6c610e2da79b` creates one `qa_backend_test_<uuid>` database, migrates it, and drops that same isolated test database with `FORCE` during teardown. It does not reset the configured application database.
- The three skips are the opt-in real Linux runtime case and two POSIX raw-IPC framing cases. No model mount or Docker test image was used.

### Linux network-disabled runtime/result/packaging slice: 33 passed, 1 warning, 4.47 seconds

```powershell
docker run --rm --network none qa-backend-ocr-runtime:local python -m pytest tests/backend/test_ocr_runner.py tests/backend/test_ocr_result_validation.py tests/backend/test_packaging_contract.py -q --tb=short -p no:cacheprovider --basetemp /tmp/qa-backend-ocr-focused-final
```

- Image identity: `qa-backend-ocr-runtime:local`, `sha256:81845d5d677a712188bfc7d326448976ca1fff6371a31138f4d19fb50130415c`, Linux amd64, created `2026-09-25T10:39:09.348783039Z`.
- Image build command used immediately before the run:

```powershell
docker build --pull=false --tag qa-backend-ocr-runtime:local --file backend/Dockerfile.test .
```

- `backend/Dockerfile.test` SHA-256: `5f93a520ceee7612def4fae20ed2d9d6ef06ff5d83efebdba54592c828ab8418`.
- Python 3.12.14 slim trixie; working directory `/app`; hash-locked install and `pip check` completed during the image build.
- Network was disabled. This slice used neither PostgreSQL nor a host model mount.
- It includes the confirmed partial-header timeout, truncated-frame retry classification, receiver-thread termination, measured child-RSS failure path, runtime/profile validation and packaging contracts.

### Linux Backend/Worker boundary: 52 passed, 1 warning, 6.59 seconds

```powershell
docker run --rm --network container:qa-visual-automation-postgres-1 --env-file .env -e DATABASE_HOST=127.0.0.1 -e DATABASE_PORT=5432 -e STORAGE_ROOT=/tmp/qa-storage -e PYTHONDONTWRITEBYTECODE=1 -v "C:\Dev\qa-visual-automation\.pytest_cache\phase3-ocr-05\model-cache\official_models:/models/ocr:ro" qa-backend-ocr-runtime:local python -m pytest tests/backend/test_packaging_contract.py tests/backend/test_ocr_result_validation.py tests/backend/test_ocr_runner.py tests/backend/test_ocr_api.py tests/backend/test_ocr_constraints.py tests/backend/test_ocr_migrations.py -q --tb=short -p no:cacheprovider --basetemp /tmp/pytest-backend-worker-boundary-final
```

- The test container shared the network namespace of `qa-visual-automation-postgres-1`; the connection was overridden to `127.0.0.1:5432` because this is the PostgreSQL container's internal port.
- PostgreSQL image observed for this evidence lane: `postgres:17-alpine`, image ID `sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`.
- `docker-compose.yml` SHA-256 `6d981dad7ddce50c529efef35ca7b603f889d9608cf07c1e79abe140744122c1` defines the host-only `127.0.0.1:5433` mapping and internal port 5432.
- The session fixture created and removed a unique `qa_backend_test_<uuid>` database. Storage was overridden per test to pytest `tmp_path`; `STORAGE_ROOT=/tmp/qa-storage` prevented use of the host application storage.
- The model source was mounted read-only at `/models/ocr`. This test selection did not opt into real OCR, but the mount kept the baked image environment identical to the real-runner lane.

### Linux real OCRRunner to isolated PostgreSQL: 1 passed, 1 warning, 7.26 seconds

```powershell
docker run --rm --network container:qa-visual-automation-postgres-1 --env-file .env -e DATABASE_HOST=127.0.0.1 -e DATABASE_PORT=5432 -e STORAGE_ROOT=/tmp/qa-storage -e QA_OCR_REAL_RUNTIME_TEST=1 -e QA_OCR_MODEL_ROOT=/models/ocr -v "C:\Dev\qa-visual-automation\.pytest_cache\phase3-ocr-05\model-cache\official_models:/models/ocr:ro" qa-backend-ocr-runtime:local python -m pytest tests/backend/test_ocr_runtime_integration.py -q --tb=short -p no:cacheprovider --basetemp /tmp/qa-backend-ocr-real-final
```

- Test source `tests/ocr/fixtures/runtime/ja.png` SHA-256: `cdda8d4ffc49236518fe64d4e51361b1694a4e32c0c0b0e7f791eb1b826ede5b`.
- Test file SHA-256: `fc7436eb3b23af8018c52465f727acecd13282fb9ebe971119683934501dbc58`.
- The same isolated-DB fixture and read-only model mount rules above applied.
- The test asserted Linux, `ATTEMPT_SECONDS == 300`, `RSS_LIMIT_BYTES == 2 GiB`, selected the available unified Linux production profile, executed `OCRRunner.run_once()`, and checked durable run/job success, OCR/verification identities, regions, runtime native-package facts and API reads.
- Model provenance file: `.pytest_cache/phase3-ocr-05/model-artifact-manifest.json`, SHA-256 `c1f470956200736ad48dda6e6a8df5bc11daa2a7fda9f1907231e34ef99cc617`. It records three official archives, 23 extracted artifacts and two license files with individual sizes and SHA-256 digests.

## Image and configuration identity

| Artifact | SHA-256 / image identity |
| --- | --- |
| Production image `qa-backend-ocr-production:local` | `sha256:f5864cffb217c86355c747bb1780a5ad4ac786f65ef01a40696131749df6882f` |
| Test image `qa-backend-ocr-runtime:local` | `sha256:81845d5d677a712188bfc7d326448976ca1fff6371a31138f4d19fb50130415c` |
| `backend/Dockerfile` | `6f871aca46a4894aab2dbedffe35ffa26664ccee4a36cfee3cf0e3bf4bb35d8b` |
| `backend/Dockerfile.test` | `5f93a520ceee7612def4fae20ed2d9d6ef06ff5d83efebdba54592c828ab8418` |
| `backend/requirements.lock` | `30c023d97b69a0d4e82a449bb88bc0fb542e95bf5c07674215821bd769661352` |
| `pyproject.toml` | `55aff766409ac914d161f7c42ddfda7e8a8f8d80213791af6b23fe595423ce57` |
| `docker-compose.yml` | `6d981dad7ddce50c529efef35ca7b603f889d9608cf07c1e79abe140744122c1` |
| `.env` without disclosing values | `eccb0361531dfd7491051e2acd67aa3a125b987b95b38993d82f4743228596d1` |
| `alembic.ini` | `14ea2e462241366748b491afe0f46a0a16452e4e95a3509e5633d54765b4149c` |
| accepted runtime report | `73919a4de478f1c85484f3388ac776b7a85e542cff316fea06d6ff89cb918afc` |
| accepted runtime handoff | `a04677b98e76996020c98d54c1fbb2a61f7f85e2b4bdc7bd39d38f6878979d97` |
| accepted 95-file manifest | `7b3bb7e5638f1e7cbda101bd2e5451f5453c0b547e410b3b9d7d06a3b8e2e23d` |

The production image build used:

```powershell
docker build --pull=false --tag qa-backend-ocr-production:local --file backend/Dockerfile .
```

## Raw-log inventory and evidence limit

| Result | Workspace raw log/JUnit path | Raw-log SHA-256 | Preserved source |
| --- | --- | --- | --- |
| Windows 202 | none | not applicable | Backend03 Codex task command/output record; accepted report lines 30-32 |
| Linux 33 | none | not applicable | Backend03 Codex task command/output record; accepted report line 37 |
| Linux 52 | none | not applicable | Backend03 Codex task command/output record; accepted report line 38 |
| real runner 1 | none | not applicable | Backend03 Codex task command/output record; accepted report line 39 |

The pytest `--basetemp` directories are temporary workspaces, not console logs. No `--junitxml`, stdout redirection or transcript file was configured for these four final invocations. The exact commands above can be recovered from the task's tool-call record, while stdout/stderr bytes, start/end timestamps and generated UUID database names cannot be assigned a filesystem location or SHA-256 after the fact. Worker05 evidence under `.pytest_cache/phase3-ocr-05/evidence` belongs to the separate Worker qualification and must not be presented as these four Backend03 raw logs.

## Whole-attempt storage-read correction

The accepted report's limitation statement is not a waiver of the revision-2 whole-attempt 300-second contract. Current code does **not** provide a bounded elapsed-time guarantee for source storage read.

- `backend/app/workers/ocr.py` SHA-256 `f76b975aed52b07e34b554bf63f6059889f396ea6f0ece08db350bb9d7499839` establishes the absolute deadline immediately after claim, then calls `_run_input()` on the parent thread.
- `_run_input()` calls `storage.open_read()` and one blocking `stream.read(expected_size + 1)` before the supervised OCR child starts. It receives no deadline or cancellation handle.
- `backend/app/storage/local.py` SHA-256 `ca93d0dce1418ee0db6b2868fdda5c1328e2cf1958411cb0df2214219f370afc` uses `Path.open("rb")` and `os.fstat()` without a timeout.
- `expected_size + 1` bounds bytes retained and size/SHA-256 checks protect integrity. The API stage normally limits uploads to 20 MiB. Neither mechanism bounds elapsed I/O time, and durable metadata does not independently enforce the 20-MiB maximum.
- The heartbeat records `ENGINE_TIMEOUT` after the deadline and stops renewing the 60-second lease, allowing fenced recovery. It cannot interrupt the blocked parent read. The post-read deadline check prevents late publication only after the read returns.
- The database `connect_timeout=5` and transaction timeouts do not apply to filesystem I/O.

Therefore the current guarantees are bounded data volume on the normal upload path, immutable size/hash validation, lease recovery and fenced result publication. There is no evidence or mechanism proving source-read-to-matching completion within 300 seconds when storage blocks. The contract hash that requires the whole-attempt limit is `478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44`.

## Proposed product correction for PM scheduling

Backend03 proposes a separate coordinated change after Frontend04 captures or releases its active live snapshot:

1. Split `_run_input()` into bounded metadata loading and supervised source reading.
2. Validate `1 <= expected_size <= 20_971_520` before opening storage so corrupted durable metadata cannot bypass the ingress limit.
3. Run source open/read/close in a separately terminable `spawn` process reconstructed from a serializable storage specification. A Python thread alone is insufficient because a blocked filesystem read cannot be safely cancelled.
4. Supervise that process with the same absolute deadline already used by OCR/verification. Do not allocate a fresh 300 seconds after reading.
5. Read at most `expected_size + 1`, return bytes through bounded IPC, and retain parent-side length and SHA-256 verification.
6. On deadline, terminate/kill/join the reader and record retryable `ENGINE_TIMEOUT`; on storage error, retain `INPUT_STORAGE_UNAVAILABLE`; never launch the OCR child or finalize results after reader timeout.
7. Bound `_stop()` by the remaining absolute budget. Its current terminate and kill joins may add up to ten seconds after deadline.
8. Add Windows-spawn and Linux tests for a permanently blocked read, shared remaining budget, 20-MiB boundaries, partial source IPC, child termination, retry state and absence of result/finalize writes.

This change is internal to runner/storage execution and should not alter public API payloads. It will change Backend source hashes and both image identities, so PM should schedule a new Backend03 manifest/image qualification and the affected Frontend04 live verification after the active snapshot is released. No part of this proposal was implemented in this addendum.

## RSS limitation retained

The 2-GiB mechanism samples only the direct OCR child PID approximately every 250 ms. It is not an OS cgroup/Job Object hard cap, does not include a descendant process tree and can miss a short peak. Strict enforcement would require a Linux cgroup limit and a Windows Job Object limit, with platform-specific qualification. The current sampled-RSS test remains valid only for the implemented monitor.

## Change control

No test was rerun for this addendum. No product, test, dependency, image, model, database, PM state, Frontend04 snapshot or accepted evidence artifact was modified. The only new file is this uniquely named addendum.
