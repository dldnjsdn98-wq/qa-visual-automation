# Linux parent-OOM causal and lease-recovery evidence plan / Backend03

Status: IMPLEMENTED FOR PARENT SECURITY/SCOPE/NECESSITY REVIEW; NOT EXECUTED.

This sidecar owns only
`.orchestration/reports/BACKEND-OCR-001-native-diagnostic-parent-oom-03.py`
and this plan. It does not edit Backend source, tests, Worker05, shared state, or
existing evidence. It does not run the changed pressure test. Parent-reported
Linux results remain separate: one boundary pass, nine supervision passes, and
the pressure-first descendant early-ready correction currently under review.

## Exact frozen inputs and purpose

- Required tag: `qa-backend-ocr-native-diagnostic:20260925b`.
- Required immutable image ID:
  `sha256:56c45fb0dac074888d84484e414107c95342ab325e148c916fe55e454f1df662`.
- The tag must resolve to that ID, and every diagnostic container is launched by
  the ID after the check. A retag or source mismatch fails before DB creation.
- The exact-source gate includes the current corrected containment-test hash
  `382257cfb9747b2fe9d7aa87fedd5d50d5f853745c483be5b1764c3c958ade1b`.
  This is only an identity gate; the pressure test is not selected or executed.
- Purpose: distinguish a container parent killed by the aggregate Linux cgroup
  from a surviving runner that can classify and commit a failure. Parent death
  must leave generation 1 RUNNING with no error/result mutation. Recovery must
  occur only after the real PostgreSQL 60-second lease expires.

This does not qualify production admission, real OCR, models, the corrected
pressure slice, or the 2GiB production profile. It does not replace the frozen
103-source checkpoint or request a 279-test rerun.

## Why the existing test helpers are reused without pytest orchestration

The harness uses `runpy.run_path("tests/backend/test_ocr_jobs.py")` inside the
approved image and calls `_insert_run`, `_factory`, and `_rows`. This reuses the
contract-complete verification run/job shapes and ORM observations already used
by the PostgreSQL tests. It does not register the test module as a pytest plugin
or invoke a test node: pytest fixture teardown cannot run after PID 1 is OOM
killed, and its module-scoped random database name would not be known to the
host cleanup path. The harness therefore owns database creation/migration/drop
explicitly and inserts only the five minimal catalog parents directly.

No catalog schema is copied. The existing helper remains authoritative for the
screenshot, profile, run, job and attempt rows. The image source-hash gate makes
helper drift an explicit precondition failure.

## Reviewed one-shot protocol

1. The host validates the exact local source hashes, immutable image ID, running
   existing PostgreSQL container, absent unique container names, and a new
   evidence directory. It reads no `.env` value. Docker receives the existing
   `.env` through `--env-file`; evidence records neither its path nor values.
2. A setup container runs the same image with `--memory 512m --memory-swap
   512m --network container:<pinned-existing-postgres-id>`. It creates exactly
   `qa_backend_parent_oom_<32 random hex>`, migrates it, writes a singleton
   owner/nonce/database-name/database-OID marker inside that DB, and inserts the
   minimal catalog plus one helper-built PENDING job. It must exit with the job
   still PENDING/QUEUED generation 0, no lease and no attempt. Setup does not
   claim the job.
3. A fresh, named OOM container uses the same ID, cgroup limits, network
   namespace and unique database. It is not auto-removed. PID 1 itself calls
   `VerificationJobService.claim()`, retains that Claim/fence in the claiming
   process, proves generation 1 and an exact DB-derived 60-second lease, then
   closes its DB connection and starts one 1MiB `launch_contained` child. The
   child gets only `LANG`, `PYTHONDONTWRITEBYTECODE`, and
   `PYTHONUNBUFFERED`; it has no DB authority and blocks without productive
   work. Thus the process intentionally OOM-killed is the actual DB claim owner.
4. Before pressure, PID 1 verifies `memory.max=536870912`,
   `memory.swap.max=0`, fresh `oom/oom_kill` counters, the child wait marker,
   and no prior error/result. It atomically publishes and fsyncs
   `oom-ready.json`. PID 1 then retains and page-touches 16MiB anonymous chunks.
   A returned `MemoryError` is explicit failure, not OOM evidence, and is never
   retried by this harness.
5. The host waits at most 45 seconds, without issuing a host stop, then inspects
   only safe Docker fields. A
   causal pass requires the retained container's exact name/ID/labels/image,
   `State.OOMKilled=true`, `State.ExitCode=137`, `docker wait=137`, 512MiB
   memory and memory-swap values, and the exact `container:<postgres-id>`
   network mode. Docker environment/config values are never inspected. These
   are container-level OOM facts: together with the pre-pressure child-ready
   observation they prove PID 1 later died from the container OOM, but cannot
   independently prove the tiny child was not an earlier OOM victim.
6. After saving `oom-container-inspect.json`, the host verifies the nonce label,
   exact name and exact ID, then removes only that stopped owned container. It
   never stops, restarts, inspects credentials from, or removes PostgreSQL.
