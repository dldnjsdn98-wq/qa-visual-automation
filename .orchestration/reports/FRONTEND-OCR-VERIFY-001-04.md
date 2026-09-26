# FRONTEND-OCR-VERIFY-001 / owner 04

Date: 2026-09-25 KST.  
Submission status: `READY_FOR_PM_REVIEW`. This is scoped owner verification evidence. It does not activate Reviewer08 and does not mark AC-P3-01..04 complete.

## Result

The PM-activated live verification completed against an isolated PostgreSQL database, isolated local storage, the submitted production Web UI, the current Backend API, and the qualified Windows Korean PaddleOCR runner.

The end-to-end lifecycle passed:

- same-`client_run_id` creation returned 202 then replayed 200 without a duplicate run;
- the qualified fixture was recognized as `안녕하세요 설정 123` with one raw region, confidence `0.9957900643348694`, bbox `77,115,619,82`, and exact item score 100;
- the first run completed `SUCCEEDED / COMPLETE`; its recognized item was `PASS`, while empty and missing expectations were individually `UNVERIFIED`, so the contract-required aggregate was `UNVERIFIED / PARTIAL_UNVERIFIED` with `incomplete=true`;
- after the current catalog text changed, the old run snapshot stayed byte-exact and the new run captured the changed text, completed processing successfully, and produced quality `FAIL`;
- corrupting the isolated stored bytes after run creation produced a durable `FAILED / INPUT_HASH_MISMATCH` run with null quality, then the original bytes were restored;
- a no-expectations screenshot completed with `UNVERIFIED / NO_EXPECTATIONS`;
- history kept the failed request as latest `all`, while Latest Completed selected the preceding successful rerun;
- original screenshot bytes, SHA-256, dimensions, and Phase 2 metadata including empty and Unicode values round-tripped exactly.

The production browser displayed the same facts. It kept the selected run from the deep link, separated current catalog text from each immutable run snapshot, rendered raw coordinates and confidence, distinguished empty from missing values, kept processing failure separate from quality failure, and showed the successful rerun as Latest Completed while retaining the later failed request in history. No browser console/network failure was observed in the final run.

## Contract correction made in the scoped harness

Only `tests/frontend/run_integration.py` changed. The readiness-only OCR path now performs the real lifecycle, records source/runtime identities, supports a prebuilt production tree and a fixed isolated API port, and preserves detailed endpoint responses before an assertion failure.

The first diagnostic run found a harness expectation error rather than a product defect. The accepted contract says that any unverified item makes an otherwise passing aggregate `UNVERIFIED`. The harness originally expected aggregate `PASS` for one passing item plus empty/missing items. It now expects `UNVERIFIED / PARTIAL_UNVERIFIED`, checks `evaluated_count=1`, `pass_count=1`, `unverified_count=2`, and still requires the recognized item itself to be exact `PASS`.

`frontend/tests/integration/contract.test.ts` was executed unchanged.

## Runtime identity

- Backend source manifest file SHA-256: `7b3bb7e5638f1e7cbda101bd2e5451f5453c0b547e410b3b9d7d06a3b8e2e23d`; aggregate `bb9c86a548c31bfb69329024ad992e605c41d10f6e7258c9b81dd5cb2237187f`.
- Backend production image: `qa-backend-ocr-production:local`, digest `sha256:f5864cffb217c86355c747bb1780a5ad4ac786f65ef01a40696131749df6882f`.
- Worker source manifest file SHA-256: `98ea7e81109668dd073ef4f011b4d4c14eff3eea2a96340a00062f6850050b0a`; aggregate `058a445d90b7c50897f77f503a31e7dd425ea71f845a70a40666816e3c7a7b94`.
- Profile: `paddleocr-korean-medium-windows-amd64-cpython312-v1`, digest `00300d2aebd8097cba3879f8f35cae888c3e7a6b0abd3f426b654e5d7201c679`.
- Engine/runtime observed by the API: PaddleOCR `3.7.0`, Windows AMD64, CPython 3.12, CPU fp32, one thread, detector `PP-OCRv6_medium_det`, recognizer `korean_PP-OCRv5_mobile_rec`.
- Fixture SHA-256: `d34992612ae1b01629475fdc7ed1bcc3359cfcb798c7bb22959f6cd709aa2702`, 14,416 bytes, 1280 x 320.
- PostgreSQL image: `postgres:17-alpine`; a unique container and database were created for the run and removed afterward.
- Production Web: Next.js 16.3.6 optimized build, TypeScript and static generation passed. The final bundle was built with `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8002`; BUILD_ID file SHA-256 `fe74a55140e7923afd9c6a3794bab2ec9fc5ec53b3ca5a59eca66aab8f83c2aa`.
- Actual agent model identity: `unverified`.

