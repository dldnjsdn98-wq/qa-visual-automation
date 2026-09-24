# REVIEW-ARCH-UPLOAD-001 revision 2 / Reviewer 08 focused independent review

Date: 2026-09-25 KST
Reviewer: 08
Contract: P2-UPLOAD-v1 document revision 2
Difficulty/model: high; requested gpt-5.6-sol/high; actual applied model unverified.

## Disposition

ACCEPTED.

R08-P2-ARCH-001 - MAJOR / RESOLVED. Revision 2 supplies a durable, immutable spool destination authority and fail-closed validation before network, queue progress, and persisted-ACK recovery. The two revision 1 A-to-B counterexamples no longer execute.

This is contract acceptance only. AC-P2-01 through AC-P2-04 remain NOT_RUN, no product behavior is marked PASS, and implementation remains BLOCKED until PM records this result, confirms exact artifacts/file claims, and promotes the dependent work.

Revision 1's CHANGES_REQUESTED result remains historical evidence and was not overwritten.

## Exact revision 2 snapshot

| File | SHA-256 |
| --- | --- |
| docs/architecture/phase-2-upload-contract.md | e47d3dca18fef169600bf6bebe78a31432105e5a1ae5b80a9934e1bf4ee8f843 |
| docs/architecture/api-contract.md | abcab2109becbe6938628aa3810bc547a33a8b2cc23348c71d8688bf6e7a0e70 |
| docs/architecture/data-flow.md | 08cb9119712d4731830d6b5513b6c38a1857f04360c9595f9c6eddb8be4f6f86 |
| docs/architecture/domain-model.md | 4147fde8c52e084b974f2fbc0f9cde14d493bd1442d234f01be9bdfb51680c1a |

All reads and checks used explicit root C:\Dev\qa-visual-automation because the inherited cwd is the old New project 2 workspace.

## Finding closure

The revision 1 defect was that no durable authority tied local queue state or a persisted ACK to Backend A. Changing configuration to Backend B could therefore redirect a PENDING/RETRY_WAIT/IN_FLIGHT send or finalize a previously persisted ACKED result without server provenance.

Revision 2 closes that defect:

- Section 7.1 makes captures/binding.json the sole destination authority. Its closed versioned schema, exact canonical bytes, narrow origin grammar, and alias rules avoid parser repair, credential/path/query/fragment ambiguity, and accidental equality through DNS resolution.
- Initialization is explicit and lock-protected. An absent final can be published only for an exactly pristine spool, through flushed same-volume no-overwrite publication and final readback. A lone exact temp has a bounded explicit-init recovery; final-plus-temp keeps the final authoritative. Missing final on a nonpristine spool and corrupt, unreadable, noncanonical, or mismatching final bindings fail closed.
- Section 7.2 validates the configured origin and final binding before discovery/recovery or mutation at startup, then retains immutable startup values. It requires revalidation before each IN_FLIGHT/count write, each HTTP attempt, every item/spool-progress mutation, ACKED, move, UPLOADED, and every recovery/requeue transition. A post-response binding failure leaves the counted attempt durable but prevents ACK persistence and movement.
- Request URLs come only from the immutable validated bound origin plus fixed paths and validated UUID components. Configuration is not hot-reloaded and manifests cannot override the destination.
- V1 has no in-place rebind, force adoption, destination override, or cross-spool ACK/item migration. A different destination requires a separate pristine spool; the old spool and ACK evidence stay with the original origin.

Counterexample A is resolved: for A-bound PENDING, RETRY_WAIT, or IN_FLIGHT state, configuration B fails startup equality before queue mutation or HTTP. Counterexample B is resolved: A-bound ACKED recovery under configuration B fails before move or UPLOADED persistence. The same A binding/configuration can still validate the ACK against immutable intent and complete recovery without a POST.

The guarantee is correctly scoped to cooperative protocol operations and process-crash behavior. External erasure/replacement of both binding and history and same-origin server-database replacement are explicitly outside the claimed guarantee; the contract does not pretend to detect them.

## Focused scenarios and trace coverage

