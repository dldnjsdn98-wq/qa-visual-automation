# L1 retained-container capture candidate / Sol high / Backend03

PREPARATION ONLY / NOT EXECUTED. PHASE-3-native-candidate-apply-01 permits this
own-evidence candidate, not Docker/image/native execution. Parent reported exact
source application PermissionDenied; this candidate does not assume application
succeeded, retry any write, or change ACLs. Product/tests remain parent-owned.

Frozen script: `BACKEND-OCR-001-native-apply-linux-capture-03.py`, SHA256
`d0a8e756cdd4cafc394d12a68e527632365aeaf43f6d9ca8cc063763db21d7fd`.
Independent Mill review and later explicit PM execution/image-build approval are
required. This document does not assert a future image already exists.

## Exact prospective selection and pins

Exactly one pytest node:
`tests/backend/test_ocr_containment.py::test_native_pressure_and_owned_tree_cleanup[shortpeak]`.
The twelve pure oracle cases are parent-owned separate evidence, not selected here.
No descendant/mapped/parent-OOM/real-model or full279 rerun.

The approved L1 source has canonical LF UTF-8 SHA256
`52349c96c31b6c373d8d8c99471b21df64ea5dea4a0a77f52539a884492e0f02`.
The approved W1 helper canonical LF SHA256 is independently hard-pinned to
`6129ff42c0789df51c105068cbda48d0b299885f53c491e7d3a777315661467c`, from the parent's
native-candidate-windows-static-01.json. A self-consistent manifest with the old
helper cannot pass. Both prospective hashes refer to approved changes, not an
assertion that either source file has actually been applied.
Raw source bytes may differ by CRLF; a reviewed immutable input JSON must provide
BOTH exact raw SHA256 and canonical LF SHA256 for every pinned source. No source
normalization/write occurs. Schema:

```json
{
  "schema_version": 1,
  "files": {
    "tests/backend/test_ocr_containment.py": {
      "sha256": "<parent-approved actual applied raw bytes, 64 lowercase hex>",
      "lf_sha256": "52349c96c31b6c373d8d8c99471b21df64ea5dea4a0a77f52539a884492e0f02"
    }
  }
}
```

The example is schematic, NOT a runnable manifest. Required additional entries:
backend/app/workers/{ocr_containment,ocr,ocr_source,ocr_runtime}.py,
tests/backend/conftest.py, backend/requirements.lock, backend/Dockerfile.test,
pyproject.toml. Parent supplies other relevant frozen Backend/Worker/test sources
as part of its reviewed build identity (up to128 entries). Hidden files, parent
traversal and paths outside backend/tests/worker or pyproject.toml are rejected.
No environment/credential file is read or passed. The input file's raw SHA256 is
a required independent CLI pin; the image ID is a required immutable sha256 value.

Parent must supply the NEW exact-source image after separate build authorization,
with its build provenance checked against these pins. Old images a/dc9828... and
b/56c45fb... are expressly rejected. Script does not build, pull, choose a tag,
guess a replacement image or retry. Image inspect must match supplied ID/Linux/
amd64. Host source verification precedes any Docker command; the single launched
PID1 verifies the same source bytes inside /app BEFORE execing the test. Thus an
unapplied/partially applied L1 source stops this candidate before native dispatch.

## Concrete future invocation shape (not run)

Use the already approved host interpreter; no absolute system-Python path is
embedded or recorded. Invoke the frozen script with `host`, then:

- `--image-id <NEW reviewed sha256 image ID>`
- `--source-pins <reviewed immutable source-pin JSON>`
- `--pins-sha256 <that JSON's raw SHA256>`
- `--evidence <NEW absolute or repository-relative directory>`

Evidence must be a new direct child of .orchestration/reports whose name starts
BACKEND-OCR-001-native-apply-linux-evidence-03-. Parent captures this outer command,
stdout/stderr/exit and exact script/input/source identities in a new namespace.
This remains a proposed invocation, not execution permission.

## Lifecycle and resource ownership

1. Verify exact source/input pins. Create only the new evidence directory and
   immutable script/pin snapshots there; publish manifest with random nonce/name.
2. Inspect only the specified image. Query only the exact generated container
   name. A Docker list failure or malformed identity is unknown, never absence.
