# FRONTEND-UPLOAD-VERIFY-001 review rework verification report

Date: 2026-09-25 KST. Owner: 04. Requested disposition: `READY_FOR_REVIEW`. This is owner evidence for `R08-P2-REVIEW-008`; independent Reviewer08 still owns finding closure and AC-P2-04.

## Exact inputs and scope

The run used the corrected Backend03 and Uploader06 owner snapshots only after both were stable and PM-matched:

- Backend report `.orchestration/reports/BACKEND-UPLOAD-001-review-rework-03.md`: SHA-256 `095d641be32bce1d0c66672c875a34493c96555acca604a53c21ad96dfafa0a4`
- Backend handoff `.orchestration/handoffs/BACKEND-UPLOAD-001-review-rework-03.md`: SHA-256 `1881739c037e5f0dfdc191807ff7dbef10b81f4e295b6bf8d4ac2efd0cdad322`
- Backend 77-file current manifest: `a8b5225bceb106cc3e09883eb3e68c2a28d659f8c0ee9ec65eb6974ffa7696a0`; all 77 entries were independently rehashed against current files with zero mismatches
- Uploader report `.orchestration/reports/UPLOAD-001-review-rework-06.md`: SHA-256 `6658de2c47c8ca4050db535ac19f5ee5e296a69d96a281b74a32301030054483`
- Uploader handoff `.orchestration/handoffs/UPLOAD-001-review-rework-06.md`: SHA-256 `e85302871e857e8ece42b33c80bd0d2ef802b5ea0e49ffe624af24f69cd9c9b9`
- Uploader 35-file current manifest: `eefafa7ce16a82b8f30613612968b6acb74b3ba09f3f2f2788547a7937b9c934`; all 35 entries were independently rehashed against current files with zero mismatches

The exact executed harness was `tests/frontend/run_integration.py`, SHA-256 `3d4952eb33bf6c4c928563a128d7b6fa7d19305ce4005096fdce61fbbe69ee1c`. The evidence records the same hash. The unchanged contract test hash was `a30e873a2ee7f6b3163a048efa5407cbb183ab695cfb1164c990fbb93ca2373c`.

The run used synthetic data, a disposable PostgreSQL 17 container and random database, temporary Backend storage and uploader spool, the actual Backend application, the actual uploader `Producer` and CLI, and a production Next.js build. It did not access user data, reset a shared service, change settings, push, deploy, or perform an IP connectivity check.

## Command and environment

The project `.venv` launcher remained unavailable, so the same bundled CPython 3.12 runtime was used with existing project site-packages and the previously prepared verification-only `rfc8785` target:

```powershell
$site = (Resolve-Path '.\.venv\Lib\site-packages').Path
$extra = (Resolve-Path '.\.pytest_cache\frontend-upload-verify-deps').Path
$env:PYTHONPATH = "$extra;$site"
& 'C:\Users\dldnj\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  tests\frontend\run_integration.py --isolated-postgres --verify-upload-web
```

Runtime facts recorded in the evidence:

- generated at `2026-09-25T01:21:25Z`
- disposable API `127.0.0.1:64348`; production Web `127.0.0.1:3001`
- PostgreSQL image `sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`
- Backend reference image `sha256:516b9eebabc14f7aba0387966c9e9dd64fc95f462010297c0c9741c7fc3d233d`; runtime Backend was the host source snapshot recorded in the JSON
- production build and TypeScript returned 0; uploader CLI returned 0

## Upload, metadata, byte and database results

One real `agent` intent and one real `automation` intent were published through the actual `Producer`, then processed together by one actual uploader CLI run. A third screenshot used a separate manual multipart request.

| Source | Screenshot ID | Client upload ID | Original/API/content SHA-256 | Exact bytes |
| --- | --- | --- | --- | --- |
| agent | `3cc36013-d6f7-4f38-815e-608d45dd3727` | `b1009ef1-0f1e-478c-8204-101c763fc1dd` | `c0ba7e61c9eb8033da72341ae2306c7838bb48a938eb60827d9ccdee6b9ebabe` | true |
| automation | `c965f6ab-e7af-404c-b550-4da59b362ebb` | `8788f205-c4d1-4c72-9aa6-d547d21c72dc` | `05d10110228783975c227600872595410b4e27c4891b7467b6dd02fc819e320e` | true |
| manual | `1d17554f-ed83-41a3-92cc-a1f0ffabd172` | null | `b6e1c2593df26b8098d4bc20ea903c14f8626c481557217f69b9d08be16e1748` | true |

For agent and automation, the producer hash, API `file_hash`, downloaded content hash and original bytes all matched. The manual multipart returned HTTP 201 with a screenshot `Location`; its API/content hash and bytes also matched. List and detail objects matched for all three.

All three metadata objects retained an empty string and nested multilingual Unicode. The automation object specifically retained top-level `empty_string: ""`, nested Korean `빈문자열: ""`, Japanese `空文字列: ""`, nested emoji object `empty: ""`, and `screen_state: ""`, together with Korean, Japanese, Arabic and emoji values. The manual object retained Unicode, decomposed `é`, null, boolean, emoji and nested empty string values.

The database contained exactly three Screenshot rows and two `COMPLETED` uploader receipts, one for agent and one for automation. Both receipts had protocol version 1, matching screenshot IDs, null leases and null errors. Temporary LocalStorage contained exactly three objects whose hashes were the three expected original hashes.

## Actual production Web evidence

The supported Codex in-app browser opened the live production Web while the disposable services were running. Accessibility snapshots and visible browser screenshots in the task transcript established:

- list page: exactly three rows, with the manual, agent and automation Unicode filenames, 320×180 dimensions, shared build/locale/category/situation labels and the correct three source values
- agent detail: non-null Client Upload ID, Metadata Version 1, full nested multilingual metadata including `empty_string: ""`, and the rendered blue `SYNTHETIC AGENT QA` original
- automation detail: non-null Client Upload ID, Metadata Version 1, every top-level and nested empty string, Korean/Japanese/Arabic/emoji metadata, and the rendered green `SYNTHETIC AUTOMATION QA` original
- manual detail: source `manual`, no Client Upload ID field, Metadata Version 1, nested Unicode/empty-string metadata, and the rendered purple `SYNTHETIC MANUAL QA` original

These views used the production UI and live Backend content endpoints. No mock, DOM fixture or static response injection was used. Browser screenshots remain in the supported browser transcript; exact IDs, metadata and hashes are in the JSON artifact.

## Artifacts and cleanup

- evidence JSON: `.orchestration/reports/FRONTEND-UPLOAD-VERIFY-001-review-rework-04-evidence.json`, SHA-256 `20381330b485f0617b2933eeb2e16068e59ce66035e81fa64ab4c8f1d15563dd`
- production Web log: `.orchestration/reports/FRONTEND-UPLOAD-VERIFY-001-review-rework-04-evidence.web.log`, SHA-256 `f25fb855e2a93338665dc4942cd76d00f0448ef6428ca7166c436d6978b31577`

The stop-file path returned the harness through normal cleanup. The JSON records Web terminated after the requested stop, API stopped, random database dropped and PostgreSQL container removed. Independent post-cleanup checks found no listeners on ports 3001 or 64348 and zero `qa-frontend-test-*` containers. The Web process reports termination exit 1 on Windows after the requested stop; its build, startup and all browser requests had already succeeded.

Python AST parsing and scoped `git diff --check` passed before execution; scoped `git diff --check` passed again after execution. Existing broad Frontend and Backend suites were not repeated by Owner04. Backend03 and Uploader06 owner-suite results remain attributed to their reports. Independent review remains pending.
