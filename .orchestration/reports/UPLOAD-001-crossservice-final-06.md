# UPLOAD-001 corrected-final cross-service evidence

Date: 2026-09-25 KST. Contract: `P2-UPLOAD-v1`, document revision 2. This report records the final uploader against Backend03's corrected stable snapshot. It changes no product source and does not replace earlier owner reports.

## Result

The response-loss/restart/replay live integration passed against the corrected Backend snapshot: **1 collected, 1 passed in 3.15s**.

The executed test retained the existing integration body in `tests/upload/integration/test_live_response_loss.py` and verified:

- a real first POST completed and returned 201 with `Idempotency-Replayed:false`;
- that valid response was recorded and deliberately discarded before uploader acknowledgement;
- durable uploader state was `RETRY_WAIT` with one attempt;
- Backend and uploader processes restarted;
- the same intent and client upload ID replayed as 200 with `Idempotency-Replayed:true`;
- replay preserved Screenshot ID, `uploaded_at`, and Location from the discarded response;
- exactly one COMPLETED receipt, one Screenshot row, and one stored object existed;
- list and detail returned the expected identity and multilingual nested metadata;
- content returned 200 and its SHA-256 matched the original uploader item hash.

## Matched snapshots

- Backend source manifest: 75 files, aggregate SHA-256 `d1799260941c7396c4e3931f21eb07e4857e90f7075d84fba962a1f5b672a0fe`, independently recomputed from the current workspace using the report's sorted UTF-8 `relative/path sha256` format with one final LF.
- `backend/app/services/screenshots.py`: `3c5e36450160f57f732071f8c9bf4eed5684c978e887f499264eee1f50dc7a2b`.
- `backend/app/storage/local.py`: `ca93d0dce1418ee0db6b2868fdda5c1328e2cf1958411cb0df2214219f370afc`.
- Backend rework report: `b83e53bbc787020b6c81b0b32b57dff3e8a65d3d49d8152911d70b529edac968`.
- Backend rework handoff: `68335accb905f4efafc0545a2ecce7d7c94a9c5cd41c93dea1c44c7fd8a19c8a`.
- Backend raw rework log: `a31e384c36e8f0caa28f1102496bc3ddf2f8786f3bc27bb0c4f9216622a4d8b1`.
- Uploader/test manifest aggregate: `593e1925a36e55b667c752be7cc10ea944f14cf81f034f5d112d23358f7a563e`, matching `.orchestration/reports/UPLOAD-001-linux-final-06.md`.
- Hash lock: `agent/screenshot_upload/requirements.lock` SHA-256 `ff214596558d1af98ab54b54fd0271a4ef5e0059d5df4d7b520738aa52cf5344`.

## Environment and isolation

- Runtime image: `qa-backend-upload-final:local`, Debian 13 / Python 3.12.14.
- Source input: `C:\Dev\qa-visual-automation` mounted read-only.
- Execution copy: `/tmp/cross-final`; all existing `__pycache__` and `*.pyc` removed before execution.
- Bytecode files in execution source: 0 before and 0 after.
- Dependencies: new `/tmp/cross-final-venv`, installed with `pip --require-hashes`; `pip check` returned `No broken requirements found.`
- Database: test-owned `postgres:17-alpine` container `qa-upload-corrected-live-06`, random host port, synthetic credentials, random per-test database, force-dropped by the integration test and container stopped in the host `finally` block.
- Backend storage and uploader spool: pytest temporary directories inside the ephemeral runtime container.
- Evidence interval: `2026-09-24T17:03:52Z` through `2026-09-24T17:04:07Z` (`2026-09-25 02:03:52` through `02:04:07` KST).

The Windows Python 3.12 base interpreter had been removed, so prior Windows venv executables could not launch. To keep the product test body unchanged, a temporary pytest plugin replaced only the test's Docker-CLI setup/cleanup helpers with the externally managed ephemeral PostgreSQL URL. The plugin did not alter assertions, Backend/API/uploader subprocess behavior, response-loss injection, restart behavior, database queries, object checks, or HTTP checks. It was deleted immediately after execution.

## Effective commands

The host started and later stopped the isolated database:

```powershell
docker run --rm -d --name qa-upload-corrected-live-06 `
  -e POSTGRES_USER=upload_test -e POSTGRES_PASSWORD=upload_test_password `
  -e POSTGRES_DB=postgres -p 127.0.0.1::5432 postgres:17-alpine
```

The Linux runtime used the read-only workspace, copied the required Backend/uploader/test sources to `/tmp`, removed bytecode, created a new venv, installed the lock, and ran:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/tmp/cross-final:/tmp/cross-final/plugin \
/tmp/cross-final-venv/bin/python -m pytest \
  tests/upload/integration/test_live_response_loss.py \
  --run-live-upload -p upload_external_pg_plugin -vv \
  -p no:cacheprovider --basetemp=/tmp/cross-final-pytest
```

## Raw output

```text
EVIDENCE_START_UTC=2026-09-24T17:03:52Z
BACKEND_SERVICE_SHA256=3c5e36450160f57f732071f8c9bf4eed5684c978e887f499264eee1f50dc7a2b
UPLOADER_MANIFEST_AGGREGATE_SHA256=593e1925a36e55b667c752be7cc10ea944f14cf81f034f5d112d23358f7a563e
BYTECODE_FILES_BEFORE_RUN=0
No broken requirements found.
============================= test session starts ==============================
platform linux -- Python 3.12.14, pytest-9.1.1, pluggy-1.6.0 -- /tmp/cross-final-venv/bin/python
rootdir: /tmp/cross-final
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 1 item

tests/upload/integration/test_live_response_loss.py::test_real_backend_restart_and_uploader_restart_replay_one_receipt PASSED [100%]

============================== 1 passed in 3.15s ===============================
BYTECODE_FILES_AFTER_RUN=0
EVIDENCE_END_UTC=2026-09-24T17:04:07Z
```

## Boundary

No product source, original report, PM YAML/decisions, Frontend, Web runtime, shared service, user database, commit, push, or IP check was changed or used. The temporary PostgreSQL container, runtime container, plugin, database, storage, spool, and test files were removed. This is owner integration evidence and does not self-accept `UPLOAD-001`, Backend work, or Phase 2 acceptance criteria.
