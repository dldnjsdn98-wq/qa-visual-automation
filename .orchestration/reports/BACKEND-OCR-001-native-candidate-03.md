# Native correction candidates / Backend03

Status: PROPOSED_PATCHES_STATIC_REVIEW_COMPLETE; PM_DECISION_PENDING. Product source/test application and all native execution remain HOLD. Branch/commit null.

Authorization: PHASE-3-native-correction-plan-01.md, SHA256 `3ea34f8507e1724608704b2842c924f6ce6fcaf9f8249fdbdf295d95789132df`. Architect reassessment report `7fa4ba3b9452bd35317a051104aa9f18d4ca22e652ac25c0c8a628b7c1108a7c` and handoff `5a2de4348bcd87463beae9bc739ca60bd87a7ba016caefde9207ae261a8e441d` were read/hash-matched. This authorization is limited to proposed patches, exact plans and independent static review. It is not source-application or runtime authorization.

## Frozen inputs and ownership

- Windows source: `backend/app/workers/ocr_containment.py`, SHA256 `ef7d7ffe6dbc0b8f620ae9416818614cf9aa9dc5ceb822fdee11d4feca76bec5`. Galileo reused, requested Astra/medium (highest). Own Windows candidate report/patch only.
- Linux source: `tests/backend/test_ocr_containment.py`, SHA256 `382257cfb9747b2fe9d7aa87fedd5d50d5f853745c483be5b1764c3c958ade1b`. Fermat reused, requested Sol/high (high). Own Linux candidate report/patch only.
- Revision2 contract: SHA256 `478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44`, unchanged. Parent owns this integration report, handoff and candidate manifest. Requested agent configuration is distinct from independently verified runtime model identity.

## Static review gates

W1 must cite actually retrieved authoritative flag/stdio/STARTUPINFOEX/suspended-Job contracts and audit known console/subprocess paths. The proposed change must replace, not combine, CREATE_NO_WINDOW with DETACHED_PROCESS using the same interpreter/pipes/limits. No Job2, conhost exemption, breakaway or memory-bound change. Uninspected native internals remain unknown. Proposed observation phases must identify pre-resume, startup and import boundaries, retained handle/creation identity, own-Job accounting/membership and effective bounds. Potentially blocked observations may not hold up the sole owner's bounded cleanup; unresolved cleanup means quarantine.

L1 must predeclare fixed touched baseline/increment, admitted headroom/event conditions and a single pressure gate. The observer owns both monotonic endpoints: before release and after observed completion/denial or identity-bound exit. Cause must combine attempted pressure identity with fresh cgroup evidence; max/reclaim or exit code alone is not enough. Strict interval <0.25s stays; no subtraction, tuning or L2 substitution. Observer death cannot generate a timing PASS. Pure-oracle cases may be proposed, but no pytest/native/build/container/model execution is authorized in this preparation.

Independent review assesses exact proposed patch bytes and oracle semantics. A dry-run patch applicability/syntax check, if performed, is static validation only and never source application. Any later source application and native execution require separate PM decisions.

## Preserved prior state

Windows native same-cause3 and historical cleanup2 remain separate; native lane stays paused. Linux prior shortpeak0.411939... is only an observed upper bound, not proof of actual duration on either side of250ms; SKIP remains. Earlier Linux passing slices and controlled job-service parent-OOM recovery retain their original scope. The denied nested identity marker is not read/retried/copied; owner56/56 versus PM incomplete recursive verification stays attributed. No whole historical audit is repeated.

Production admission, Frontend04, Reviewer08 and all P3 AC remain gated. No product/tests/worker/profile/dependency/API/schema/host-permission edits, model access, builds, probes, tests, commits or pushes are part of this preparation.

## Frozen proposed candidates and parent static checks

W1 final report `9053925f9d8436556ce0bf69f2daa26aa78887521481d31d8ef660b147c1698d`; patch `84a8fb80f36b7718ac580c31f3fec8fc44cb8c6be28dc50539a30e1126ea1f9f`. One hunk changes only the console-policy constant and adjacent comment; combined flags0x08080404 ->0x0008040c. Official Microsoft Learn pages were read by the author through the browser and are quoted/cited in its report; live pages are not commit-pinned snapshots. Static package audit found no literal console creation calls in the scoped Python source set, but native internals and transitive imports remain unknown. Paddle's PATH-indexing DLL fallback is an unresolved import precondition; no PATH change is proposed. The diff includes no diagnostic instrumentation or cleanup change.

