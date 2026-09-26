# FRONTEND-UPLOAD-VERIFY-001 verification report

Date: 2026-09-25 KST. Owner: 04. Requested model/effort: gpt-5.6-sol / medium; actual parent model application was not independently verifiable. Status requested: READY_FOR_REVIEW. This report does not self-accept AC-P2-04 or Phase 2.

## Scope and snapshots

The verification used only synthetic data and disposable resources. It ran the real uploader `Producer` plus `python -m agent.screenshot_upload run`, an isolated PostgreSQL 17 container, migrated Backend, temporary LocalStorage, a production Next.js Web process, and the supported Codex in-app browser. It did not access the user database or real captures, reset a shared service, edit Backend/uploader/Frontend product code, or perform Commit/Push/IP checks.

The first actual Web run is retained unchanged as `.orchestration/reports/FRONTEND-UPLOAD-VERIFY-001-04-evidence.json`, SHA-256 `b4d3910265257043f60267b5393ca409c4a3d8601b4507a365a2aa690adb4620`, generated at `2026-09-24T16:50:40Z`. PM read and hash-verified it. Its Backend source snapshot included:

- `backend/app/services/screenshots.py`: `3c5e36450160f57f732071f8c9bf4eed5684c978e887f499264eee1f50dc7a2b`
- `backend/app/storage/local.py`: `ca93d0dce1418ee0db6b2868fdda5c1328e2cf1958411cb0df2214219f370afc`

Reviewer preflight then required Backend content/hash rework evidence. Owner03 submitted the stable corrected snapshot in `BACKEND-UPLOAD-001-rework-03.md` (SHA-256 `b83e53bbc787020b6c81b0b32b57dff3e8a65d3d49d8152911d70b529edac968`) and handoff (SHA-256 `68335accb905f4efafc0545a2ecce7d7c94a9c5cd41c93dea1c44c7fd8a19c8a`). The raw log hash was independently confirmed as `a31e384c36e8f0caa28f1102496bc3ddf2f8786f3bc27bb0c4f9216622a4d8b1`.

The matching rerun is `.orchestration/reports/FRONTEND-UPLOAD-VERIFY-001-04-corrected-evidence.json`, SHA-256 `8bcd4d64a36239f6d7dacad8b669b816681e4469f91da66f612161b1844ece71`, generated at `2026-09-24T17:03:17Z`. It records:

- Backend source manifest metadata captured during the run: 75 files, case-insensitive Windows-sort aggregate `d1799260941c7396c4e3931f21eb07e4857e90f7075d84fba962a1f5b672a0fe`
- Backend reference image: `sha256:516b9eebabc14f7aba0387966c9e9dd64fc95f462010297c0c9741c7fc3d233d`
- PostgreSQL image: `sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`
- Runtime Backend: the host source snapshot recorded in the evidence, not the reference image

Owner03 then supplied `.orchestration/reports/BACKEND-UPLOAD-001-rework-source-manifest.txt`, whose 75 per-file hashes all match the corrected runtime source. Its canonical ordinal-sort aggregate and file SHA-256 are both `1464c7678cf044f0da996c19cc0174dc31581306e7c011ba98ff1e5d1dc754e5`. The accompanying `.orchestration/reports/BACKEND-UPLOAD-001-rework-manifest-addendum.md` has SHA-256 `e89185a0c8f036d5bcb3a28f048167cc3bbe1c63ecb076b6dfd20e1ec6aa43c5`. It explains that `d179…` used PowerShell culture/case-insensitive ordering over the same 75 files. PM verified every current per-file hash; there was no source drift and no rerun was required.

## Executed flow and results

The corrected run created project/build/locale/category/situation rows with Korean, Japanese and emoji labels. It generated two distinct 320×180 PNG originals with visible synthetic identifiers.

The agent path initialized an isolated spool, published `합성-agent-ようこそ-😀.png` through the real `Producer`, and executed the real uploader CLI. The CLI returned 0. API list and detail were structurally equal for screenshot `fdccd5a6-90b0-43a8-9573-5e09f69c1293` and showed:

