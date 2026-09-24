# REVIEW-ARCH-UPLOAD-001 / Reviewer 08 handoff

- Task/owner: REVIEW-ARCH-UPLOAD-001 / 08.
- Result: CHANGES_REQUESTED against P2-UPLOAD-v1 revision 1.
- Required finding: R08-P2-ARCH-001 - MAJOR / OPEN. Backend origin binding is required but no origin is persisted and no fail-closed comparison/migration exists. A spool for A can restart under B, accept B ACK, and become uploaded without delivery to A. Persisted ACK also lacks server provenance.
- Required fix: durable versioned canonical origin authority; atomic locked initialization; nonempty missing/corrupt binding and mismatch fail closed before state mutation, HTTP, or ACK recovery; immutable-v1 destination or exact crash-safe migration; preserve IDs/state/ACK/originals; add destination-change/restart/binding-crash tests.
- Architect binding.json proposal: directionally sufficient but unsubmitted and not revision 1 evidence.
- Hashes: contract ab53b327517e6fd24bbff4b08c56a4d64f6dbda1a25f34a436e575858854ea4d; API f494bfbfec6de2742312e1bc22e5aec7f93a714e37171965580e14ea81aa7443; flow d11a9ae800c9b8f5edd6ecb88c3e71638b918993abbd47798ac4fe7a6db02b18; domain 6365a75c80b3ed8fc7b812d1b79100dca7239552dfeea6eaf563ffc23c7d1065.
- No other blocker in receipt fencing, per-generation keys, ambiguous commit, cleanup, JCS/Unicode/manual wire, strict ACK, or Web metadata.
- Line 135 gives completed replay precedence over line 42 fenced-owner wording. Clarify, nonblocking.
- Queue clarification: list normal PENDING/RETRY_WAIT/FAILED restart and quarantine representation, nonblocking.
- PASS: explicit-root access; four hashes; independent 4-doc/11-link/5-JSON check; sections 1-10/F01-F24 and bounded JCS checks. Owner PASS remains Owner evidence.
- NOT_RUN: product API/DB/migration/storage/queue-crash/Web/build/full-RFC tests. AC-P2-01 through AC-P2-04 remain NOT_RUN.
- Difficulty/model: high; requested gpt-5.6-sol/high; actual unverified. Luna/high sidecar ended in 429 without result, execution-limit only.
- Changed files: Reviewer report and this handoff only. Contract/product/PM YAML/DECISIONS/mobile proposal unchanged.
- Branch/commit: null/null. No Commit/Push.
- Next: PM records CHANGES_REQUESTED; Architect submits revision 2 with exact hashes/evidence; PM reactivates Reviewer 08. Implementation remains blocked until acceptance and PM READY/file claims.

