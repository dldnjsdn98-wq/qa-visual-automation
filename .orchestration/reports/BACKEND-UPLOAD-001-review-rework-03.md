# BACKEND-UPLOAD-001 review rework / Owner 03

Date: 2026-09-25 KST  
Disposition: READY_FOR_REVIEW owner submission; independent Reviewer08 closure pending  
Formal input: `.orchestration/reports/REVIEW-UPLOAD-001-08.md` SHA-256 `1da2d73e837d62bc4b9926f41b168a56d12bc64bd9ab8c56001640d7c234bab8`  
Formal handoff: `.orchestration/handoffs/REVIEW-UPLOAD-001-08.md` SHA-256 `f182ffe3eb83b7ae193bb7c5efdca4d852c950108bce0822d11fff919dee13cf`

## Scope and result

This correction addresses only Owner03 findings `R08-P2-REVIEW-005` and `R08-P2-REVIEW-009`. Existing Phase 2 Backend behavior, old evidence, PM state, contract, Frontend, uploader, migrations and unrelated dirty files were preserved.

- `005` corrected: `BoundaryMiddleware` now admits at most four concurrent whole-body requests per application process before allocating the request `bytearray`. The permit is retained until downstream response completion because the replay closure and parser/decoder copies retain or duplicate the body. A fifth request is rejected before calling `receive` with `503 REQUEST_OVERLOADED` and `Retry-After: 1`. Completion, disconnect/cancellation and downstream error all release the permit.
- `009` corrected: finalize revalidation takes PostgreSQL `FOR KEY SHARE` locks on Project, Build, Locale, Category and Situation and retains them through Screenshot insertion and receipt completion. Existing callers of `catalog.get(lock=True)` retain `FOR UPDATE`; the first full-suite run caught and caused correction of an accidental lock-mode regression.
- A new fault seam, `AFTER_FINAL_REFERENCES_BEFORE_SCREENSHOT_INSERT`, makes the reference-read/insert boundary deterministic without adding external work to the transaction.
- Actual two-connection PostgreSQL tests prove that a concurrent parent delete waits on the key-share lock and fails after successful finalize because the committed Screenshot retains the parent. They also prove that a delete committed before finalization returns the existing `404 RESOURCE_NOT_FOUND`, writes no Screenshot, and changes only the same owned generation to fenced `FAILED` after confirmed rollback.
- Receipt transaction `lock_timeout = 5s`, `statement_timeout = 10s` and PostgreSQL 17 transaction bound remain unchanged.

## Changed source and test files

| File | SHA-256 |
| --- | --- |
| `backend/app/api/middleware.py` | `de84a870057dac81eed439cb7dbfdadeef28a798f35da3d2256b2777d6179aa9` |
| `backend/app/repositories/catalog.py` | `95ccacb7cba3b976bdba83233c55b4c213c4c4118ec671a59d306afa87ca6011` |
| `backend/app/services/catalog.py` | `6e207a6734c0647fea2adb77ade4f16aca2ed22d01e1b87cb1adb782fc7a775e` |
| `backend/app/services/upload_receipts.py` | `6b6e630be692230f7c3d0b9a7cd4a24638b26a930707f19473318daa7540ff66` |
| `tests/backend/test_request_concurrency.py` | `d1a5c2890d6b3afd3f30437692ac2510605969fc25204c2f075ba8acff8b6f2e` |
| `tests/backend/test_finalize_reference_lock.py` | `247c350dfd30d25648711547c46fd29c4ba804a8a06cb1914b7dd474c30c1685` |

Current source manifest: `.orchestration/reports/BACKEND-UPLOAD-001-review-rework-source-manifest.txt`. It contains 77 ordinal-sorted, slash-normalized entries for `backend`, `tests/backend` and `pyproject.toml`, with one final LF. Every entry was rehashed against current source. Manifest/file aggregate SHA-256: `a8b5225bceb106cc3e09883eb3e68c2a28d659f8c0ee9ec65eb6974ffa7696a0`. This supersedes the previous 75-file Backend aggregate for this corrected submission; prior manifests remain historical evidence.

## Fresh execution evidence

Environment:

- Host test runner: bundled CPython 3.12.14 with the existing isolated `agent-clean-win` site-packages.
- Database: fresh disposable `postgres:17-alpine`, PostgreSQL `17.11`, `pg_is_in_recovery() = false`, host port 55439.
- Linux image: `qa-backend-review-rework-03:local`, image ID `sha256:f5d00d7ef450f7150f87794061991ffea1d25bcea6ef7dce9ef67ea40072669b`.
- Dockerfile.test hash-lock dependency installation was cached from the unchanged lock. The current source wheel was rebuilt and `pip check` returned `No broken requirements found.`

Fresh commands and results:

1. New ASGI and PostgreSQL corrections:

   `$env:PYTHONPATH=(Resolve-Path '.pytest_cache\agent-clean-win\Lib\site-packages').Path; $env:POSTGRES_DB='qa_backend_rework'; $env:POSTGRES_USER='qa_backend_rework'; $env:POSTGRES_PASSWORD='qa_backend_rework'; $env:DATABASE_HOST='127.0.0.1'; $env:DATABASE_PORT='55439'; & 'C:\Users\dldnj\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m pytest tests/backend/test_request_concurrency.py tests/backend/test_finalize_reference_lock.py -q -p no:cacheprovider --basetemp=.orchestration/reports/backend-review-rework-03-targeted-tmp`

   Result: `7 passed, 1 warning in 0.58s` against the disposable PostgreSQL primary.

2. Reviewer risk set for prior `001..004` evidence and response contracts:

   `$env:PYTHONPATH=(Resolve-Path '.pytest_cache\agent-clean-win\Lib\site-packages').Path; $env:POSTGRES_DB='qa_backend_rework'; $env:POSTGRES_USER='qa_backend_rework'; $env:POSTGRES_PASSWORD='qa_backend_rework'; $env:DATABASE_HOST='127.0.0.1'; $env:DATABASE_PORT='55439'; & 'C:\Users\dldnj\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m pytest tests/backend/test_screenshots.py::test_content_read_verifies_returned_bytes_and_preserves_state tests/backend/test_reconcile_upload_receipts.py tests/backend/test_migrations_storage.py::test_0002_data_is_preserved_by_additive_0003_migration tests/backend/test_upload_receipt_constraints.py tests/backend/test_upload_response_contract.py -q -p no:cacheprovider --basetemp=.orchestration/reports/backend-review-rework-03-risk-tmp`

   Result: `38 passed, 1 warning in 3.43s`. This is fresh owner evidence and does not independently close Reviewer-owned findings.

3. Focused regression after restoring existing `FOR UPDATE` semantics:

   `$env:PYTHONPATH=(Resolve-Path '.pytest_cache\agent-clean-win\Lib\site-packages').Path; $env:POSTGRES_DB='qa_backend_rework'; $env:POSTGRES_USER='qa_backend_rework'; $env:POSTGRES_PASSWORD='qa_backend_rework'; $env:DATABASE_HOST='127.0.0.1'; $env:DATABASE_PORT='55439'; & 'C:\Users\dldnj\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m pytest tests/backend/test_concurrency_contract.py::test_concurrent_expected_replacements_are_atomic tests/backend/test_request_concurrency.py tests/backend/test_finalize_reference_lock.py -q -p no:cacheprovider --basetemp=.orchestration/reports/backend-review-rework-03-regression-tmp`

   Result: `8 passed, 1 warning in 0.55s`.

4. Final host Backend suite:

   `$env:PYTHONPATH=(Resolve-Path '.pytest_cache\agent-clean-win\Lib\site-packages').Path; $env:POSTGRES_DB='qa_backend_rework'; $env:POSTGRES_USER='qa_backend_rework'; $env:POSTGRES_PASSWORD='qa_backend_rework'; $env:DATABASE_HOST='127.0.0.1'; $env:DATABASE_PORT='55439'; & 'C:\Users\dldnj\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m pytest tests/backend -q -p no:cacheprovider --basetemp=.orchestration/reports/backend-review-rework-03-full-final-tmp --junitxml=.orchestration/reports/BACKEND-UPLOAD-001-review-rework-03.xml`

   Result: `126 passed, 1 warning in 7.66s`.

