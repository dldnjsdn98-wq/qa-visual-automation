# BACKEND-UPLOAD-001 rework report

Date: 2026-09-25 KST. Contract: P2-UPLOAD-v1 revision 2. Input: `REVIEW-UPLOAD-001-preflight-08.md`, SHA-256 `df50c3b749876a0ad5b310b09c0c2a9e72c3d05a649b3eb458331df1d8e2a6f1`. Status requested: READY_FOR_REVIEW after CHANGES_REQUESTED rework.

This report preserves the original Backend report, addendum, log and handoff. It addresses only R08-P2-PREFLIGHT-001/002/003 under the existing Backend ownership. No historical migration, uploader, Frontend, PM state, contract, README, root integration, commit, push or IP check was changed.

## Finding closure

### R08-P2-PREFLIGHT-001 — fixed and executed

`backend/app/services/screenshots.py::read_content` now reads the bytes that will be returned from one open storage handle and checks both exact length and SHA-256 against `Screenshot.file_hash`. It does not verify one handle and reopen another. A missing, truncated, extended or same-length substituted object returns `503 STORAGE_UNAVAILABLE`; the Screenshot, UploadReceipt and existing object remain unchanged.

The parameterized HTTP regression covers normal, missing, length-changed and same-length-changed objects. Targeted owner slice result: 4 passed. Integrated targeted and full-suite results are below.

### R08-P2-PREFLIGHT-002 — real PostgreSQL evidence added

No reconcile product-code change was required. `tests/backend/test_reconcile_upload_receipts.py` now drives `reconcile(...)` with real PostgreSQL UploadReceipt rows and independent sessions. It covers:

- live and expired PROCESSING candidate protection plus Screenshot protection;
- dry-run no mutation;
- apply-mode durable PROCESSING→FAILED commit before deletion;
- failed commit rollback and fault after FAILED commit with object retention;
- post-transition fresh database inventory;
- fresh Screenshot or PROCESSING reference at the deletion barrier;
- exact object/staging `>24h` eligibility, with equality and younger items retained;
- incomplete inventory, DB, storage and all fault-seam failures stopping deletion;
- advisory maintenance lock and writers-stopped assertion.

The dedicated real PostgreSQL run was 24 passed. The integrated targeted selection was 29 passed and the final suite was 119 passed.

### R08-P2-PREFLIGHT-003 — populated preservation evidence expanded

The existing additive `0003_phase2_upload_receipts` migration was not modified. The populated `0002→0003` test now seeds a real Screenshot with a fixed timezone-aware `uploaded_at`, all relationship IDs and image facts, decomposed Unicode filename, non-empty nested CJK/emoji/combining/empty/null JSONB metadata, actual SHA-256/storage key, and actual PNG original bytes in LocalStorage. It snapshots every Screenshot column and the exact object bytes before upgrade, upgrades to `0003`, compares the complete row and bytes afterward, confirms zero synthetic receipts, and retains model/Alembic parity coverage.

The first integrated targeted run exposed a test-only SQLAlchemy mapping key error (`KeyError: capture_metadata`): 28 passed, 1 failed. The column was explicitly labeled `capture_metadata`; rerunning the identical selection produced 29 passed. The failure and correction are preserved in `BACKEND-UPLOAD-001-rework-linux.txt`.

## Final executable evidence

Environment: Docker Desktop Linux, Python 3.12 base image, PostgreSQL 17.11 isolated test container. Commands used `.env` via Docker `--env-file`; no credential value is recorded. `tests/backend/conftest.py` creates random `qa_backend_test_<uuid>` databases and force-drops them in `finally`; migration tests use their own random databases and also force-drop them.

Targeted command:

```powershell
docker run --rm --network qa-visual-automation_default --env-file .env `
  -e PYTHONDONTWRITEBYTECODE=1 -e DATABASE_HOST=postgres -e DATABASE_PORT=5432 `
  -v "C:\Dev\qa-visual-automation:/app" -w /app qa-backend-upload-final:local `
  python -m pytest `
    tests/backend/test_screenshots.py::test_content_read_verifies_returned_bytes_and_preserves_state `
    tests/backend/test_reconcile_upload_receipts.py `
    tests/backend/test_migrations_storage.py::test_0002_data_is_preserved_by_additive_0003_migration `
    -q -p no:cacheprovider --tb=short
```

Final image and suite:

```powershell
docker build --pull=false -f backend/Dockerfile.test -t qa-backend-upload-rework:local .
docker run --rm --network qa-visual-automation_default --env-file .env `
  -e PYTHONDONTWRITEBYTECODE=1 -e DATABASE_HOST=postgres -e DATABASE_PORT=5432 `
  qa-backend-upload-rework:local `
  python -m pytest tests/backend -q -p no:cacheprovider --tb=short
```

Results:

- corrected targeted selection: **29 passed, 2 warnings in 2.54s**;
- mounted integration suite before image rebuild: **119 passed, 2 warnings in 6.60s**;
- hash-locked image build, project wheel install and `pip check`: **PASS** (`No broken requirements found`);
- final unmounted image suite: **119 passed, 2 warnings in 5.64s**;
- AST parse: **65 Python files OK**;
- `git diff --check -- backend tests/backend`: **PASS**; line-ending notices only.

The two warnings are existing third-party Starlette/httpx and anyio deprecations.

## Final hashes

Sorted UTF-8 manifest of `rg --files backend tests/backend` plus `pyproject.toml`, lines formatted `relative/path sha256` with one final LF: 75 files, aggregate SHA-256 `d1799260941c7396c4e3931f21eb07e4857e90f7075d84fba962a1f5b672a0fe`.

| Artifact | SHA-256 |
| --- | --- |
| `backend/app/services/screenshots.py` | `3c5e36450160f57f732071f8c9bf4eed5684c978e887f499264eee1f50dc7a2b` |
| `backend/app/storage/local.py` | `ca93d0dce1418ee0db6b2868fdda5c1328e2cf1958411cb0df2214219f370afc` |
| `backend/app/maintenance/reconcile_storage.py` | `db7a44c79f039cdc3d54d1e47cfdd34b7a439ff0187b4386acd0d0df651cb059` |
| `tests/backend/test_screenshots.py` | `cc59cefb41b372e51608ea1afc1cec8af69f9a7e3fb0b8773922604b2aca68d2` |
| `tests/backend/test_reconcile_upload_receipts.py` | `692b5bf25ac92da50e60df8a2a52c26ad4ce021eff775fc7ab059301409c3bc2` |
| `tests/backend/test_migrations_storage.py` | `e7b122e0045c16d6015d8819bd488e8460df85b3cbfa4cdc9650f91e283c8bda` |
| `backend/migrations/versions/0003_phase2_upload_receipts.py` | `b882b7eb714ba4b79995b73bfef9e3940108fcda23eb9dbaa05243da121cd228` |

Final image ID and repo digest: `sha256:516b9eebabc14f7aba0387966c9e9dd64fc95f462010297c0c9741c7fc3d233d`.

## Delegation and disposition

- R08-001: requested Sol/high; actual model unverified.
- R08-002: requested Astra/medium due F14 recovery complexity; actual model unverified.
- R08-003: requested Sol/high agent did not produce a patch and was shut down; the parent implemented and executed this slice. No result is attributed to that agent.

Branch/commit: `null` / `null`. User database access: none. This is an owner READY_FOR_REVIEW request, not self-acceptance or a Phase 2 AC promotion. Reviewer should independently verify the final hashes and risk-selected behavior.

