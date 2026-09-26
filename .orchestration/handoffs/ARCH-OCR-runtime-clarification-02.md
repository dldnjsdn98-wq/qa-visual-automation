# Handoff

- Task / owner: P3-RUNTIME-001 contract interpretation / Architect02.
- Status: COMPLETE read-only clarification; no revision 3 proposed.
- Contract basis: accepted P3-OCR-v1 revision 2 SHA-256 `478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44`, sections 3 and 10.2.
- Input: Backend03 runtime addendum SHA-256 `aef7bea1af2d8c57938736be4ad8b95e6a7c4dc23e30d210ec314ce8c2274d18`.
- Changed files: this handoff and `.orchestration/reports/ARCH-OCR-runtime-clarification-02.md` only.
- Decision: 250 ms direct-child PID sampling is valid monitor-path evidence but insufficient to qualify the 2 GiB guarantee. The contract requires continuous OS-level enforcement or an equivalent proven mechanism; cgroup/Windows Job Object are practical implementations, not mandated names. Include descendants unless qualification proves none can exist.
- Deadline: 300 seconds is one absolute productive budget from claim. No phase or stop receives a fresh allowance. A small bounded post-deadline termination/reap tail is allowed only for containment under the contract's quarantine rule; it cannot renew, publish, finalize or continue useful work.
- Commit interpretation: the contract does not require PostgreSQL to finish an already issued, locked and validly fenced COMMIT before the caller's local second 300. A later acknowledgement/commit is resolved by fresh-primary recovery. After deadline, do not start/retry finalization; confirmed prior commit may stand, and uncertainty permits no compensating mutation.
- Authority: the adapter/attempt child may not own DB credentials or renew/stage/finalize/fail. Parent owns every DB mutation and ambiguity recovery. The observed Backend03 draft child-DB design conflicts with revision 2 and must be reworked or separately proposed as an exact contract revision.
- Parent DB wait: a parent-owned DB thread may outlive the productive deadline only to settle/recover one already issued operation. The runner stops child work and quarantines new claims/mutations. One fenced `ENGINE_TIMEOUT` failure is allowed only after confirmed child stop, no in-flight/uncertain mutation and a still-live fence.
- Minimum action: bounded terminable source reader; remaining-deadline stop/join; immediate expiry kill/quarantine; process/tree memory containment at or below 2 GiB; Windows/Linux short-peak/descendant/deadline/no-write tests.
- Tests: NOT_RUN by Architect02; read-only source/contract/hash inspection only. Existing owner tests were interpreted, not reclassified as independent acceptance.
- Acceptance: AC-P3-01..04 not re-evaluated. Product correction remains Backend03/PM scope.
- Revision threshold: revision 3 plus independent review only if the guarantee is weakened or its resource subject/metric is materially redefined. Current correction fits accepted revision 2.
- Requested model / actual: Sol high / unverified.
- Branch / commit: null / null.
- Next owner: Backend03 implements the activated bounded correction and supplies focused evidence; PM verifies and coordinates downstream affected verification.
