# W1 independent static review / Backend03

2026-09-26 KST. **PASS — static candidate-readiness only.** Both plan clarifications were verified in the revised frozen report below; no blocking static finding remains. This is not source-application approval, execution readiness, native qualification, AC acceptance or admission. Windows same-cause count3 / separate cleanup count2 unchanged; PM and downstream gates remain closed.

Requested review difficulty/model: highest, Astra/medium. Actual model selection is not independently verified. This reviewer did not create additional tasks or delegate implementation.

## Frozen artifacts actually read and hashed

| Artifact | SHA-256 |
|---|---|
| `backend/app/workers/ocr_containment.py` | `ef7d7ffe6dbc0b8f620ae9416818614cf9aa9dc5ceb822fdee11d4feca76bec5` |
| `.orchestration/reports/BACKEND-OCR-001-native-candidate-windows-03.patch` | `84a8fb80f36b7718ac580c31f3fec8fc44cb8c6be28dc50539a30e1126ea1f9f` |
| `.orchestration/reports/BACKEND-OCR-001-native-candidate-windows-03.md` | `9053925f9d8436556ce0bf69f2daa26aa78887521481d31d8ef660b147c1698d` |

Read AGENTS.md and PHASE-3-native-correction-plan-01.md. Author Galileo confirmed the above report/patch freeze and actual Microsoft Learn browser retrieval. Reviewed the report's quoted rendered API excerpts and exact source URLs; did not independently refetch them or claim an immutable raw source capture. These live-page excerpts suffice for this narrowly scoped compatibility review. The package audit is author-supplied bounded evidence, not independently repeated here.

## Findings

- Resolved clarification 1: revised report explicitly defines `cleanup_deadline = min(stop_request_time + 2.0s, t0 + 30s)`, including early failure and startup-only completion. Unused observation time cannot extend the two-second tail; failure at t0+1s cannot receive 29 seconds of cleanup.
- Resolved clarification 2: initial future approval is startup-only and the invocation must terminate after startup. Native imports cannot be activated in that invocation. A later separately approved import-capable invocation repeats pre-resume/startup gates, with one owned launch/one stop per invocation. Neither the initial approval nor this review authorizes that later invocation or a hidden retry.

These were explicitness gaps in original report SHA-256 `8ecef52b814a71292bdfb5daf3f09bdecbe118288560da72e114712d642af472`; that version is superseded for this disposition. Patch remains unchanged.

- Minimality: patch changes only the adjacent comment and `0x08000000` to `0x8`; combined flags become `0x0008040c`. CREATE_NO_WINDOW is removed, with no CREATE_NEW_CONSOLE or breakaway added. Interpreter, environment, process limit and cleanup implementation are unchanged.
- Redirected handles: baseline retains three inheritable real pipe/null handles, HANDLE_LIST `0x00020002`, bInheritHandles TRUE, STARTF_USESTDHANDLES and STARTUPINFOEX with its full size and EXTENDED_STARTUPINFO_PRESENT. Author-fetched CreateProcessW, UpdateProcThreadAttribute and STARTUPINFOW excerpts support this explicit handle path; console detachment does not itself validate Python's runtime I/O behavior.
- Suspended Job semantics: creation still precedes assignment, hard-WS setup and effective-limit checks, followed by ResumeThread requiring previous suspend count1. The flag change does not alter this order. Nested Job assignment can fail; no unsupported guarantee of valid nesting, absence of pre-assignment memory activity, permanent console exclusion or absence of conhost is asserted.
- Audit limits: report distinguishes Windows bootstrap from Linux/CLI subprocess paths, identifies the Paddle PATH fallback risk, and leaves native DLLs, dynamic aliases, transitive imports and inference unknown. Literal-token absence is not treated as all-path proof. No dependency/environment change or model execution is implied.
- Oracle: prospective pre-resume, startup and import gates retain direct-handle PID/creation/image identity and exact owned-Job membership; class1/class3 counts require a sole direct process, including TotalProcesses1 at pre-resume. Later gates repeat identity/count/effective-limit observations. Nonce/PID frames gate work; invalid lengths, unstable identity, missing imports and failed APIs remain unknown/failure. Two members take failure precedence. Same page-rounded Job memory, active limit1, no breakaway and direct hard-WS bounds remain required. Non-atomic snapshots are explicitly not continuous proof.
- Cleanup: prospective one owned launch/one termination request, original handles, supervisor independent of observation locks and pre-kill queries, absolute observation deadlines and bounded polling are specified. No helper.stop duplication or close-under-live-query is allowed; unresolved observers/termination retain ownership and quarantine. The report correctly declines a hard wall-clock guarantee for synchronous native calls. Current production cleanup is unchanged.

## Required later gates

The two-line patch implements no pre-resume hook, retained supervisor ownership interface, import gate or independent timeout stop route. A separately reviewed concrete harness is mandatory before any diagnostic: expose owned handles before potentially blocking observations, enforce the stated deadlines without extending the cleanup tail, avoid duplicate termination, and retain handles while native access is unresolved. Native import side effects, PATH/DLL prerequisites, permanent no-console behavior, continuity/RSS and cleanup latency remain unproved. Clean startup/import would establish only that slice's nonreproduction.

Parent reports exact-context/in-memory AST/`git apply --check` PASS, with candidate LF source SHA-256 `6129ff42c0789df51c105068cbda48d0b299885f53c491e7d3a777315661467c`. These are parent-reported results; this reviewer did not run them. Author files and backend/test files were not edited. Only this review report was written.

## Actual verification and limitations

Performed static text inspection and SHA-256 checks only; all three hashes matched the requested baseline/author freeze. No Python runtime/imports, native/API probes, pytest, build, container, model, dependency, ACL or security changes. All runtime tests/qualification: **NOT_RUN**.

Before scope was narrowed, a file-name discovery command encountered access denials in unrelated report directories. No denied content was read, no access retry or alternate route was attempted, and the denied nested Windows marker was not read. A historical Windows diagnostic plan was read as background only; its older count2 does not replace the current count3 history. Subsequent reads were restricted to exact candidate artifacts. Initial candidate-report absence was resolved by the author's freeze; no missing-report assumption remains in this disposition.
