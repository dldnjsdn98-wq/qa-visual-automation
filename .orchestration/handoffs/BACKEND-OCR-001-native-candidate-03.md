# Handoff: W1/L1 proposed native corrections

- Task / owner: BACKEND-OCR-001 / P3-RUNTIME-001, Backend03.
- Activation: PHASE-3-native-correction-plan-01.md, candidate preparation only.
- Status: PROPOSED_PATCHES_STATIC_REVIEW_COMPLETE; PM_DECISION_PENDING. Product source/test application and native execution HOLD.
- Changed files: own native-candidate evidence reports, proposed .patch files and static validation artifacts only. No product/test patch applied.
- Contract changes: none. Revision2 remains2GiB/300s; existing test-specific250ms condition preserved.
- Branch / commit: null / null.
- Review: Windows writer Galileo Astra/medium, independent Hooke Astra/medium; Linux writer Fermat Sol/high, independent Mill Sol/high. Parent integrates static applicability and source hashes.
- Tests: pytest/build/native/container/model NOT_RUN under current preparation-only scope. Parent exact in-memory diff/AST and git apply --check PASS for both patches; static candidate validation only, no candidate function or proposed test executed.
- Current evidence: .orchestration/reports/BACKEND-OCR-001-native-candidate-03.md; lane-specific reports/patches use the same native-candidate prefix.
- Blockers/risks: W1 remains an unproven startup console hypothesis; L1 fixed pressure/timing oracle remains unexecuted. Native Windows pause count3 and historical cleanup2 unchanged; prior Linux shortpeak SKIP unchanged. No conhost exception, limit change, retry/tuning or L2 substitution.
- Acceptance: P3 AC/production admission/Frontend04/Reviewer08 remain gated.
- Next owner/action: independent static review complete; PM decides exact source application and separate native execution prerequisites. This handoff grants neither.

- W1 final report SHA2569053925f9d8436556ce0bf69f2daa26aa78887521481d31d8ef660b147c1698d; patch84a8fb80f36b7718ac580c31f3fec8fc44cb8c6be28dc50539a30e1126ea1f9f; independent reviewf426d2009556a6126592de7a86b7965781882714ce19f0f6fd24bed438cb0957 PASS static only.
- L1 final report SHA256ea706e2f02ede9c9b6aed446127d85bdbb665cc73380e02a7738cad61ecf0f9; patchd15ebab5fc1a5c3b4bb6fdd8c5d06907216decbff087f9f7722b34f9669a6639; independent review502349baf5895278deafc6b93d3498caf5ea3e68fbf01b1654b6effde5cefd5d PASS static only.
- Artifact manifest: .orchestration/reports/BACKEND-OCR-001-native-candidate-manifest-03.json. Baseline helper/test unchanged ef7d7ffe.../382257cf...; no source application.