3. Set launch_uncertain BEFORE one docker create. Command uses --pull=never,
   --init=false, explicit python entrypoint, network none, read-only root,
   536870912-byte memory/memory-swap (zero extra swap), bounded128MiB tmpfs /tmp,
   and the one evidence bind mount. No env-file, DB/model mount, socket, privilege,
   host namespace, OOM tuning, security setting or dependency modification.
4. Pin ID/name/owner-label/nonce and image/resource/network settings using a
   whitelisted formatted inspect. One docker start only. The initial Python
   uses -I -S to verify pins, then os.execv to pytest; observer remains PID1.
   Child containment and its allowlisted DB-free environment remain unchanged.
5. Wait45s for natural container exit. Save safe terminal State/OOMKilled/ExitCode,
   timestamps, exact image/resource/ownership facts BEFORE stop/removal. No --rm.
   Capture fixed synthetic stdout/stderr; command records retain exact argv,
   monotonic start/end, CLI status and output. Raw Config.Env is never queried.
6. In finally, resolve only a visible exact named/labelled owned ID if launch
   reply was uncertain. Empty lookup does NOT clear launch uncertainty: daemon
   creation may still be late. No create/start retry. Ambiguous lookup retains
   unresolved state, no unrelated cleanup. For proven ownership, one stop with
   --time2 only if running (CLI timeout10s), confirm not running, then one ordinary
   rm by exact ID. No --force, second stop or second removal. Cleanup failure
   overrides any L1 PASS and is recorded for reassessment.
7. Reverify host sources and script/input snapshots; save artifact hashes and
   final manifest. Directory fsync is POSIX-only; host Windows directory durability
   is explicitly not proven. Evidence-write/host-process failure cannot be made
   durable by this script; parent retains outer capture and owns residual review.

Docker calls have per-command timeouts: create30s, wait45s, others10s. A timeout
kills the CLI wait only, NOT the daemon operation; ownership stays uncertain until
proved cleanup. No universal cancellation guarantee is claimed. There is no new
timer process or monitor thread. A stopped disposable container is the ultimate
cleanup boundary, independent of an in-container observer/child failure.

## Survival, results and attribution

The host is outside the pressure cgroup. A natural PID1 exit0 plus exactly one
expected JUnit case with no skip/fail/error is necessary but insufficient for PASS.
The capture additionally validates L1 verdict, identity/attempt facts, unchanged
320MiB+224MiB construction, same-observer t1-t0 strictly below250ms, correlated
oom_kill+owned child exit-9 OR oom+explicit denial, and confirmed owned-tree cleanup.
Exact-source inner-input evidence must identify observer PID1 and the selected node.
All container cleanup and source-stability checks must also succeed.

An observer death/nonzero exit, missing/partial JUnit, skip, malformed evidence,
timeout, source mismatch or forced stop cannot produce PASS_SCOPED_L1. A dead
observer supplies no invented t1, duration or replacement JUnit. Original partial
files are retained and independently hashed. `UNPROVED_OBSERVER_EXIT` is not a
claim that every nonzero exit was OOM; actual Docker fields and any raw JUnit
remain the evidence. Forced stop is separately UNPROVED_FORCED_STOP. An existing
failure record is not transformed into a passing pressure result.

Docker OOMKilled may describe cgroup OOM activity, including target child death.
It is not alone proof that PID1 died. A surviving pytest observer's exit0 and
complete verified L1 record distinguish the child-kill witness. Conversely,
exit137/OOMKilled does not provide missing child timing or victim ordering.
No completed over-limit RSS, universal250ms SLA,2GiB runtime, model qualification,
Windows result, production admission or overall AC acceptance is inferred.

## Preparation evidence and remaining gates

Only this plan and own capture .py were written. No script import/run, Python/AST,
pytest, Docker, image build, native probe, DB/model access, source/test change,
permission retry or host change was performed. SHA256 was read statically.
Parent separately handles AST/independent review and any approved source recovery.
Actual source application, frozen pin input, new exact-source build, reviewed
outer invocation and explicit PM native approval are all still prerequisites.
No automatic retry, size/headroom tuning, L2 substitution or old-image fallback.