| Scenario | Independent result |
| --- | --- |
| Empty pristine root / absent state directories | PASS contract: explicit init may safely create directories and no-overwrite-publish the final binding |
| Final absent, only exact regular binding.json.tmp | PASS contract: normal startup refuses; explicit locked init may discard only that temp and restart publication |
| Valid final plus temp | PASS contract: final wins; no promotion or replacement; unsafe temp type fails closed |
| Nonempty spool with missing final | PASS contract: BINDING_MISSING, retain evidence, no adoption/mutation/network |
| Corrupt/noncanonical/unsupported final | PASS contract: BINDING_INVALID, no rewrite or inference |
| Valid final with different configured origin | PASS contract: BINDING_MISMATCH even when spool is otherwise empty |
| PENDING/RETRY_WAIT/IN_FLIGHT A-to-B restart | PASS contract: no attempt/state mutation and no HTTP |
| ACKED/UPLOADED A-to-B restart | PASS contract: no ACK recovery, directory move, or final state write |
| Binding failure after response or before any later transition | PASS contract: previous durable state remains; same-origin replay can recover |
| In-place rebind, force adoption, or ACK transfer | PASS contract: prohibited for V1 |
| F25-F30 | PASS static coverage: each appears once and maps initialization, A-to-B states, missing/corrupt/temp matrix, transition guards, origin boundaries, and immutable destination semantics |

The generic “before EVERY item/spool-progress mutation” rule includes producer publication, state temp/replace operations, initialized marker creation, retry/failure/diagnostic/quarantine writes, ACK persistence, directory movement, and recovery/requeue writes. Opening the root lock is explicitly not item progress; binding bootstrap has its own inventory and publication rules.

## Regression comparison against revision 1 bytes

I independently decoded the four embedded revision 1 base64 snapshots from the owner report and verified each snapshot's stated SHA-256 before comparison. I did not treat the owner's checker as Reviewer evidence.

- Contract sections 1 through 6 are byte-identical between the verified revision 1 snapshot and revision 2. The compared slice is 25,571 UTF-8 bytes with SHA-256 d393c030ebf625cb728bcf32565c9c0d2738ed3c92bbd40dea14580304b9f868.
- data-flow.md differs on line 56 only: the contract link label changed from revision 1 to revision 2.
- api-contract.md differs on line 169 only: the same revision-link update.
- domain-model.md differs on line 52 only: the same revision-link update.
- Therefore the prior sections 1-6/API/manual/fingerprint/receipt/DB assessment is unchanged. Revision 1's nonblocking completed-replay precedence and queue-description clarifications are not reopened.

The historical Reviewer artifacts were read back unchanged:

- reports/REVIEW-ARCH-UPLOAD-001-08.md: aec4661e79e7a8628e4df49c6aba3659ce9d4fa78d7752eabc88e230de290c53
- handoffs/REVIEW-ARCH-UPLOAD-001-08.md: af0e5cf2af03fe1b4ea48283943fcecf976fdb3f786ff4c61be96085e2bb88c5

## Commands, attribution, and results

| Check | Result |
| --- | --- |
| Get-FileHash on the four submitted revision 2 files | PASS, exact submitted hashes above |
| Targeted section/term inspection with rg and numbered Get-Content | PASS, Reviewer inspection of sections 7.1, 7.2, 8, 9, and 10 |
| In-memory base64 decode, strict UTF-8 snapshot hashing, section slice comparison, and three reference line comparisons | PASS: four revision 1 snapshot hashes; sections 1-6 exact; one expected link-label line per reference document |
| Independent focused PowerShell decision model | PASS: 5 A-to-B states blocked; 52 failed-binding/stage combinations halted; 7 init/partial-init decisions; same-origin ACK recovery allowed; F25-F30 each present once |
| First draft of that model | HARNESS_ERROR: an unsafe-word substring assertion matched NO_REPLACE; corrected to exact expected outcomes and rerun PASS. This was not a contract/product failure. |
| git diff --check for the four submitted documents | PASS, exit 0 |
| Owner origin/init/static checkers | OWNER_PASS only; retained as supporting submission evidence, not relabeled independent |
| Actual uploader implementation, filesystem no-overwrite/concurrency/crash, HTTP, DB, migration, Web, manual smoke, full RFC parser tests | NOT_RUN: implementation is still blocked and this was a focused contract re-review |
| AC-P2-01, AC-P2-02, AC-P2-03, AC-P2-04 | NOT_RUN: architecture acceptance does not execute product criteria |

No IP connectivity checks were performed.

## Scope and next action

Changed files: this report and .orchestration/handoffs/REVIEW-ARCH-UPLOAD-001-revision-2-08.md only.

Product code, submitted contract/reference documents, mobile proposal, PM YAML, ACCEPTANCE.yaml, TASKS.yaml, PROJECT_STATE.yaml, DECISIONS.md, and prior Reviewer/owner artifacts were not edited.

Branch/commit: null/null. No Commit/Push.

Next owner PM01: hash/read this report and handoff, record revision 2 ACCEPTED and R08-P2-ARCH-001 RESOLVED while preserving revision 1 history, then decide coordinated dependent-task promotion and exact file claims. Product execution must test F25-F30 and all four acceptance criteria; no Phase 2 criterion or phase acceptance follows from this review alone.
