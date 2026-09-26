# Backend03 approved W1/L1 application checkpoint 04

Status: EXACT_SOURCE_APPLIED; PURE12_PASS; native/build/additional-hook HOLD. Previous checkpoint03 and historical failures remain immutable.

PM relayed the user's explicit approval of the concrete regular elevated approval route. Parent issued exactly one tools.exec_command request with sandbox_permissions=require_escalated for the approved git apply command. That request returned actual exit0 with empty output (tool chunk8b67a3); source readback then established success separately. This is not merely user approval or a claim inferred from approval. No ACL/security change, alternate writer, repeated escalation or Windows diagnostic hook application occurred. The earlier normal-context failed attempt remains in checkpoint03.

Applied files:

| Source | Raw SHA256 | Canonical LF SHA256 |
|---|---|---|
| backend/app/workers/ocr_containment.py | 9a47c3348980b4f5d25afafce5407ed067cd974caff2b60b87d2dc5f8228dbd9 | 6129ff42c0789df51c105068cbda48d0b299885f53c491e7d3a777315661467c |
| tests/backend/test_ocr_containment.py | e72c2fb79a9bc3b0c0e08f155b5c78f16173d8e02ecc9f8349f2ecab3674af45 | 52349c96c31b6c373d8d8c99471b21df64ea5dea4a0a77f52539a884492e0f02 |

Raw hashes differ from canonical because checkout bytes have CRLF. Canonical hashes match precisely the approved W1-only helper and L1 test candidates. Parent AST parsing passed for both, and raw bytes remained unchanged through the test and final readback.

## Executed validation

Fixture inspection: selected test takes only parametrized overrides/expected; backend database/client/catalog fixtures are not autouse. Engine and session factories initialize lazily; this selection does not request database fixtures or invoke API handlers. Prior fixture inspection was refreshed against applied source. External pytest plugin autoload and cacheprovider were disabled; native opt-in flags and inherited pytest overrides were absent for this process. No dependency installation or configuration edit was made.

One actual invocation of tests/backend/test_ocr_containment.py::test_l1_shortpeak_oracle: exit0, **12 passed, 1 warning in 0.07s**. Parent parsed the actual JUnit: exactly12 selected-node cases, zero failures/errors/skips. Wrapper wall time was1.718s. Warning: existing Starlette TestClient/httpx deprecation; no dependency update attempted. This is pure oracle validation only, not real OS containment or pressure evidence.

Evidence directory BACKEND-OCR-001-approved-application-evidence-04 contains transcribed application result with exact actual source hashes, fixture inspection, exact argv and environment controls, raw stdout/stderr, JUnit, exit/timing and final source/JUnit checks. The application result is explicitly transcribed from the tool response, not a fabricated shell-captured apply log.

One incidental rg discovery encountered unrelated denied Reviewer08 evidence directories; no read retry or bypass occurred. It did not affect selected source/fixture reads or test results.

## Remaining gates

Linux first preserves helper6129 plus test52349. Actual raw/LF pin inputs, a new exact-source image and explicit build/native execution approvals are still required. Windows extra hook0496 remains unapplied and separately gated; no blind repinning of Linux capture. No native probe, containment run, container/build/model/DB action, full279 run, push or deployment was performed. Windows same-cause3 / separate cleanup2 and04/08/admission/allAC gates remain unchanged. No automatic follow-on activation.

Independent exact evidence review is recorded separately in BACKEND-OCR-001-approved-application-review-04.md. Final own artifact manifest: BACKEND-OCR-001-approved-application-manifest-04.json, self excluded. PM is next owner for the distinct remaining decisions.

Final independent review: PASS, SHA256 bdf3063b32fcb55b5c2d4c94ff95e1500cfe165e4ffe4b33d3246c4693b1dcd3. PM separately confirmed actual source raw/LF hashes and pure12 evidence. The previous source-write blocker is resolved for this exact application; old failed-attempt evidence remains preserved.

Linux capture input boundary: its existing `sha256` field means exact raw bytes and `lf_sha256` means CRLF-normalized bytes. For current files these must be raw9a47c334... / LF6129ff42... and rawe72c2fb7... / LF52349c96... respectively, as fully recorded above. Its host AND image verification requires both identities; an image converting CRLF to LF will change raw hashes and cannot silently pass using canonical identity alone. Existing capture source/pin predicates were not changed. No complete future source-pin input or image is claimed ready by this two-file checkpoint; required other fixture/dependency pins and immutable image still require the next explicitly activated preparation/review.
