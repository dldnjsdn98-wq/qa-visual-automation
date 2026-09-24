# Phase 1 QA Frontend

Existing Next.js App Router + TypeScript application. No later-phase OCR/automation UI.

## Run

From `frontend/`, with Node.js LTS and npm on PATH:

```powershell
npm.cmd ci
npm.cmd run dev
```

Open `http://127.0.0.1:3001`. Backend defaults to `http://127.0.0.1:8001`.
Set `NEXT_PUBLIC_API_BASE_URL` in a local `frontend/.env.local` before dev/build if the API origin differs. Next.js embeds this public setting at build time; rebuild when it changes. Docker builds accept the same build argument. No credentials belong in this public setting.

## Navigation and workflow

Screens use bookmarkable hash routes on the Next.js root page: `#/dashboard`, `#/projects`, `#/builds`, `#/locales`, `#/categories`, `#/situations`, `#/strings`, `#/upload`, `#/screenshots`, `#/detail`. Project and review filters are stored in the hash query, so refresh/back retain the context. Project changes clear dependent selections. Filter changes reset pagination and in-progress forms to the new scope.

Create Project, Build, Locale, Category and Situation. In Strings → String Keys, register stable String IDs. In Translations, register Build/Locale-specific text. In Expected 설정, choose Build/Situation, then replace the ordered String ID mapping; choose Locale for resolved preview. A Situation filter shows its expected translations, including missing entries that can be added directly.

Upload one original PNG/JPEG with Build/Locale/Category/Situation selected. Detail shows original content and current-catalog Expected Strings. Empty translations are distinct from missing translations. An ambiguous upload error requires checking the list before manual retry; uploads never retry automatically.

Collections have 50-row pages. Local text search is explicitly limited to the current page; Strings also supports exact String ID filtering across all pages. Situation-resolved search covers its complete mapping (up to 1,000 IDs). Metadata selectors load paginated lookup catalogs; very large metadata catalogs may require a future searchable server-backed selector. Full-text server search is outside the approved API.

## Verification

```powershell
npm.cmd test
npm.cmd run typecheck
npm.cmd run build
```

From project root, with Backend dependencies installed in `.venv` and Docker available:

```powershell
.\.venv\Scripts\python.exe tests/frontend/run_integration.py --isolated-postgres
```

This runs the real TypeScript client against the real FastAPI app, generated OpenAPI, PostgreSQL migrations and temporary local image storage. It creates and removes its own uniquely named PostgreSQL container/database. Existing user databases, credentials and storage are unchanged. Without `--isolated-postgres`, the runner uses configured PostgreSQL credentials but still allocates a separate database.

Add `--serve` for temporary browser QA on port 8001; stop with Ctrl+C to clean up. Unit/component tests use synthetic mocks; real integration tests are separately reported. A passing Frontend suite is not Backend acceptance or Phase 1 acceptance.
