# Windows owned-process identity diagnostic proposal / Backend03

Status: READ-ONLY ANALYSIS COMPLETE; instrumentation and execution pending parent review.
Authorization: PHASE-3-native-diagnostic-resume-01.md. Requested Astra/medium;
actual runtime model unverified. No native execution, network access, test run,
helper edit, privilege/settings change or checkpoint replacement in this step.

## Preserved evidence and observations

- Preserve the 103-source/50-artifact checkpoint and reported 279 PASS/15 SKIP.
- Current helper SHA256: ef7d7ffe6dbc0b8f620ae9416818614cf9aa9dc5ceb822fdee11d4feca76bec5.
- Current containment tests: 9b1ac57bd2b02518d00524dd1e93a1f1ee9e60eaf5dcabb6f63285a997101c3e.
- Diagnostic02 XML: f424b1b8c6e7635bd114b978003973c1982a4ad80862c5b7ec97f85f1353b37d,
  in the existing runtime-conformance-evidence-03 directory. Do not overwrite it.
- Initial suspended accounting reported ActiveProcesses=1. At the marker, both
  basic accounting and the class-3 PID list reported two live processes:
  31428 (CreateProcess PID) and 109892 (identity unknown). TotalProcesses=2.
- Basic accounting is 48 bytes, DWORD=4, pointer=8, ActiveProcesses offset=40;
  returned length=48. This is not evidence for an ABI-layout correction.
- Job flags 8712/0x2208 contain active-process-limit, job-memory and kill-on-close;
  queried active-process limit=1, hard working-set flags=6, maximum=268435456.
- Cleanup reported ActiveProcesses=0, confirmed stop in approximately 0.016s.
  Native-accounting same-cause count remains TWO; previous cleanup count TWO is
  separate. Changed diagnostic framing does not reset either count.
- pyvenv.cfg names the bundled base interpreter. Earlier static disk inspection
  distinguished its Py_Main/python312.dll executable from the venv executable
  containing venvlauncher/CreateProcessW. This does NOT prove which executable
  actually ran in diagnostic02: its launch argv and process image were absent.

## Missing facts and source analysis

The current test selects sys._base_executable, but records only the outer pytest
command. Its marker contains "ready", not the writer PID. The helper records
CreateProcess PID and job counts but not process images, creation times, parent
PID, actual job membership for each returned PID, or the originating process.
Thus two real PID-list entries do not yet establish their ancestry or roles.

The source creates an unnamed non-inheritable Job, limits inherited handles to
three stdio handles, creates suspended, assigns the process, installs/queries the
hard working set, then resumes. There is no requested second Python process in
the basic workload. No source-supported correction to flags, struct packing,
active-process limit, or executable selection is justified yet.

Hypotheses to distinguish, not conclusions:

1. The selected executable is still a redirector or runtime bootstrap: the
   self-reporting Python PID differs from CreateProcess PID and its parent/image
   identities explain the additional process.
2. An implicit runtime/OS helper joins the owned Job: Python self PID matches
   CreateProcess PID, while the second image and parent identity differ.
3. Enclosing-job/nested-job accounting or incorrect handle use changes observed
   membership: exact owned-Job membership, same-handle query history and baseline
   parent-in-job facts distinguish this from an ordinary descendant. A boolean
   outer-job observation alone cannot establish the complete Job hierarchy.
4. A process exits during observation: creation-time-pinned handles and recorded
   query failures distinguish a race from PID reuse or a fabricated identity.

## Proposed materially changed diagnostic (one invocation after review)

Keep the same 256MiB cap, active-process limit ONE, no breakaway, hard working-set
flags, inheritance whitelist and suspended setup. No pressure, model imports,
DB operations, service changes or alternative host identity. Use one fresh
test-owned scratch directory and a new evidence namespace chosen by the parent.
Do not rerun the old pytest node as the new experiment.

The parent-owned diagnostic harness launches a stdlib-only direct-interpreter
identity workload with -I -S. Before launch, record the exact absolute application
argument and command line for this synthetic workload, resolved image path,
file SHA256/size, interpreter selection inputs, pointer width, OS build and
allowlisted environment KEY NAMES only. Never dump ambient environment, Docker
configuration or credentials. Path/hash capture is evidence, not a replacement
for the actual process-image query.

Replace the fixed marker workload with two explicit gates:

- At entry, atomically publish a bounded JSON identity record containing
  os.getpid(), os.getppid(), sys.executable, sys._base_executable, isolation flags
  and a harness-supplied nonsecret nonce; wait for one input byte.
- After the parent captures the first identity/membership snapshot, a single
  gate permits the same tiny pathlib marker action as diagnostic02, then a
  second identity marker; wait for termination. No further useful work.

