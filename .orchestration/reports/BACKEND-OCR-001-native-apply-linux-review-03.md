# Independent L1 external capture static review / Backend03

2026-09-26 KST. PASS for the frozen capture candidate and plan. No remaining
concrete blocker found in this static scope. Execution, build and source-write
permission are separate gates; no runtime success is asserted.

Author Fermat directly confirmed final freeze. Reviewer read both files and
rehashed them after confirmation:

| Artifact | SHA-256 |
| --- | --- |
| BACKEND-OCR-001-native-apply-linux-capture-03.py | d0a8e756cdd4cafc394d12a68e527632365aeaf43f6d9ca8cc063763db21d7fd |
| BACKEND-OCR-001-native-apply-linux-plan-03.md | 4d655c861b205add420a33c317aae4605037b60ea02dac53ee087aa7a3b2d595 |

Activation PHASE-3-native-candidate-apply-01 was read. The parent-reported
PermissionDenied128 application failure remains unresolved: helper is still
ef7d7ffe6dbc0b8f620ae9416818614cf9aa9dc5ceb822fdee11d4feca76bec5 and test still
382257cfb9747b2fe9d7aa87fedd5d50d5f853745c483be5b1764c3c958ade1b by fresh hash
checks. No retry or alternative writer was used. Pure12 remain NOT_RUN/node absent.

## Resolved review finding

The preliminary script enforced L1 identity but accepted any self-consistent
helper hash. Reviewer sent this HOLD directly to Fermat. Final script also pins
W1 canonical LF identity 6129ff42c0789df51c105068cbda48d0b299885f53c491e7d3a777315661467c,
matching the parent's prospective-source identity, alongside L1 identity
52349c96c31b6c373d8d8c99471b21df64ea5dea4a0a77f52539a884492e0f02. The final plan
states these are prospective, not applied-source claims. This blocker is resolved.

## Reviewed gates

- Host raw/LF source verification precedes Docker. Inner PID1 verifies the same
  manifest and script before execing exactly the one shortpeak node. Both source
  candidates are independently hard-pinned; remaining raw/LF entries and manifest
  digest must be supplied through the later reviewed build/invocation inputs.
- Immutable new image ID is required; old a/b are rejected, --pull=never is set,
  and there is no build, tag fallback, retry or source-write action in the script.
- Launch uncertainty is published before create and remains through start,
  wait and removal. Failed/ambiguous list or inspect is not absence. Unknown-ID
  recovery only accepts the generated exact name, full ID and owner/nonce labels.
  Empty discovery after uncertain create cannot clear uncertainty.
- Inspect whitelists identity, resource/network and terminal state fields.
  No Config.Env, env-file, DB/model mount, privileged namespace or socket is used.
  Container is network-none, 512MiB with zero extra swap and read-only root.
- Natural wait and terminal inspection precede cleanup and are preserved.
  Forced stop explicitly changes disposition. Only the exact validated owned
  container may be stopped once, checked not running and ordinarily removed;
  failure overrides any tentative PASS. Command timeouts are bounded but do not
  claim daemon cancellation. Late/unresolved state remains for parent review.
- PASS needs natural observer exit0, one completed expected JUnit case with no
  skip/fail/error, mandatory cleanup property, fixed pressure dimensions,
  identity/attempt evidence, consistent observer endpoints below250ms, and the
  matched killed/denied oracle plus causal counter. Malformed/partial JUnit,
  observer death, nonzero exit, missing properties, forced stop, cleanup failure
  or source drift cannot return a successful scoped capture.
- OOMKilled is correctly treated as container-level activity: child death may
  coexist with surviving observer exit0. Observer death supplies no fabricated
  t1 or JUnit. This is a short-attempt witness, not universal victim attribution,
  completed over-limit RSS, production/model qualification or a Windows result.
- Evidence publication file-fsyncs before replace; POSIX-only directory fsync
  does not claim Windows directory durability. Outer host failure still needs
  parent evidence/residual handling as explicitly stated in the plan.

## Verification and remaining gates

Reviewer used only shell reads/searches/hashes and direct author coordination;
only this review file was written. No harness import, Python/pytest/native/API
probe, Docker/build/container, DB/model access or source/test edit. Parent reports
AST-parse-only PASS for the frozen script; this reviewer did not repeat it or
equate it with execution. An unrelated historical-directory search denial was
not bypassed.

Source application and pure12 HOLD remain unchanged. Later prerequisites are
authorized source recovery/application, reviewed applied raw/LF pins, separately
approved exact-source image build and frozen image ID, reviewed outer invocation
and explicit PM one-shot native approval. This static PASS does not grant any of
those actions, reset prior failure counts, authorize a retry or advance admission.
