# Approved W1/L1 application — independent evidence review

2026-09-26 KST. **PASS — current-source identity and recorded pure12 evidence.** No discrepancy found within this narrow read-only review. Requested highest Astra/medium reviewer context retained; actual model not independently verified. Prior immutable03 artifacts untouched.

Parent/user relayed explicit PM activation and one regular require_escalated git application returning exit0. `application-01.json` records that command/result as a transcription of tool chunk8b67a3; this reviewer independently verifies resulting source bytes, not the original approval/tool event. Earlier denied application history is not erased.

## Current source identity

Independently read and hashed both current files. Raw byte lengths and SHA-256 values exactly match application-01.json; UTF-8 CRLF-to-LF normalization matches both recorded expected canonical hashes. Helper has829 CRLF lines, test has592; neither has lone LF.

| Source | Bytes | Raw SHA-256 | Canonical LF SHA-256 |
|---|---:|---|---|
| `backend/app/workers/ocr_containment.py` | 42692 | `9a47c3348980b4f5d25afafce5407ed067cd974caff2b60b87d2dc5f8228dbd9` | `6129ff42c0789df51c105068cbda48d0b299885f53c491e7d3a777315661467c` |
| `tests/backend/test_ocr_containment.py` | 29181 | `e72c2fb79a9bc3b0c0e08f155b5c78f16173d8e02ecc9f8349f2ecab3674af45` | `52349c96c31b6c373d8d8c99471b21df64ea5dea4a0a77f52539a884492e0f02` |

Helper retains ordinary `_launch_windows(argv, env, cwd, limit)` and W1 flags `0x4 | 0x400 | 0x8 | 0x00080000`. No diagnostic owner-sink/primary-thread hook is present; canonical source is W1-only6129, not composed-hookf9f41.

## Recorded test verification

Exact recorded command, cwd `C:\Dev\qa-visual-automation`:

```text
C:\Dev\qa-visual-automation\.pytest_cache\agent-clean-win\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests/backend/test_ocr_containment.py::test_l1_shortpeak_oracle --junitxml=C:\Dev\qa-visual-automation\.orchestration\reports\BACKEND-OCR-001-approved-application-evidence-04\pure12-junit.xml
```

Command record disables plugin autoload and bytecode, and records native opt-ins/PYTEST_ADDOPTS/PYTEST_PLUGINS absent. The selected function's12 parametrizations and direct pure `_l1_oracle` call were read statically; it requests only `overrides, expected`. Fixture inspection is parent-recorded and was not broadened/repeated.

Result record exit0; stdout says `12 passed, 1 warning in 0.07s`; stderr is empty. JUnit reports12 tests, zero failures/errors/skips and exactly the selected parametrized node: overrides0–11 cover killed/denied success, three timing failures, attempted/identity/cleanup failures and four unproved-cause cases. No unrelated testcase appears. JUnit0.068s and command elapsed1.718s measure different scopes and are consistent. The one warning is StarletteDeprecationWarning about httpx in starlette.testclient, reported by parent as existing; no dependency change is proposed.

These artifacts corroborate the reported single selected run. This reviewer did not rerun pytest, import source, execute native/API calls or independently assert absence of other historical invocations. Application AST PASS and sources-unchanged-during-test are recorded parent results; current hashes independently agree.

## Exact evidence hashes

All files below were read and hashed under `.orchestration/reports/BACKEND-OCR-001-approved-application-evidence-04/`.

| File | SHA-256 |
|---|---|
| `application-01.json` | `5741c7820ea5c928f197e8bf56f339d72f135a72730385d8da12f6b0d47bf056` |
| `test-command-01.json` | `e2118f1039538981839f339597de1b9602f6a1ded1f72a5e8453889cdeaa58d4` |
| `test-result-01.json` | `2d0e498f0723fc53de72901b972ce62fc8c61ec3f4ee5a42dc74f8a45f80fef2` |
| `fixture-inspection-01.json` | `4366fe83df1a2c88c866f56a4f8413275efbf0a19e293f1b827864fe159c4789` |
| `pure12-stdout.log` | `0c9d06633ca4477d4a34f9604e3b9bbe274a51e89da33ca1eceb049670b99be3` |
| `pure12-stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `pure12-junit.xml` | `ee5e941b5d3ece8c12321e5b4b612e227fd9c94a40a4384a8c5419d6d5349cc6` |

Only this NEW review file was written. Reads were confined to the two sources and exact evidence directory/files; no denied discovery/retry or broad audit. Recorded pure tests:12 PASS. Reviewer runtime tests:NOT_RUN. Native/build/model/DB/additional-hook remain HOLD; Windows same-cause3/cleanup2 unchanged. No native qualification, admission or downstream gate is promoted.
