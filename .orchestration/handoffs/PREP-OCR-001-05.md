# PREP-OCR-001 handoff / OCR & Verification 05

- Task / owner: `PREP-OCR-001` / 05 OCR & Verification.
- Goal: assess PaddleOCR/OpenCV/RapidFuzz compatibility, locale/model mapping, output limits, licenses/resources, and multilingual fixture strategy before the reviewed Phase 3 contract.
- Status / activation evidence: preparation complete; `PHASE-3-activation-01.md` and current orchestration mark this preparation READY after Phase 2 acceptance. `OCR-001` remains BLOCKED by `REVIEW-ARCH-OCR-001` and PM implementation ownership.
- Difficulty / model: high because multilingual engine/model differences and platform compatibility affect every Phase 3 result. Requested `gpt-5.6-sol` / `high`; actual model unverified.
- Scope / changed files: this handoff and `.orchestration/reports/PREP-OCR-001-05.md` only. No product/shared/Phase4/mobile changes.
- Contract changes: none. Key proposal is explicit locale-to-model mapping: PP-OCRv6 medium for English/Chinese/Japanese and documented PP-OCRv5 Korean recognition for Korean; original-pixel polygons, separate recognition/detection/match confidence, versioned normalization and scorer identity. Architect 02's conservative v1 matching draft is compatible with runtime preparation: exact, then NFC plus Unicode whitespace collapse, then `rapidfuzz.distance.Levenshtein.normalized_similarity(processor=None)`; no casefold/NFKC/transliteration.
- Dependency proposal: CPython 3.12 CPU baseline; PaddleOCR 3.7.0, PaddlePaddle 3.3.1, RapidFuzz 3.14.6; resolve PaddleX/OpenCV in clean OS-specific environments before exact lock. One headless `cv2` provider only. No install/download performed.
- Commands/results: orchestration/role/package files and official docs read; focused repository scans PASS; bundled CPython 3.12.14 NFC/NFKC probe PASS; RapidFuzz absent. Existing project venv failed to launch because its referenced interpreter is absent. One Docker inventory check was permission denied and not repeated.
- Tests: OCR inference, model download/cache verification, RapidFuzz score boundaries, Windows/Linux parity and resource benchmark are NOT_RUN. AC-P3-01..04 remain NOT_RUN.
- Principal risks: PP-OCRv6 lacks Korean; text-line orientation documents only 0°/180°; general pipeline documents recognition confidence but not detection confidence; original-coordinate mapping after resize/preprocessing requires proof; matching must keep missing/empty/processing outcomes out of scored quality and use deterministic one-to-one assignment; hosted model-weight license/provenance needs explicit review.
- Review requested / result: Architect 02 and PM 01 consultation requested; no independent review result and no self-acceptance.
- Next owner / condition: Architect 02 dispositions the report's contract questions; Reviewer 08 accepts the exact contract; PM 01 approves role05 paths and owner03 dependency edit. Only then may `OCR-001` implementation/install/model acquisition begin.
- Branch / commit: null / null. No Commit/Push.