If the first snapshot already violates containment, capture the scoped facts
and terminate immediately WITHOUT releasing the second gate. Do not suppress
the error in order to finish the protocol. A changed workload may remove the
symptom; one clean observation is not root-cause resolution or qualification.

Proposed helper instrumentation, ONLY after parent approval:

1. Record bounded immutable snapshots after CreateProcess (still suspended),
   after Job assignment/limit query, and immediately after ResumeThread; record
   requested flags, ResumeThread return, timestamps, process/thread IDs, Job
   handle lifecycle identifier and stdio whitelist metadata. Handles are local
   evidence only, never public API values or reopened after close.
2. Use the existing process handle to query GetProcessId,
   QueryFullProcessImageNameW, GetProcessTimes and IsProcessInJob(owned_job).
   Record whether the diagnostic parent is in any Job and in THIS owned Job;
   do not inspect unrelated Job objects or change membership.
3. For at most the first four PIDs returned by THIS Job's class-3 query, open
   only PROCESS_QUERY_LIMITED_INFORMATION|SYNCHRONIZE handles, revalidate exact
   Job membership and GetProcessId, and record image, creation time and exit
   status. Retain handles only through the bounded observation/cleanup scope.
   Access denial, disappeared PID, unexpected count or buffer overflow is
   explicit unknown evidence, not grounds for elevation or repeated querying.
4. Parent PID is supplied by the child self-report for the Python process.
   For a non-reporting second PID, propose a narrowly scoped
   NtQueryInformationProcess(ProcessBasicInformation) on its already validated
   owned handle, with explicit pointer-sized signature/layout and return-length
   checks. This API choice requires review; if unsupported/denied, record parent
   identity unknown. No global Toolhelp/WMI process enumeration, memory reads,
   command-line scraping or opening the returned parent PID. No PID-based kill.
5. Capture raw class-1/class-3 results and exact Job membership on the same
   retained handle. Record before/after counts because separate OS queries are
   not an atomic snapshot. Drain bounded completion notifications as supporting
   evidence even if the limit check fails; notifications are not guaranteed.
6. Store diagnostic facts in containment_info and on any setup exception so
   failures before handle return are captured. Preserve original exception,
   cleanup_confirmed and workload_started. Never convert an anomaly into safe
   ENGINE_UNAVAILABLE or ignore it to return a runnable handle.

## Bounds, cleanup and result interpretation

Parent harness gives entry/observation at most 5 seconds total and uses the
existing single 2-second containment-only stop tail. At most four member handles
and a fixed-size record per stage; one snapshot per gate/anomaly, no polling
process enumeration. OS metadata calls are synchronous and cannot promise a hard
wall-clock bound: if a diagnostic query stalls, the independent supervisor must
still stop the owned Job and record the observation thread as unresolved. No new
mutation/work or next launch under unresolved state. The parent should reject
the implementation before execution if this separation is absent.

Terminate ONLY through the owned Job handle; prove owned direct-process exit and
Job ActiveProcesses=0, close diagnostic handles, capture before/after evidence
in finally. A second process may be inspected only after owned-Job membership
validation; never terminate a process merely because its PID appeared in a stale
list. No host process cleanup. If stop is unproven, quarantine and retain evidence.

Interpretation matrix:

- Different self-report PID, image/parent linkage consistent with redirector:
  propose exact direct-executable correction with provenance; do not raise limit.
- Same Python PID plus identified helper: investigate documented creation/Job
  semantics before proposing any correction. Do not exempt it from RSS accounting.
- PID not confirmed in this Job or query ambiguity: retain unavailability and
  investigate handle/query provenance; do not infer unrelated process ownership.
- Two proven members under limit1 again: this is another same-cause failure,
  pause the Windows lane for reassessment even though new facts were collected.
- One member: record the new facts and non-reproduction; Windows remains
  UNAVAILABLE until the previous discrepancy is explained and reviewed.

## Review and ownership gate

Parent reviews this proposal before helper instrumentation. This lane may edit
only ocr_containment.py after that approval; the harness/tests/capture namespace
remain parent/test-owner work. Parent executes and captures exactly one reviewed
diagnostic; no execution by this lane, unchanged third probe, hidden retry,
network-permission retry, limits relaxation or host configuration change.

Linux work proceeds independently. Production admission, affected Web04 and
Reviewer08 remain blocked. Native qualification/pressure/real OCR are NOT_RUN in
this lane. This plan is not an acceptance result.

## Concrete optional instrumentation interface / parent review

Parent has authorized instrumentation only after documenting its rationale. The
rationale is the missing identity link: diagnostic02 proved two Job members but
did not identify the marker writer, actual process image or second member's
parent. Counts, limits and ABI are already evidenced; repeating them alone is
not useful. This addition must not change flags, limits, resume/stop decisions,
exception classification or production admission.

Proposed private-module surface (existing launch_contained signature unchanged):