5. Final clean Linux/hash-lock image suite:

   `docker build --pull=false --tag qa-backend-review-rework-03:local --file backend/Dockerfile.test .`

   Build result: PASS; current project wheel built, installed and `pip check` returned `No broken requirements found.`

   `docker run --rm --name qa-backend-review-rework-03-test -e POSTGRES_DB=qa_backend_rework -e POSTGRES_USER=qa_backend_rework -e POSTGRES_PASSWORD=qa_backend_rework -e DATABASE_HOST=host.docker.internal -e DATABASE_PORT=55439 -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONHASHSEED=0 qa-backend-review-rework-03:local python -m pytest tests/backend -q -p no:cacheprovider --basetemp=/tmp/backend-review-rework-03`

   Result: `126 passed, 2 warnings in 9.01s`.

6. Static checks:

   - AST parse: `67` Python files PASS.
   - `git diff --check -- backend tests/backend`: exit 0; only existing line-ending notices.
   - Manifest verification: 77 entries, ordinal order, current hashes, final LF PASS.

Evidence hashes:

| Artifact | SHA-256 |
| --- | --- |
| `.orchestration/reports/BACKEND-UPLOAD-001-review-rework-03-tests.txt` | `b8889bdf6cca7a1823954b5fa5c516ede226b0e096e24a64b4b4f352cec9b16c` |
| `.orchestration/reports/BACKEND-UPLOAD-001-review-rework-03.xml` | `187ffcedf6992100d0c217da26201c4636be535c0203b8653aff5135bc17aadb` |
| `.orchestration/reports/BACKEND-UPLOAD-001-review-rework-03-linux.txt` | `3965fe3c1b314a81d3ffe7467fd90d9b7dd3d51279f89a1a620a4edcb44e9f91` |

## Preserved failures and corrections

- The original isolated venv launcher later returned exit 1 because its base interpreter path was unavailable. No test started. The bundled CPython 3.12.14 plus the same isolated site-packages was used instead.
- The first Backend full-suite run returned `1 failed, 125 passed`: `test_concurrent_expected_replacements_are_atomic` exposed that the first implementation changed shared `catalog.get(lock=True)` from `FOR UPDATE` to `FOR KEY SHARE`. The shared behavior was restored and a separate `key_share=True` mode was added only for finalize reference stability. Failure evidence remains in `BACKEND-UPLOAD-001-review-rework-03-full-failed.txt` (`09d8e57691f2791b5d51028f8f3bc30258b97e23bb9a1ce13a47bdf0ef5cbb0d`) and `.xml` (`a2e52f3af59b93b4fd54a10b257cc84a7393627286ed610c5c826eff45a5768d`).
- The first sandboxed Linux `docker run` was denied before container creation. Its output is preserved in `BACKEND-UPLOAD-001-review-rework-03-linux-sandbox-blocked.txt` (`5d772fd41bc943de1c8da1ba6e72196573ebb8df127eb019f9843eedfc2fe07a`). The approved rerun produced the successful Linux result above.
- The first current-manifest write reported a PowerShell sort type failure and its aggregate was discarded. The file was rewritten with `[string[]]` plus `StringComparer.Ordinal`, then every entry/order/final LF was verified. Only `a8b522...` is canonical.

## Cleanup, attribution and remaining gate

The tests created only uniquely named synthetic databases in the fresh container; the final query returned no `qa_backend_test_%` databases. The disposable PostgreSQL container was stopped and removed, and no user/shared database or service was reset. No commit, push, deployment, account/security change, IP check, Frontend/uploader/contract/PM-state edit or historical migration edit occurred.

Subagent routing was requested exactly as assigned: `005` Sol/high, `009` Astra/medium, evidence Sol/medium and submission hygiene Terra/high. The multi-agent management API returned `not_found` for all four newly issued IDs before any result or file change was observed. Their actual models and execution are therefore unverified, and all final implementation, integration and test claims above are parent-executed.

Owner03 considers `005` and `009` corrected and submits this snapshot for independent review. `R08-P2-PREFLIGHT-001..003`, `R08-P2-REVIEW-004`, Phase 2 acceptance and final finding closure remain solely Reviewer08/PM decisions and are not marked closed here.