- `source: agent`
- non-null `client_upload_id: 6889f7f4-5abb-4969-9003-319dbc49b457`
- `metadata_version: 1`
- the complete nested metadata object containing Korean, Japanese, Arabic, French, emoji, booleans, null, numbers and decomposed `é`
- producer, API and content SHA-256 `c0ba7e61c9eb8033da72341ae2306c7838bb48a938eb60827d9ccdee6b9ebabe`
- byte-for-byte content equality

The database contained one matching `COMPLETED` upload receipt with protocol version 1, matching screenshot ID, null lease and null last error. No second receipt or deduplicated screenshot was inferred.

The separate manual multipart uploaded `수동-원본-保持-😀.png` with nested Unicode metadata. It returned HTTP 201 and a `Location` header. Screenshot `994bbec8-ca7d-401e-b29e-3d89fd2bae99` showed `source: manual`, `client_upload_id: null`, and `metadata_version: 1`. Response hash and content SHA-256 both equaled `b6e1c2593df26b8098d4bc20ea903c14f8626c481557217f69b9d08be16e1748`; downloaded content was byte-for-byte equal to the manual original.

LocalStorage contained exactly two objects and their hashes were exactly the two original hashes. The project had exactly two Screenshot rows.

## Actual browser evidence

The supported Codex in-app browser opened the actual production Web at `http://127.0.0.1:3001` while the disposable API listened on `127.0.0.1:58716`. Browser screenshots and accessibility snapshots were captured in the task transcript.

The list visibly rendered both Unicode filenames, 320×180 dimensions, build/locale/category/situation labels, `manual` and `agent` sources, and two total rows. The agent detail visibly rendered the non-null Client Upload ID, Metadata Version 1, full sorted multilingual nested JSON, and the blue `SYNTHETIC AGENT QA` image. The manual detail visibly rendered Source manual, Metadata Version 1, nested Unicode JSON, and the purple `SYNTHETIC MANUAL QA` image. These were live Backend requests and Blob-rendered images, not mocks, DOM fixtures or static response injection.

## Harness and exact command

`tests/frontend/run_integration.py` gained the bounded `--verify-upload-web` mode. It allocates host-reachable PostgreSQL readiness, a random database/API port, temporary storage and spool, synthetic uploads, API/DB/storage/hash assertions, production Web startup, evidence JSON, a stop-file controlled shutdown, and cleanup recording. The fixed Web port 3001 is required by the existing Backend CORS contract; PostgreSQL, database, API, storage and spool are disposable.

The project `.venv` launcher pointed to an unavailable interpreter. The bundled Python interpreter was therefore used with existing project site-packages and a verification-only temporary `rfc8785==0.1.4` target. The executed verification command was:

```powershell
$site = (Resolve-Path '.\.venv\Lib\site-packages').Path
$extra = (Resolve-Path '.\.pytest_cache\frontend-upload-verify-deps').Path
$env:PYTHONPATH = "$extra;$site"
& 'C:\Users\dldnj\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  tests\frontend\run_integration.py --isolated-postgres --verify-upload-web
```

The first attempt stopped before resource creation because `rfc8785` was absent. A second attempt exposed the old container-local readiness race; the harness now probes the published host port and emits container logs on failure. The subsequent preliminary and corrected runs passed. No failed attempt was reported as product behavior.

The corrected run necessarily built the production Web after allocating the random API port so `NEXT_PUBLIC_API_BASE_URL` was embedded correctly. Build and TypeScript checks completed successfully. Existing 26 Frontend unit tests and the full Backend suite were not redundantly rerun; owner evidence remains 26/26 and Backend corrected owner evidence remains targeted 29 and final 119.

## Cleanup and limits

The stop-file path let the corrected run exit through normal cleanup. API stopped, database dropped, PostgreSQL container removed, temporary storage/spool disappeared, and no listener remained on ports 3001 or 58716. The Next process reports Windows termination exit 1 after the requested browser-evidence stop; its startup/build and browser requests had already succeeded.

Browser screenshots are retained in the supported browser tool transcript rather than as repository binary files. Exact IDs, metadata and hashes are retained in the corrected JSON artifact. The Backend per-file manifest gate is resolved. Independent review still owns acceptance; this submission does not mark AC-P2-04 PASS.
