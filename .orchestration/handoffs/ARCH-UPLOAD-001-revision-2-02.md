# ARCH-UPLOAD-001 revision 2 / owner 02 handoff

Date 2026-09-25 KST. P2-UPLOAD-v1 document revision 2.
Status request READY_FOR_REVIEW; independent re-review pending.
Finding R08-P2-ARCH-001 MAJOR/OPEN: author correction submitted, no self-closure.
PM-approved scope: spool-origin binding sections7/8/9/10 and necessary three architecture references.
Difficulty highest; requested gpt-6-astra/medium; actual application unverified.
Branch/commit null/null; no Commit/Push.

Changed files: four contract paths below plus reports/ARCH-UPLOAD-001-revision-2-02.md and this new handoff. Existing rev1 author report/handoff are intact; exact original four-file byte snapshots are in the new report. Reviewer history, product, PM YAML/DECISIONS, mobile proposal untouched.

| File | SHA256 |
| --- | --- |
| docs/architecture/phase-2-upload-contract.md | e47d3dca18fef169600bf6bebe78a31432105e5a1ae5b80a9934e1bf4ee8f843 |
| docs/architecture/api-contract.md | abcab2109becbe6938628aa3810bc547a33a8b2cc23348c71d8688bf6e7a0e70 |
| docs/architecture/data-flow.md | 08cb9119712d4731830d6b5513b6c38a1857f04360c9595f9c6eddb8be4f6f86 |
| docs/architecture/domain-model.md | 4147fde8c52e084b974f2fbc0f9cde14d493bd1442d234f01be9bdfb51680c1a |

Fix: sole immutable spool-root binding.json, canonical origin/byte representation, explicit locked no-overwrite initialization, pristine inventory/partial-temp recovery, missing/corrupt/mismatch fail closed before any item mutation/network, revalidation at send and all ACK/recovery transitions. No in-place destination change or cross-server ACK transfer. Protocol/API/manual/fingerprint/Backend DB semantics unchanged; sections1..6 byte-preserved except revision header. F25..F30 added.

Counterexample A: A-bound PENDING/RETRY_WAIT/IN_FLIGHT under B -> zero HTTP/attempt/state changes. Counterexample B: persisted A ACKED under B -> zero move/finalization. Same-origin recovery remains valid. Current URLs use immutable validated origin plus fixed API paths.

Evidence: [new report](../reports/ARCH-UPLOAD-001-revision-2-02.md) includes executable read-only reference/static checkers, exact commands/results, prior snapshots and support integration.
PASS: 10 accepted/39 rejected origins, 9 init decisions, 27 failure-stage decisions, five A-to-B state counterexamples + same-origin recovery; scope/hash/link/JSON/trace checks and whitespace.
NOT_RUN: actual filesystem/concurrency/crash/HTTP/DB/Web/full RFC/product tests, independent acceptance.
Support: reused previous impact analysis; one HIGH Sol/high normalization/partial-init sidecar completed, parent integrated and verified; actual model unverified. No duplicate whole audit.

Remaining limits: process-crash guarantee not universal power-loss; unsupported external erased history cannot be detected; same-origin DB replacement outside destination-continuity guarantee. No new author-side required blocker; Reviewer retains closure authority.
JCS/common packaging selection remains separate PM-owned claim process; no dependency edits. Owner06 later implements/tests binding within existing exclusive scope. No backend/manual/frontend implementation expansion.

Next owner PM01: activate focused Reviewer08 closure on these hashes. All product work remains BLOCKED until independent acceptance + PM READY and file claims. AC-P2-01..04 NOT_RUN.
