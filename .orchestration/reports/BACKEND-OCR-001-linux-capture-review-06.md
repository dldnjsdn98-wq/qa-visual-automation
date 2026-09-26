# Linux capture result independent review 06

Disposition: HOLD / UNPROVED_OWNERSHIP_OR_CLEANUP. The recorded harness attempt failed after container creation and before container start. No scoped L1 enforcement result, image-internal source verification, observer timing, OOM attribution or cleanup proof exists. The selected pressure test was NOT_RUN on this recorded command path. Review role requested: reused Mill Sol/high; actual model identity not attested.

Authority: PHASE-3-linux-capture-01.md; parent completion notice explicitly prohibits additional Docker operations. This review reads completed evidence only; it does not query the residual container.

## Exact evidence reviewed

Paths below are relative to .orchestration/reports/. SHA-256 values were independently computed from the completed files.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| BACKEND-OCR-001-linux-capture-outer-06/command.json | 952 | 87378e7169e9db4426429bfbf83eacf8e5602e6a0edc19364c7d2a83726525df |
| BACKEND-OCR-001-linux-capture-outer-06/preflight.json | 363 | c7f42e8ef0564c1f6c915fa6caa6a145c11e16248f337d5e453fea1050d8fdf8 |
| BACKEND-OCR-001-linux-capture-outer-06/result.json | 1310 | 7e431dd0f31897e2dafab0a33a774b836cb3068e0df1a6b550e4d08822c14b68 |
| BACKEND-OCR-001-linux-capture-outer-06/stdout.log | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| BACKEND-OCR-001-linux-capture-outer-06/stderr.log | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| BACKEND-OCR-001-native-apply-linux-evidence-03-06/capture.py | 16815 | d0a8e756cdd4cafc394d12a68e527632365aeaf43f6d9ca8cc063763db21d7fd |
| BACKEND-OCR-001-native-apply-linux-evidence-03-06/source-pins.json | 25270 | d92e20493eb42a3d4d2702b17c3d5559c17cad78e31b364387039e649146f2bc |
| BACKEND-OCR-001-native-apply-linux-evidence-03-06/manifest.json | 57056 | cd519e114459fe5ee07967b9a536fd8ae4660a6514762f183df61e4008381eb5 |

Outer command/result agree on one attempt, approved interpreter with -E -B and optimize0, frozen capture/pins, expected fresh evidence destination and image sha256:a1337c5556ab00f01dac45075f6bbf71ba9198c1b179a83d0210e5879a426d0a. Preflight records113 host raw/LF matches and previously absent output. Actual outer result records capture-process exit2, elapsed1.063s and unchanged script/pins. Parent separately reports tool-shell exit1; it is not the capture-process exit or a container exit. No container exit137 is recorded. Empty outer logs do not mean success: Docker errors were captured inside manifest command entries.

## Recorded actual behavior

Exactly five commands are recorded in sequence:

1. Image whitelist inspect: exit0, exact authorized image and linux/amd64.
2. Exact generated-name container listing: exit0, empty before creation. This is not post-creation absence or cleanup evidence.
3. One docker create: exit0, full ID affc94c2fe2468fd867c1e80be5878836a9b70868e68f2bff4f54d9c84988e8a. Requested name qa-l1-3e363b492d1347efbbae6d4de1541353; owner BACKEND-OCR-001-L1-capture-03; nonce 3e363b492d1347efbbae6d4de1541353. Requested flags match reviewed image,512MiB memory/no extra swap, network none, read-only root,128MiB tmpfs, evidence-only mount and fixed synthetic environment. These are command arguments, not successfully inspected configuration facts.
4. First owned-ID inspect: exit1, Go-template error.
5. The finally-path owned-ID inspect: exit1, same error. This is the existing scheduled cleanup path, not a second capture/create attempt.

No start, wait, stop, rm or logs command is recorded. Manifest retains launch_uncertain=true, cleanup_confirmed=false, stop_requested=false and RuntimeError for both operation and cleanup. The create receipt is positive evidence of creation, but returned labels/state/configuration were never validated. Residual ownership/state/removal remains unresolved; the review neither assumes it is running nor claims it is absent or stopped. Any later inspection/cleanup needs separate PM authority.

## Cause and static-review miss

Both inspect records contain owner/nonce expansions of the form `{{json index .Config.Labels "qa.visual.owner"}}`. Docker reports `wrong number of args for json: want 1 got 3`. The generated template passes index and its operands as separate arguments to json instead of grouping the index expression. This explains both failed inspections and the failure before start, consistently with frozen source control flow.

My earlier static capture review missed this Go-template composition defect. Reviewing ownership logic and Python syntax did not establish the embedded Go-template semantics; the earlier no-blocker judgment was incorrect on that point. Source-pin completeness does not validate the template. A grouped index expression is the conceptual correction, but no correction has been applied or executed and no proposed replacement is approved by this report. Historical files remain unchanged.

## Evidence limits and source consistency

Independently compared all113 entries and both raw/LF hashes in recorded source_before and source_after against the exact pinned snapshot:113/113 match with no differences; manifest source_unchanged=true. This review verifies recorded source equality, not a new live-source scan or an atomic filesystem history.

Evidence directory contains only capture.py, source-pins.json and manifest.json. No inner-inputs.json, result.xml, terminal.json or container.log exists; manifest artifacts is empty. Thus there is no image-internal113 verification, completed JUnit/oracle/properties, observer t0/t1, headroom/attempt/PID witness, enforcement cause, State.OOMKilled, natural container exit, or proven owned-tree/container cleanup. Missing files cannot establish cleanup. This is a harness lifecycle failure, not a measured pressure-enforcement failure or observer-OOM finding.

No PASS_SCOPED_L1, qualification,250ms guarantee, production admission or AC promotion follows. Original Windows native3/historical cleanup2 counts remain unchanged;04/08/admission and further execution gates remain held.

Only this new review file was written. Performed read-only evidence inspection, JSON comparisons and artifact hashing. No Docker query/removal, duplicate run, native/test execution, harness import, DB/model access, source/author edit or repair was performed. Parent reports PM was notified of the unresolved residual. No further operation is authorized by this review.
