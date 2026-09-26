# BACKEND-UPLOAD-001 evidence addendum

Date: 2026-09-25 KST. This addendum supplements, and does not rewrite, `BACKEND-UPLOAD-001-03.md`. It adds executable environment detail and corrects the Windows evidence classification. No product file was changed and no test was rerun for this addendum.

## Executed disposable-database path

The executed Linux run used the repository's already-created, isolated PostgreSQL 17 test container on Docker network `qa-visual-automation_default`. The container was stopped before this task, started only for verification, and stopped again afterward:

```powershell
docker start qa-visual-automation-postgres-1
docker build --pull=false -f backend/Dockerfile.test -t qa-backend-upload-final:local .
docker run --rm `
  --network qa-visual-automation_default `
  -e PYTHONDONTWRITEBYTECODE=1 `
  -e POSTGRES_DB=qa_visual `
  -e POSTGRES_USER=qa_visual `
  -e POSTGRES_PASSWORD `
  -e DATABASE_HOST=postgres `
  -e DATABASE_PORT=5432 `
  qa-backend-upload-final:local `
  python -m pytest tests/backend -q -p no:cacheprovider --tb=short
docker stop qa-visual-automation-postgres-1
```

`POSTGRES_PASSWORD` above is deliberately shown as Docker environment pass-through. The executed credential was the existing synthetic container credential; its value is not evidence and is not recorded in this artifact. No production/user credential was used.

`tests/backend/conftest.py::database` is the disposal boundary. It connects only to the isolated server's administrative `postgres` database, creates a random database named `qa_backend_test_<uuid>`, runs Alembic to `head`, yields that engine to the suite, then executes `DROP DATABASE <name> WITH (FORCE)` in `finally`. Migration-specific tests independently create random `qa_migration_test_<uuid>` and `qa_migration_preservation_<uuid>` databases and drop them in `finally`. The existing `qa_visual` application database is only a settings source; product rows are never reset or used by the fixtures.

The final captured command output is preserved verbatim in `BACKEND-UPLOAD-001-linux-final.txt`. It records `94 passed, 2 warnings in 4.10s`. The two warnings are third-party Starlette/httpx deprecation warnings. The Docker build completed the hash-locked install, project wheel installation and `pip check` with `No broken requirements found`.

## Standalone equivalent setup

The following equivalent creates a wholly temporary PostgreSQL container with only synthetic values. It is provided for reviewer reproduction and was not separately rerun for this addendum:

```powershell
docker network create qa-backend-upload-review
docker run -d --name qa-backend-upload-review-pg `
  --network qa-backend-upload-review `
  -e POSTGRES_DB=qa_upload_review `
  -e POSTGRES_USER=qa_upload_review `
  -e POSTGRES_PASSWORD=qa_upload_review_ephemeral `
  postgres:17-alpine
docker build --pull=false -f backend/Dockerfile.test -t qa-backend-upload-final:local .
docker run --rm `
  --network qa-backend-upload-review `
  -e PYTHONDONTWRITEBYTECODE=1 `
  -e POSTGRES_DB=qa_upload_review `
  -e POSTGRES_USER=qa_upload_review `
  -e POSTGRES_PASSWORD=qa_upload_review_ephemeral `
  -e DATABASE_HOST=qa-backend-upload-review-pg `
  -e DATABASE_PORT=5432 `
  qa-backend-upload-final:local `
  python -m pytest tests/backend -q -p no:cacheprovider --tb=short
docker rm -f qa-backend-upload-review-pg
docker network rm qa-backend-upload-review
```

## Windows evidence correction

The owner report's phrase that the local venv points to a missing interpreter is not supported by a preserved failure command/output from this final execution. It must not be used as evidence of a missing interpreter. The accurate final classification is:

> Native Windows Backend execution environment was not established for the final suite; native Windows full-suite verification is NOT_RUN.

The bundled Windows Python was used only for no-bytecode AST parsing. Earlier restricted-launcher or filesystem permission failures do not prove that a Python interpreter is missing. This correction supersedes only that evidence statement; it does not change the Linux result or claim Windows PASS.

Receipt/migration work was delegated with requested Terra/high, but requested/actual model attribution is not acceptance evidence and actual application remains unverified. Independent review should apply high-difficulty scrutiny to concurrency, fencing and additive data preservation regardless of that delegation label.

