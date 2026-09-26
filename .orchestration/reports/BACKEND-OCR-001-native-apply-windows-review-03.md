# W1 concrete startup harness — independent static review

2026-09-26 KST. **PASS — exact static candidate review only.** No blocking static finding remains in the refrozen artifacts below. Source application, additional product-hook claim and native execution remain **HOLD**. This is neither execution readiness nor native qualification, AC/admission or downstream approval. Windows same-cause3 / separate cleanup2 remain unchanged; no new run occurred.

Requested difficulty/model: highest, Astra/medium; actual model selection is not independently verified. Reused the existing independent review role and prior API review. Read AGENTS.md, PHASE-3-native-candidate-apply-01.md, exact candidate files and their exact query dependency; no broad discovery or additional source retrieval.

## Exact reviewed identities

Candidate names below are relative to `.orchestration/reports/`. SHA-256 values are actual file hashes unless explicitly described as canonical LF.

| Artifact | SHA-256 |
|---|---|
| `BACKEND-OCR-001-native-apply-windows-harness-03.py` | `be6b865e6ca8be5cea2bedf04bc6ed79dcdb17ed3510c165a393ee882f0d0a11` |
| `BACKEND-OCR-001-native-apply-windows-plan-03.md` | `cc8fcd7ce40fe2ade92e5dcdc11208b47123fe022880589d68083e6a33227865` |
| `BACKEND-OCR-001-native-apply-windows-hook-03.patch` | `0496d7a5cc18881d7c8fda045969a8314911b1913673dd6372ef7418600c56f3` |
| Query dependency `BACKEND-OCR-001-native-diagnostic-windows-03.py`, canonical LF independently hashed | `e0650cbc135da408b589c1765bc7aaa67f2db1e2f62174c339f3549426210133` |
| Actual unchanged `backend/app/workers/ocr_containment.py`, independently hashed | `ef7d7ffe6dbc0b8f620ae9416818614cf9aa9dc5ceb822fdee11d4feca76bec5` |

The hook's declared base is **prospective W1**, canonical LF `6129ff42c0789df51c105068cbda48d0b299885f53c491e7d3a777315661467c`, not the actual helper. Composed W1+hook canonical LF is `f9f41dc9d09f003a857d6e98c3053279b9616a346f0b34aa97309666c14c6302`; the harness requires exactly this source before executing its bytes. Parent reports final exact pins, in-memory baseline+W1+hook context/composition/hash PASS and helper/harness/CHILD AST PASS, recorded in `windows-capture-static-01.json`. These checks are parent-reported and were not rerun by this reviewer. Prior W1 API report `9053925f9d8436556ce0bf69f2daa26aa78887521481d31d8ef660b147c1698d` is reused, not refetched.

## Ownership and control-flow assessment

- Private hook accepts only an empty built-in list; ordinary/default launch path remains unchanged. It publishes the original owner and original primary-thread handle before return/finally, `_check_limits` and ResumeThread. This provides the supervisor a stop route if return-time attribute cleanup stalls after publication. The hook does not copy the launcher, change flags/limits or resume useful work.
- Before publication, existing helper owns failed-setup cleanup. No published owner means the harness cannot infer absence of a process or independently stop one whose creation/assignment is unresolved. After publication, supervisor owns the sole Job termination route. The proposed exception branch avoids a second helper stop/close; return-finally failures still leave the published sink available. Successful timely launch completion plus complete pre-resume evidence is required before resume.
- Original direct/Job/primary/pipe handles are retained; no PID/name/parent-Job termination, substitute reopened process, helper.stop call or automatic retry exists. A late publication can receive a best-effort termination request without changing the already failed launch gate. No cleanup proof is accepted after its deadline. Harness exit is explicitly not proof of cleanup for unresolved/unassigned processes.
- Before resume and after startup, predicates require one direct process in class1/class3, exact owned-Job membership and retained creation identity, intended stable image/path hash, matching self-report PID/image, effective WS flags6, page-rounded 256MiB bound, Job flags0x2208 and active limit1. Unknown/truncated data blocks success. Queries are separate non-atomic observations, not continuous containment proof.
- Child is startup-only stdlib with binary redirected pipe handshake and nonce. ResumeThread must return1 before S is sent. There is no native package/model/import phase. Any later import-capable invocation needs a different reviewed harness and separate authorization.

## Findings resolved in the final freeze

1. **Late-result acceptance:** workers now append events rather than mutate final report booleans. Stage, stop proof and close results require completion timestamps within their deadlines. Main checks worker completion; late results cannot promote the fixed published snapshot. Stop deadline is `min(stop_request_time + 2.0, t0 + 30)` for early failures as well as normal completion. All joins share that tail; close must begin and finish within it.
2. **Missing startup frame hid counts:** receiver and count observer are separate. Receiver failure fixes the stop time immediately, starts counts-only capture for at most one second and enters owned termination without optional image/limit auditing. This capture races termination and may leave cause unknown; it cannot establish successful startup. Resume result is checked immediately before handshake.
3. **Unsafe close/duplicate stop:** close is permitted only after timely direct-signaled/Job-empty proof and all tracked launcher/observer/receiver/stop workers have ended. Original primary thread is closed once, then owner.close uses proven stopped state. Unresolved/partial/late closure is retained, with no extra stop.
4. **Invalid raw accounting promoted to failure:** the previous frozen harness `c37b90db07f7ef985eb90fbe6454c3d5d412ed9eebda832f26e6cb58b408c124` admitted raw helper anomaly counts without query validity. Final lines in the extra-process predicate now require `query_succeeded is True`, class1 and `returned_bytes == buffer_bytes == 48` before interpreting ActiveProcesses. Failed or invalid queries remain unknown through failed helper_check; partially populated fields cannot increment history. Valid extra-process evidence still takes precedence over optional identity errors.

## Remaining limitations and gates

Prepublication native setup can block without transferring handles. Native resume, query, termination, handle close and filesystem/output calls have no established hard return-time bound. Bounded joins cannot forcibly cancel them. Live workers/retained owners remain unresolved; late evidence after the snapshot is not asserted absent. A passing startup slice would mean only STARTUP_NONREPRO_NOT_QUALIFIED, not permanent no-console behavior, DLL/import compatibility, hard-WS continuity, full OCR or full-runtime acceptance.

Parent reported the actual two-file git application failed with exit128 Permission denied and unchanged helper/test baselines. This reviewer did not retry, use an alternate writer or apply either patch. Parent now reports exact in-memory composition PASS, but the extra product hook still requires a separate PM claim and resolution of the source-write hold; native execution requires a distinct decision. No authorization is inferred from this PASS.

## Actual checks and changes

Reviewer performed read-only text/control-flow inspection and SHA-256 checks; final candidate hashes, unchanged helper and canonical query dependency matched. Author reports source-only AST parsing of proposed helper/harness/embedded child; this reviewer did not rerun AST or claim those as independently executed tests. Runtime/import/native/API probes, pytest, builds, containers, DB and models: **NOT_RUN**.

Only this review file was authored by this reviewer. No author's file, product/test, dependency, ACL, profile or security setting was changed. No denied nested marker was read. Earlier incidental discovery denials remain documented in the prior review; they were not retried or bypassed. Findings and final disposition were sent directly to author and parent for static integration.
