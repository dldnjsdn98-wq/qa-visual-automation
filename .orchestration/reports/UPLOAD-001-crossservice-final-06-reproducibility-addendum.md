# UPLOAD-001 cross-service reproducibility addendum

Date: 2026-09-25 KST. This report-only addendum supplements `.orchestration/reports/UPLOAD-001-crossservice-final-06.md` without modifying that original report, product source, or test source. No test was rerun for this addendum.

## Setup difference from the checked-in integration test

The checked-in test normally calls Docker CLI from Python to start and stop its own PostgreSQL container. The Linux runtime image used for the corrected-final cross-service run had Python 3.12.14 but no `docker` executable. The host therefore created and stopped the same disposable `postgres:17-alpine` service. A temporary pytest plugin replaced only these two module functions after collection:

- `_start_postgres(port, name)` returned a SQLAlchemy admin URL for the host-managed disposable PostgreSQL container;
- `_stop_postgres(name)` was a no-op because the host `finally` block owned container cleanup.

The plugin did not replace or edit the test function, its assertions, `_migrate`, `_start_api`, `_stop_api`, uploader subprocess commands, response-loss helper, database creation/drop, HTTP clients, storage checks, or receipt/Screenshot queries. The checked-in test still created a random `qa_upload_live_<uuid>` database, migrated it to head, force-dropped it in its own `finally`, and executed all assertions. Only outer PostgreSQL container ownership differed.

## Exact temporary plugin

The plugin was created at `.pytest_cache/upload_external_pg_plugin.py`, copied into the ephemeral execution root, loaded with `-p upload_external_pg_plugin`, and deleted from the workspace immediately after the run. Its complete content was:

```python
from __future__ import annotations

import os


def pytest_collection_modifyitems(session, config, items):
    del session, config
    module = next(
        item.module
        for item in items
        if item.module.__name__.endswith("test_live_response_loss")
    )
    admin_url = module.URL.create(
        "postgresql+psycopg",
        username=os.environ["LIVE_PG_USER"],
        password=os.environ["LIVE_PG_PASSWORD"],
        host=os.environ["LIVE_PG_HOST"],
        port=int(os.environ["LIVE_PG_PORT"]),
        database="postgres",
    )

    def external_postgres(_port: int, _name: str):
        return object(), admin_url

    module._start_postgres = external_postgres
    module._stop_postgres = lambda _name: None
```

Because the hook runs at `pytest_collection_modifyitems`, the test module was already imported and the collected test item still referred to the original test function. The patch changed the two global helper lookups used when that test function executed; it did not modify collection, selection, or assertions.

## Exact host orchestration

The host command used synthetic credentials, an automatically assigned loopback port, readiness polling, URL fields passed as environment variables, and unconditional cleanup:

```powershell
$ErrorActionPreference = 'Stop'
$pgName = 'qa-upload-corrected-live-06'
$pgUser = 'upload_test'
$pgPassword = 'upload_test_password'

docker run --rm -d --name $pgName `
  -e "POSTGRES_USER=$pgUser" `
  -e "POSTGRES_PASSWORD=$pgPassword" `
  -e POSTGRES_DB=postgres `
  -p 127.0.0.1::5432 postgres:17-alpine
if ($LASTEXITCODE -ne 0) { throw 'ephemeral PostgreSQL start failed' }

try {
  $ready = $false
  for ($i = 0; $i -lt 100; $i++) {
    docker exec $pgName pg_isready -U $pgUser -d postgres *> $null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Start-Sleep -Milliseconds 200
  }
  if (-not $ready) { throw 'ephemeral PostgreSQL readiness timeout' }

  $mapping = docker port $pgName 5432/tcp | Select-Object -First 1
  $pgPort = [int](($mapping -split ':')[-1])

  docker run --rm `
    --add-host host.docker.internal:host-gateway `
    -e LIVE_PG_HOST=host.docker.internal `
    -e "LIVE_PG_PORT=$pgPort" `
    -e "LIVE_PG_USER=$pgUser" `
    -e "LIVE_PG_PASSWORD=$pgPassword" `
    -v "C:\Dev\qa-visual-automation:/workspace:ro" `
    -w /workspace qa-backend-upload-final:local `
    sh -ec '<container evidence script below>'
  if ($LASTEXITCODE -ne 0) { throw 'cross-service live verification failed' }
}
finally {
  docker stop --time 5 $pgName | Out-Null
}
```

The observed automatic mapping was `127.0.0.1:51653` on the host. Inside the Linux runtime, `LIVE_PG_HOST=host.docker.internal` and `LIVE_PG_PORT=51653` produced the SQLAlchemy admin URL fields. The password was supplied as a URL field rather than interpolated into a URL string, matching SQLAlchemy escaping semantics.

## Exact container evidence script

The single-quoted script passed to `sh -ec` was equivalent to the following formatted commands; formatting and line breaks here do not change the command sequence:

```sh
echo EVIDENCE_START_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo BACKEND_SERVICE_SHA256=$(sha256sum backend/app/services/screenshots.py | cut -d" " -f1)
echo UPLOADER_MANIFEST_AGGREGATE_SHA256=$( \
  { find agent/screenshot_upload tests/upload -type f \
      \( -name "*.py" -o -name requirements.in -o -name requirements.lock \) \
      -print0 | sort -z | xargs -0 sha256sum; sha256sum pyproject.toml; } \
  | sha256sum | cut -d" " -f1 )

mkdir -p /tmp/cross-final/agent /tmp/cross-final/tests/upload /tmp/cross-final/plugin
cp -a agent/screenshot_upload /tmp/cross-final/agent/
cp -a backend /tmp/cross-final/
cp -a tests/upload/. /tmp/cross-final/tests/upload/
cp alembic.ini pyproject.toml /tmp/cross-final/
cp .pytest_cache/upload_external_pg_plugin.py /tmp/cross-final/plugin/
find /tmp/cross-final -type d -name __pycache__ -prune -exec rm -rf {} +
find /tmp/cross-final -type f -name "*.pyc" -delete
echo BYTECODE_FILES_BEFORE_RUN=$(find /tmp/cross-final -type f -name "*.pyc" | wc -l)

python -m venv /tmp/cross-final-venv
/tmp/cross-final-venv/bin/python -m pip install \
  --disable-pip-version-check --quiet --require-hashes \
  -r /tmp/cross-final/agent/screenshot_upload/requirements.lock
/tmp/cross-final-venv/bin/python -m pip check

cd /tmp/cross-final
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/tmp/cross-final:/tmp/cross-final/plugin \
/tmp/cross-final-venv/bin/python -m pytest \
  tests/upload/integration/test_live_response_loss.py \
  --run-live-upload -p upload_external_pg_plugin -vv \
  -p no:cacheprovider --basetemp=/tmp/cross-final-pytest

echo BYTECODE_FILES_AFTER_RUN=$(find /tmp/cross-final -type f -name "*.pyc" | wc -l)
echo EVIDENCE_END_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
```

The host run returned exit code 0. Its preserved interval was `2026-09-24T17:03:52Z` through `2026-09-24T17:04:07Z`, and pytest reported `1 passed in 3.15s`.

## Backend manifest relationship

The original cross-service report preserved `d1799260941c7396c4e3931f21eb07e4857e90f7075d84fba962a1f5b672a0fe`, computed from 75 slash-normalized `relative/path sha256` entries ordered by culture-sensitive PowerShell `Sort-Object` with one final LF. The canonical submitted manifest contains the same 75 path/hash entries but orders them with Python ordinal string sorting. Its SHA-256 is:

`1464c7678cf044f0da996c19cc0174dc31581306e7c011ba98ff1e5d1dc754e5`

Canonical artifacts:

- `.orchestration/reports/BACKEND-UPLOAD-001-rework-source-manifest.txt`: SHA-256 `1464c7678cf044f0da996c19cc0174dc31581306e7c011ba98ff1e5d1dc754e5`;
- `.orchestration/reports/BACKEND-UPLOAD-001-rework-manifest-addendum.md`: SHA-256 `e89185a0c8f036d5bcb3a28f048167cc3bbe1c63ecb076b6dfd20e1ec6aa43c5`;
- `.orchestration/reports/UPLOAD-001-crossservice-final-06-manifest-correction.md`: report-only supplement that applies this correction to the cross-service evidence.

The ordering correction does not indicate source drift and does not change any per-file hash or live-test result.

## Windows launch observation correction

Immediately before the qualifying Linux run on 2026-09-25 KST, these commands were attempted from `C:\Dev\qa-visual-automation`:

```powershell
.\.pytest_cache\agent-clean-win-2\Scripts\python.exe --version
.\.pytest_cache\agent-clean-win-2\Scripts\python.exe -m pip check
.\.pytest_cache\agent-clean-win\Scripts\python.exe --version
.\.venv\Scripts\python.exe --version
python.exe --version
py.exe --version
```

The three venv launchers reported that they were unable to create a process using `C:\Users\dldnj\AppData\Local\Programs\Python\Python312\python.exe`. `python.exe` and `py.exe` were not recognized on PATH. The base interpreter path itself was not checked with `Test-Path` during that observation, so the original report's phrase that it “had been removed” is too strong. The supported statement is limited to: **the existing Windows venvs and PATH Python launch were unavailable in that observed session**. This correction does not revise any earlier Windows result recorded at a different time.

## Boundary

The original cross-service report, product source, checked-in tests, PM state, and contract remain unchanged. No test, service, database, commit, push, or IP check was run for this addendum. The temporary plugin remains deleted. This addendum supplies reproducibility evidence only and does not self-accept any task or acceptance criterion.