7. A recovery container uses read-only short connections to observe DB
   `clock_timestamp()` and the one exact job. It performs no mutation while the
   generation-1 lease is greater than DB time. Every observation must preserve
   the original lease and hashed fence identity from `oom-ready.json`. At real
   equality/expiry, it requires generation 1 still RUNNING/OCR/STARTED with no
   run/job/attempt error, result links or result rows, then calls the production
   `VerificationJobService.claim()` once.
8. Recovery passes only if generation 2 owns a fresh real 60-second lease,
   run/job remain RUNNING/OCR at generation/attempt 2, attempt history is
   `[EXPIRED(LEASE_EXPIRED), STARTED(no error)]`, no result links/rows exist,
   and both generation-1 `renew` and `stage` are rejected with `LostFence`.
   Thus the durable transition is lease takeover, not a fabricated clock,
   direct lease update, or a failure commit by a runner that survived the OOM.
9. Setup, OOM, recovery and cleanup are all detached named containers. The host
   marks the phase launch uncertain before dispatch, then pins each full ID and
   nonce labels before waiting. CLI timeout cannot lose authority: the host may
   recover an already-visible exact named/labelled identity and perform bounded
   stop/remove, but absence after an interrupted launch cannot clear uncertainty
   because creation may be late. DB deletion does not begin while any
   setup/OOM/recovery launch remains unresolved. Cleanup-launch uncertainty is
   retained as a residual cleanup failure.
10. The DB is dropped only when `database-created.json` and the live DB's
   singleton marker both match owner, invocation nonce, exact database name and
   pg_database OID. If create/marker publication is uncertain, including an
   existing-name failure, the DB is retained as unresolved. After all writer
   containers are confirmed terminal and removed, one owned cleanup container
   performs the exact `DROP DATABASE ... WITH (FORCE)` and verifies absence.
   There is no retry of setup, OOM, recovery, cleanup, image build, pressure,
   Docker permission, or test execution.

## Evidence and failure interpretation

The parent selects a new directory whose basename starts with
`BACKEND-OCR-001-native-diagnostic-parent-oom-evidence-03-`. The harness refuses
an existing directory. Expected records are:

- `manifest.json`: exact image/source/script identities, bounded phase exit
  codes, source stability and cleanup result; no command argv or env values.
- `database-created.json` and `setup.json`: owner/nonce/name/OID authority and
  an unclaimed PENDING generation-0 seed.
- `oom-ready.json`: PID 1 owner, tiny contained child PID and allowlisted env key
  names, fresh cgroup facts, PID-1 generation-1 claim, hashed fence identity,
  exact 60-second live lease and absence of results/error. Claim tokens are not
  written.
- `oom-container-inspect.json`: exact retained identity, OOMKilled, exit 137,
  limits and network mode. Environment inspection is explicitly false.
- `recovery.json`: first post-death observation, DB-clock expiry observation,
  generation-2 takeover, attempt outcomes and stale-fence denials. Tokens are
  used only in memory after reading this unique DB and are not recorded.
- `cleanup.json`: exact random database removal.

On Windows host writes, the harness file-fsyncs temporary content before atomic
replace but does not claim directory-fsync durability because Python/Windows
does not expose the POSIX directory fsync used by inner Linux modes. This host
limitation is recorded in `manifest.json`.

`OOMKilled=false`, any exit other than 137, host stop before the actual
`docker wait=137` gate, missing pre-OOM evidence, a child
that is not ready, early cgroup events, parent `MemoryError`, less than 45
seconds of live lease, pre-expiry mutation, a prior error/result, generation
other than 2, stale-fence acceptance, source drift, or incomplete cleanup is a
failure. The harness does not transform such a result into a surviving-runner
resource failure or a lease-recovery pass.

If `MemoryError` returns to PID 1, `handle.stop()` must prove cleanup before
`close()`. An unproven handle remains retained until the owned container is
confirmed terminal. A setup/recovery timeout never grants DB-drop authority.
Container existence uses only a successful, formatted exact-name Docker list.
Daemon, access or transport errors are ambiguous failures and are never treated
as authoritative absence.

## Proposed parent-reviewed command (not run by this sidecar)

Use the repository's existing Python environment. Replace only the already
known existing PostgreSQL container name and choose a fresh evidence suffix:

```powershell
.\.pytest_cache\agent-clean-win\Scripts\python.exe `
  .orchestration/reports/BACKEND-OCR-001-native-diagnostic-parent-oom-03.py host `
  --image qa-backend-ocr-native-diagnostic:20260925b `
  --image-id sha256:56c45fb0dac074888d84484e414107c95342ab325e148c916fe55e454f1df662 `
  --postgres-container <existing-postgres-container> `
  --env-file .env `
  --evidence-dir .orchestration/reports/BACKEND-OCR-001-native-diagnostic-parent-oom-evidence-03-01
```

Parent must review the destructive necessity before execution: intentional OOM
is limited to one disposable owned container; DB deletion is limited to the
random database created by this invocation; container removal is limited by
exact ID, name and nonce labels. The existing PostgreSQL container and shared
databases are outside cleanup authority.

## Execution status

NOT_RUN. This sidecar performed no Python harness execution, pytest execution,
Docker command, DB connection/mutation, image build, dependency operation,
model access, source/test edit, production admission, or 279-suite rerun.
