# BACKEND-UPLOAD-001 review rework handoff / Owner 03

Status: READY_FOR_REVIEW owner submission; independent acceptance pending.

Formal CHANGES_REQUESTED input:

- `.orchestration/reports/REVIEW-UPLOAD-001-08.md` — `1da2d73e837d62bc4b9926f41b168a56d12bc64bd9ab8c56001640d7c234bab8`
- `.orchestration/handoffs/REVIEW-UPLOAD-001-08.md` — `f182ffe3eb83b7ae193bb7c5efdca4d852c950108bce0822d11fff919dee13cf`

Owner correction evidence:

- Report: `.orchestration/reports/BACKEND-UPLOAD-001-review-rework-03.md`
- Report SHA-256: `095d641be32bce1d0c66672c875a34493c96555acca604a53c21ad96dfafa0a4`
- Current source manifest: `.orchestration/reports/BACKEND-UPLOAD-001-review-rework-source-manifest.txt`
- Manifest count/aggregate: `77` / `a8b5225bceb106cc3e09883eb3e68c2a28d659f8c0ee9ec65eb6974ffa7696a0`
- Host raw output: `.orchestration/reports/BACKEND-UPLOAD-001-review-rework-03-tests.txt` — `b8889bdf6cca7a1823954b5fa5c516ede226b0e096e24a64b4b4f352cec9b16c`
- Host JUnit: `.orchestration/reports/BACKEND-UPLOAD-001-review-rework-03.xml` — `187ffcedf6992100d0c217da26201c4636be535c0203b8653aff5135bc17aadb`
- Linux evidence: `.orchestration/reports/BACKEND-UPLOAD-001-review-rework-03-linux.txt` — `3965fe3c1b314a81d3ffe7467fd90d9b7dd3d51279f89a1a620a4edcb44e9f91`
- Linux image ID: `sha256:f5d00d7ef450f7150f87794061991ffea1d25bcea6ef7dce9ef67ea40072669b`

Correction summary:

- `R08-P2-REVIEW-005`: four body-bearing requests per process may retain whole-body memory. Further requests receive `503 REQUEST_OVERLOADED`, `Retry-After: 1` before `receive`; completion, disconnect/cancel and error release the permit.
- `R08-P2-REVIEW-009`: finalize uses `FOR KEY SHARE` on every scoped parent through atomic Screenshot plus receipt completion. Existing `FOR UPDATE` callers remain unchanged. Two-connection PostgreSQL barriers prove delete-waits/success and delete-first `404` plus same-generation fenced `FAILED` after confirmed rollback.
- Existing five-second receipt lock timeout remains.

Fresh results:

- New 005/009 tests: `7 passed`.
- Reviewer risk selection for prior 001..004: `38 passed` as owner evidence.
- Regression selection after lock-mode correction: `8 passed`.
- Final host Backend suite: `126 passed, 1 warning`.
- Final Linux/hash-lock Backend suite: `126 passed, 2 warnings`.
- Hash-lock image build, project wheel install and `pip check`: PASS.
- AST: 67 files PASS; scoped diff-check PASS; canonical manifest verification PASS.

The first full run (`1 failed, 125 passed`) is preserved because it caught an accidental shared lock-mode change; the final code restores that behavior. The sandbox-denied first Linux launch and discarded first manifest sort attempt are also retained and not reported as product PASS/FAIL.

The disposable PostgreSQL 17 container was stopped and removed after verifying zero residual `qa_backend_test_%` databases. No user/shared DB or service was reset. No commit, push, deploy, account/security change, IP check, PM-state edit, contract, Frontend or uploader edit occurred.

Reviewer08 must independently rerun and decide closure of `005`, `009`, preflight `001..003` and review `004`. PM alone may update task/acceptance/phase status. Frontend04 and Uploader06 should use the report/manifest hashes above for any matching rerun; receipt response and upload success contracts remain unchanged except the documented overload response at capacity.

Requested subagent routing was Sol/high for 005, Astra/medium for 009, Sol/medium for evidence and Terra/high for submission hygiene. The management API returned `not_found` before any result or patch appeared, so actual models are unverified and all final work is parent-executed.
