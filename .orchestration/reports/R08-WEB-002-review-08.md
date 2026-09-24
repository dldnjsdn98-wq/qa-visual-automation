# R08-WEB-002 — Independent correction review / 08

Date: 2026-09-12 KST. Repository: `C:\Dev\qa-visual-automation`.

## Disposition

**CODE/TARGETED REGRESSION PASS; CLOSURE CONDITIONAL. R08-WEB-002 remains OPEN, MAJOR pending parent preservation and configured restart/readback evidence.** No additional blocking code finding was established in this bounded correction review. This report does not accept Backend or Phase 1 as a whole.

Read [REVIEW-WEB-001-backend-08.md](REVIEW-WEB-001-backend-08.md). Terra's implementation attribution comes from the assignment; code inspection and the test executions below were performed independently by this correction reviewer. Parent owns preservation of the exact legacy original and configured API restart/readback. No parent runtime result is certified here.

## Code and test evidence

- `backend/app/storage/local.py:11` changes `parents[4]` to `parents[3]`; the inspected Git diff for this file contains only that correction. For this checkout, index 3 is `C:\Dev\qa-visual-automation`, whereas index 4 is `C:\Dev`. Line 18 retains `Path(os.path.abspath(ROOT / root))`: relative roots now anchor to the repository independently of process working directory, while an absolute root retains its override behavior. Component/reparse checks and directory creation remain at lines 19–20.
- `tests/backend/test_storage_root.py:7–18` derives the expected repository root from the test file, changes to an unrelated temporary working directory, suppresses `Path.mkdir`, and asserts the actual module root, default `storage/local` destination and absolute override. The previous `parents[4]` value contradicts its root/default assertions, so this is a meaningful regression. That failure against old code is a source-level conclusion, not a separately executed mutation test.
- Default configuration remains `storage/local` (`backend/app/config.py:14`, `.env.example:6`, `backend/README.md:24`). Compose explicitly sets `/app/storage/local` and binds `./storage/local:/app/storage/local` (`docker-compose.yml:27,31`). The corrected host destination matches that host bind directory. This is configuration/source agreement, not an executed container transition.
- The test executes constructor resolution from one non-repository working directory, with module import occurring before that change. It does not prove object publication, preservation, API configuration, restart durability or Linux behavior. The absolute source-derived ROOT also supports repository-working-directory invocation by inspection; a second working-directory test was not run.

Source SHA-256 values were independently measured before and after the test and remained unchanged:

| File | SHA-256 |
| --- | --- |
| `backend/app/storage/local.py` | `6532f479e1b37540b54ea179536843e0ebd22f89b4eb00b1294e39c356624aea` |
| `tests/backend/test_storage_root.py` | `5a49d6add539bb5095b5b52414f5315c07439c5ae9fb9eae26a08574d3d037dc` |

## Independent targeted execution

Both Python commands used required escalation, from the repository root. Initial command:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/backend/test_storage_root.py -q -p no:cacheprovider --junitxml=.orchestration/reports/R08-WEB-002-review-08-targeted.xml
```

Result: **setup ERROR**, Windows `PermissionError [WinError 5]` scanning the shared `C:\Users\dldnj\AppData\Local\Temp\pytest-of-dldnj` directory; the test body did not execute. Preserved [initial JUnit](R08-WEB-002-review-08-targeted.xml), SHA-256 `efda743f3007f00086de2f9f7eb5de96da865dd8f10d0a97dfd11c1e3c6a2065`. This is environment/setup evidence, not a product assertion failure.

Verified the retry base path was absent and resolved inside the repository before passing it to pytest, which can clear an existing base directory. Retry:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/backend/test_storage_root.py -q -p no:cacheprovider --basetemp=.orchestration/reports/R08-WEB-002-review-08-tmp-20260912-a --junitxml=.orchestration/reports/R08-WEB-002-review-08-targeted-retry.xml
```

Result: **1 passed, 2 warnings in 0.02s**, exit 0. Independently parsed [retry JUnit](R08-WEB-002-review-08-targeted-retry.xml): tests 1, failures 0, errors 0, skipped 0; timestamp `2026-09-12T23:39:19.611873+09:00`. SHA-256 `aa8a0eddf4589cdf7a816638f43b85b01aea8592bfd04b7ff87cd4fece3faa87`. Warnings concern Starlette/httpx and the deprecated AnyIO BlockingPortal alias.

Inspected `tests/backend/conftest.py`, `backend/app/main.py`, `backend/app/db.py` and `backend/app/api/dependencies.py` before execution: collection imports the app and constructs a lazy SQLAlchemy engine, but the selected test requests no database/client/catalog fixture and invokes no API route or storage dependency. Its constructor calls have mkdir mocked. No DB connection/migration, configured-storage creation, object write/copy/delete, reconciliation, service restart or baseline rewrite was performed. Pytest writes its temporary fixture directory and the two JUnit artifacts; Python bytecode and pytest cache writes were disabled. A later `rg --files` report inventory encountered access denied on the elevated pytest temp directory; known JUnit files and hashes were read successfully. No temp cleanup was attempted.

Other storage tests were inspected but not executed: the atomic-publication test writes temporary objects, and migration/reconciliation/upload tests mutate isolated databases or storage. The assignment prohibits DB/storage mutation. There is no concern requiring another full suite; retained 54 Backend / 23 Frontend / 2 integration / typecheck/build PASS remain historical evidence with their original attribution, not new executions here.

## Remaining closure gate — parent runtime evidence

Parent must supply a preservation account and configured before/after ordinary-restart readback for the same DB and exact original fixture, then the closure reviewer must assess that evidence. Required identity from the prior independent report:

- Relative key: `objects/41ee9635-80f5-4dfd-8c7f-25c4be181f47/383d49f8-1783-4910-a567-dcd15992c253.png`.
- Original bytes SHA-256: `ebfa933afb0bfbe51ae0e2eb059cb58b4dfd22b6fcb67048450257b78b194135`.
- Retained `ENV-P1-DB-001-records.json` SHA-256: `0ab5f214eac550f4da5924a550d49f3c9cf3b16aebc9b0ba02c421cf5ef8ad5b`.

These fixture hashes and prior outside-root placement are attributed historical evidence, not remeasured in this correction review. Closure requires verified corrected physical root and exact object/hash, preservation of legacy original and baseline without conflicting overwrite/deletion/reseed/DB replacement, unchanged screenshot and catalog IDs/metadata/associations, and exact multilingual Expected Strings plus API original-content hash across the parent's ordinary restart. A passing path-resolution unit test cannot establish those runtime facts. Host/Compose alignment is supported statically above; an actual mode switch is not claimed.

Keep R08-WEB-002 and storage-dependent configured acceptance conditional until that evidence arrives and is reviewed. Historical authenticated readiness and same-path retention successes remain valid within their original limits. This reviewer changed no product/test source, orchestration state, prior review, database or application storage; no commit or push.
