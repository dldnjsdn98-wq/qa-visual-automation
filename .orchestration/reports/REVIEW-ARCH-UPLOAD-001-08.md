# REVIEW-ARCH-UPLOAD-001 / Reviewer 08 independent contract review

Date: 2026-09-25 KST
Reviewer: 08
Contract: P2-UPLOAD-v1 revision 1
Difficulty/model: high; requested gpt-5.6-sol/high; actual model unverified.

## Disposition

CHANGES_REQUESTED.

Required finding: R08-P2-ARCH-001 - MAJOR / OPEN - persist and enforce spool destination identity before queue mutation or HTTP.

AC-P2-01 through AC-P2-04 remain NOT_RUN. All implementation remains BLOCKED. PM alone owns YAML/AC/phase state.

## Exact snapshot

| File | SHA-256 |
| --- | --- |
| phase-2-upload-contract.md | ab53b327517e6fd24bbff4b08c56a4d64f6dbda1a25f34a436e575858854ea4d |
| api-contract.md | f494bfbfec6de2742312e1bc22e5aec7f93a714e37171965580e14ea81aa7443 |
| data-flow.md | d11a9ae800c9b8f5edd6ecb88c3e71638b918993abbd47798ac4fe7a6db02b18 |
| domain-model.md | 6365a75c80b3ed8fc7b812d1b79100dca7239552dfeea6eaf563ffc23c7d1065 |

The inherited cwd is old New project 2. All reads/checks used explicit C:\Dev\qa-visual-automation. The old checkout was not edited; Git protection was not bypassed.

## R08-P2-ARCH-001

Contract evidence in phase-2-upload-contract.md:

- Line 167 defines item layout/files and the lock.
- Line 173 requires Backend origin binding and explicit destination migration while forbidding endpoint data in the manifest.
- Line 181 defines the OS lock but no spool metadata authority.
- Line 189 fixes initialized.json to queue_state_version, client_upload_id, and manifest_sha256; no origin.
- Lines 191 and 213-220 allow restart send/ACK/move recovery without durable destination comparison.

Counterexample A: initialize spool S for Backend A; leave PENDING, RETRY_WAIT, or restartable IN_FLIGHT; stop; change config to Backend B; restart. Every defined local check passes because none records A. If B has matching scoped references, B can return valid 201 and satisfy strict ACK, moving the item to uploaded although A never received it.

Counterexample B: A succeeds and ACKED is durable before directory move; stop and change config to B; restart. Recovery validates ACK against the manifest, but state/ACK authority does not identify A, so local UPLOADED can be finalized under B configuration without proving which server owns the receipt.

Backend idempotency is database-local and cannot prevent cross-server redirection. Impact: cross-environment disclosure, duplicates, false local success/failure, and lost receipt provenance.

Required next revision:

1. Durable versioned spool origin authority, or equivalent per-item authority, with canonical Backend origin and no credentials.
2. Exact scheme/host/default-port/API-path/trailing-slash rules; reject userinfo, query, fragment, redirects, and unsupported paths.
3. Atomic first initialization under spool lock: temp write, flush/close, no-overwrite publish, directory durability where supported, readback. Nonempty missing/corrupt binding fails closed.
4. Compare configured origin before restart/send/retry/recovery and persisted-ACK recovery. Mismatch causes zero network and zero attempt/ACK/directory/protocol-authority mutation.
5. Exact destination changes. Acceptable v1: destination immutable per spool and new spool for new origin. If migration remains, define lock, eligible states, atomicity, crash recovery, rollback, ACK/history, and IN_FLIGHT unknown outcomes.
6. Deterministic tests for first init; nonempty missing/corrupt binding; A-to-B with PENDING/RETRY_WAIT/IN_FLIGHT/ACKED; binding/migration crash; no mutation/network on mismatch.

Architect's unsubmitted binding.json proposal is directionally consistent but is not revision 1 evidence. Revision 2 with exact hashes and focused re-review is required.

## Remaining areas
No additional blocking design finding.

Receipt/fencing: lines 110-127 define durable identity, 131-135 DB-time generation/token fencing, 140-148 per-generation keys and no worker deletion, 150-157 ambiguous-insert arbitration, and 161 exclusive receipt-aware cleanup. A stale generation cannot finalize or delete the winner. P2-RESUME-SERVER-0920 also found no static blocker. Actual DB concurrency/crash is future evidence.

Wire/JCS/manual: manual remains two multipart parts, 201, null ID, no replay header. Agent identity, strict ACK, safe Web metadata, Unicode, and JCS/binary64 are explicit. Line 42 broadly says fenced former owner gets 409, but line 135 resolves precedence: completed receipt replays 200; otherwise UPLOAD_IN_PROGRESS. Clarify line 42 in revision 2, nonblocking. JSONB/binary64 and full RFC 8785 are future implementation tests.

Queue/ACK: except for origin binding, marker-last publication, atomic state, OS lock, IN_FLIGHT restart, ACK-before-move, no-overwrite move, retry/backoff, requeue, and original retention are adequate. Nonblocking clarifications: list normal pending/PENDING, pending/RETRY_WAIT, failed/FAILED restart behavior; define quarantine representation. Existing rules already require no HTTP, reset, overwrite/delete, and original retention.

## Scenario coverage

All F01-F24 and all 25 uploader preparation scenarios were traced and remain planned, not product evidence.

| Scope | Coverage |
| --- | --- |
| P01-P07 | F02-F04 and marker-last |
| Q01-Q03 | OS lock/state recovery, F16/F19/F20 |
| R01-R05 | F01/F17 persisted retry |
| A01-A05 | F06/F07/F13/F18 strict ACK |
| S01-S03 | F19 ACK/state/directory recovery |
| I01-I02 | F13/F22/F24 future real integration |
| Destination restart | Missing; add R08-P2-ARCH-001 cases |

## Commands, attribution, limits

| Check | Result |
| --- | --- |
| Get-Location; Resolve-Path current root | PASS, Reviewer execution |
| Four SHA256 values | PASS against activation snapshot |
| Current state/activation/role/owner/preparation/contract reads | PASS static inspection |
| Independent Node cross-document checker | PASS: 4 docs, 11 local links, 5 JSON examples |
| Independent bounded contract/JCS checker | PASS: sections 1-10, F01-F24, JSON, UTF-16 order, -0, 1/1e0, Unicode, null/missing, five mutations, order-independent hash |
| Owner checker | Owner PASS retained separately, not relabeled |
| Support audits | Server/wire no extra blocker; claims planning only; Reviewer owns disposition |
| Luna/high sidecar | NOT_USED: 429 before result; execution limit, not product/model finding |
| Product API/DB/migration/storage/queue-crash/Web/build/full RFC | NOT_RUN by scope/gate |
| Git status | NOT_RUN final pass; no safe-directory bypass |

Independent synthetic fingerprint c62e5336cce686441f55f01eac056731ba9ad9f541082c090cf2423761e29bcf used different input from Owner 911d...; neither is product evidence.

## Changes and next action

Changed files: this report and .orchestration/handoffs/REVIEW-ARCH-UPLOAD-001-08.md only.
Contract/product/PM YAML/DECISIONS/mobile proposal: unchanged.
Branch/commit: null/null. No Commit/Push.

PM records CHANGES_REQUESTED and routes R08-P2-ARCH-001 to Architect 02. Architect submits revision 2 with exact hashes and targeted evidence. PM reactivates Reviewer 08 for focused closure. Implementation remains blocked until independent acceptance and PM READY.