```python
@contextmanager
def windows_diagnostic_capture(*, record_limit=8, member_limit=4):
    # Thread-local opt-in, entered IN the thread calling launch_contained.
    # Yields a capture object with snapshot() -> JSON-safe copied dictionary.
    # No native query in __enter__/__exit__, no exception suppression.
    ...

handle.diagnostic_snapshot(stage: str) -> dict
# Windows diagnostic opt-in only; stages live_gate/anomaly/before_stop/after_stop.
# Read-only, synchronous, at most one outstanding snapshot per handle.
# Called by the diagnostic observer thread, NEVER the termination supervisor.
```

The capture is explicitly retained by the harness before launch. It therefore
remains available if launch has not returned or raises. Its copied schema is also
attached as exception.containment_diagnostics on setup failure and as
containment_info["native_diagnostics"] when an owner exists. A native query error
is recorded with an operation/code; it does not replace the original failure,
grant cleanup proof or become a successful diagnostic. No environment-variable
activation, callback executing arbitrary caller code, unbounded event queue or
new public Backend/API endpoint.

Internally, opt-in stage snapshots are recorded at the existing suspended-created,
assigned-capped and resumed locations; the same existing calls proceed in the
same order. The observation itself adds latency and is included in the harness's
5-second observation budget. Record allocation uses fixed caps. The first anomaly
is retained without replacement, even after shutdown snapshots.

```text
schema_version: 1
capture_id: harness-independent random nonsecret identifier
limits: {record_limit: 8, member_limit: 4}
launch:
  application_argument, executable_size, executable_sha256
  process_id, thread_id, job_handle_local_id, process_handle_local_id
  requested_creation_flags, requested_job_flags, active_process_limit
  parent_pid, parent_in_any_job, parent_in_owned_job
  stdio: {inherited_handle_count: 3, attribute_handle_list_present: true}
records[]:
  sequence, stage, begin_monotonic, end_monotonic
  class1: {begin/end, succeeded, returned_bytes, raw_hex, values, error}
  class3: {begin/end, succeeded, returned_bytes, assigned, listed, pids, error}
  members[]:
    listed_pid, handle_pid, creation_time_100ns, exit_time_100ns
    image_path, image_basename, image_file_sha256, image_file_size
    owned_job_before, owned_job_after, creation_time_after_100ns
    parent_pid, parent_query_status, parent_query_returned_bytes
    status: confirmed_owned | exited | membership_changed | inaccessible | unknown
    errors[]: {operation, winerror_or_ntstatus}
  errors[], truncated, non_atomic: true
first_anomaly_sequence: integer | null
observer: {pending, failed, observation_budget_expired}
```

The image hash describes the file read from the observed image path, not a hash
of loaded process memory. Report file metadata before/after hashing and mark it
unstable on change. Do not hash an arbitrary caller-provided path as proof of
actual PID identity. Missing hash is explicit unknown; no network shares or
unbounded executable reads (local regular PE, bounded file size only).

Implementation ownership rules:

- Open only PIDs returned by this retained Job's class-3 query; verify owned-Job
  membership immediately on opening BEFORE image/parent detail inspection.
- Validate GetProcessId and creation time on the retained handle before/after
  inspection. Membership loss or exit is evidence, not authority to reopen/kill.
- Retain no more than four diagnostic member handles through snapshot completion;
  close in finally. On a blocked observer retain its ownership record and keep
  the parent quarantined. The stop path never waits for its Python lock.
- Keep the Job handle and process handle open while a query is outstanding;
  owner.close must not discard handles used by an observer. The harness joins
  the observer before normal close; an unresolved observer retains the owner.
- Optional parent query uses only the already membership-validated handle with
  explicit pointer-sized ProcessBasicInformation layout. Unsupported API or
  insufficient rights yields unknown; no access upgrade, global enumeration,
  opening parent PID or command-line/environment inspection.
- Capture partial stage records before any optional metadata query. On setup
  stall the harness retains capture/owner state; instrumented launch does not
  falsely claim a returned process or complete cleanup.

Harness contract for Fermat: create capture in the launch thread, expose its
object to the supervisor before launch, execute exactly one launch, consume
bounded atomic identity markers with nonce validation, request at most live-gate
and anomaly snapshots, stop the owned workload exactly once, preserve finally
records even on failure. There must be an independently available owned-Job stop
route during a suspended-setup diagnostic stall; this prerequisite needs concrete
implementation review before execution. If it cannot be supplied without changing
launch control flow, omit blocking setup metadata queries and record only local
already-returned facts at those stages. Do not introduce a hidden second stop.

This interface is proposed for review, not yet implemented. Parent instrumentation
authorization does not authorize native execution by this lane or an unchanged
third test. Fermat receives the agreed implemented surface before writing tests.