L1 report `ea706e2f02ede9c9b6aed446127d85bdbb665cc73380e02a7738cad61ecf0f9`; patch `d15ebab5fc1a5c3b4bb6fdd8c5d06907216decbff087f9f7722b34f9669a6639`. Two hunks add a fixed short-attempt helper/oracle/prospective unit cases and route only shortpeak to it; mapped/descendant behavior is unchanged. Exact values: cap536870912, touched baseline335544320, one increment234881024, total570425344; admitted pre-gate headroom67108864..167772160. Protocol/identity/fresh-event checks precede the gate; same observer clock provides a conservative upper bound with strict250000000ns comparison. The outer owned-container evidence capture remains a future prerequisite, not implemented survival in this diff.

Parent ran the own-report-only in-memory unified-diff validator and `git apply --check` separately for both patches: exit0, exact context PASS, prospective Python AST PASS, no application. Canonical proposed-source SHA256 is LF/UTF-8: Windows `6129ff42c0789df51c105068cbda48d0b299885f53c491e7d3a777315661467c`; Linux `52349c96c31b6c373d8d8c99471b21df64ea5dea4a0a77f52539a884492e0f02`. These are in-memory candidate hashes, not hashes of applied product files. Corresponding native-candidate-*-static-01.json retain exact patch/source identities and NOT_RUN runtime status. No candidate function, proposed unit case, import, model, native API or child process was executed by these checks.

## Independent review and execution boundary

Mill's independent L1 review `BACKEND-OCR-001-native-candidate-linux-review-03.md`, SHA256 `502349baf5895278deafc6b93d3498caf5ea3e68fbf01b1654b6effde5cefd5d`, returned PASS for the frozen preparation proposal only. Verified fixed pressure arithmetic, headroom/events/participants, retained child identity, conservative observer endpoints, rejection of max-only/ambiguous cause, and cleanup-before-oracle control flow. Outside-container capture and exact changed-source image remain later execution prerequisites. Its12 prospective pure oracle cases were not run.

W1's minimal flag diff passed compatibility review, but parent and Hooke required the future plan to state two boundaries explicitly: every stop path preserves a separate maximum2s cleanup tail capped also by total-run deadline; an initial startup-only authorization cannot automatically execute native imports. Author clarified and refroze the report: cleanup_deadline=min(stop_request_time+2.0s,t0+30s), including early failure and startup-only completion. The first approved startup-only invocation must stop after startup; a later separately approved import-capable invocation repeats pre-resume/startup gates before import, each with one launch/one stop. No implicit retry/second invocation is authorized. Patch unchanged; no source/runtime change followed.

The proposed patches can be evaluated for PM source-application approval after exact static review. They cannot be used as immediate execution instructions: Windows needs a concrete independently reviewed owned-observer/hook/capture implementation; Linux needs a retained named-container owner/capture plan and a rebuilt exact-source image. Success of static compatibility or AST parsing proves neither installed runtime behavior nor timing feasibility. No old image may stand in for changed tests; no repeated native trial or parameter tuning is authorized by this packet.


Hooke's final independent W1 review `BACKEND-OCR-001-native-candidate-windows-review-03.md`, SHA256 `f426d2009556a6126592de7a86b7965781882714ce19f0f6fd24bed438cb0957`, returned PASS for static candidate-readiness after verifying both report clarifications and the unchanged patch. Reviewed author-fetched official excerpts without independently refetching them; package-audit findings remain attributed to the author. Missing concrete instrumentation/supervisor and installed native behavior are downstream gates, not silently completed work. Both reviewers recorded incidental denied file-name discovery in unrelated historical report directories without reading/retrying/bypassing those denied contents; no candidate artifact was blocked.

## Final disposition

PROPOSED_PATCHES_STATIC_REVIEW_COMPLETE, PM_DECISION_PENDING. W1 and L1 have exact proposed patches, independent static reviews and parent in-memory applicability/AST plus git apply --check results. Product helper and test retain their original hashes; no proposed patch was applied. All pytest, prospective oracle unit cases, native APIs/imports/probes, Docker/build/container/model/DB actions are NOT_RUN in this preparation. Read-only source/document retrieval and static patch validation are the only executed checks. No new runtime result is added to the previous diagnostic checkpoint.

PM next decides source application only if desired, with the exact frozen patch identities. Native execution remains separately held pending concrete reviewed capture/hook implementation, exact changed-source runtime build where applicable, and explicit per-lane authorization. Windows3/cleanup2, prior shortpeak SKIP, production admission and04/08/P3AC gates are unchanged. Candidate artifact hashes are delivered in `BACKEND-OCR-001-native-candidate-manifest-03.json`; it is a proposal evidence manifest, not qualification.