## Verification commands and results

1. `node frontend/node_modules/next/dist/bin/next build .pytest_cache/phase3-frontend-04/live-web --webpack` with the fixed API origin: `PASS`; compile, TypeScript, static generation 3/3, optimization, and trace collection completed.
2. Qualified Worker Python running `tests/frontend/run_integration.py --verify-ocr-web --isolated-postgres` with Worker site-packages first, pinned model/cache roots, one-thread native settings, prebuilt Web root, and `QA_VERIFY_API_PORT=8002`: `PASS`.
3. Browser inspection through the Codex in-app browser: `PASS` for first run, catalog-mutation rerun, failed run, history/latest-completed selection, snapshot/current distinction, raw coordinates, source hash, empty/missing displays, and processing-versus-quality separation.
4. `npm run test:integration` with `QA_API_BASE_URL=http://127.0.0.1:8002`: `PASS`, 1 file and 2 tests.
5. Harness AST parse and scoped `git diff --check`: `PASS`; only the existing LF-to-CRLF notice was emitted.

The first integration-test attempt did not run because sandbox permissions denied Vitest's temporary write under `node_modules/.vite-temp`; the approved rerun passed. Earlier live attempts are retained in the evidence: Docker sandbox denial before runtime, package precedence causing `ENGINE_UNAVAILABLE`, the aggregate-expectation diagnostic, and a production bundle/API-origin mismatch that caused browser `NETWORK_ERROR`. None is reported as a successful product check.

## Evidence and final SHA-256

- `tests/frontend/run_integration.py`: `67d0223f2eb6b079037d19db9b4b95c4abd67448ca376e651498f3a8b16264ff`.
- `frontend/tests/integration/contract.test.ts`: `72d9cf2522e27490c84dc3d53e4097ff10f2ec99c325d7204355e8d1084dd46b`.
- `.orchestration/reports/FRONTEND-OCR-VERIFY-001-04-evidence.json`: `dc23871457272dbba938481d4020a075edc61fc8e71599a2dce5cb1e15b73ca3` before this report was written.
- `.orchestration/reports/FRONTEND-OCR-VERIFY-001-04-evidence-diagnostic.json`: `7c39773109cdd1da69c7a9fbf0970621a09865b21132a70aed23d6dbd49e6f97`.
- `.orchestration/reports/FRONTEND-OCR-VERIFY-001-04-evidence.web.log`: `353e1fe83b6364ea969373f55ce7c3c50edf08c80bfae2d027d32978944026c4`.

The evidence records the harness hash as the same `67d022...64ff` at start, before browser inspection, and after cleanup. The forced production-server termination is recorded as `terminated_exit_1`; this is the harness stop operation after browser verification. API, database, and PostgreSQL container cleanup are all recorded complete.

## Limits and acceptance status

- This run used the approved Korean qualification fixture and a synthetic catalog. It does not claim arbitrary OCR accuracy or broad multilingual engine qualification.
- The qualified runtime identity is evidenced; the executing agent model remains `unverified`.
- AC-P3-01, AC-P3-02, AC-P3-03, and AC-P3-04 remain `NOT_RUN` pending PM01's phase decision and the separately controlled independent review sequence.
- Reviewer08 was not invoked.
- No product file, shared database, user data, security setting, deployment, commit, push, IP check, Phase 4, or mobile scope was changed.

PM01 should reconcile this matched live submission and decide the next gate. Independent Reviewer08 remains blocked until PM activation.
