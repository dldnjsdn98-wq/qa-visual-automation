# Observer focused test proposal / Descartes09

Status: HOLD pending PM source disposition, 2026-09-26 KST. Requested Sol/high; actual model unverified. No commit.

Parent-provided interpreter metadata: approved Python 3.12.14, pytest 9.1.1. Installed SQLAlchemy 2.0.54 differs from lock 2.0.52; installed psycopg 3.3.6 differs from lock 3.3.5. These facts were supplied by parent, not queried by this lane. No dependency mutation. Any future re-export capture on this interpreter must preserve the mismatch limitation and cannot establish locked-runtime parity.

Earlier admission work is complete and frozen with no unresolved sidecar edit. Parent conformance report records windows-admission-api-02 25PASS after the unique-ID fixture correction; this is parent evidence, not execution here.

Read AGENTS.md, PHASE-3-linux-observer-refactor-01.md and the complete Architect headroom reassessment. Coordinated directly with Fermat 01a0d854-c4be-7931-b5bb-9a02c96b8a99 and Galileo 01a0d859-e6ca-71b3-af26-fe3a013a44f8. Fermat reports first ordinary helper creation denied, runner write never reached. Galileo reports no writes, interfaces proposal-only. Do not retry helper creation or use an alternate writer.

## Actual writes and dependency hold

Before the parent's hold arrived, one successful apply_patch created tests/backend/test_ocr_child_environment.py. It remains untouched after the hold, as instructed. SHA-256: 66ee202f0843064138f87456d54002062ad6fa752d4e9e755c1d603a00dcc85b. This file is an authored draft, not executable capture-ready evidence: backend/app/workers/ocr_child_environment.py is absent. No other product file was edited by this lane. The later candidate and this report are authorized evidence-only writes.

No write denial occurred in this lane. Broad report discovery encountered access-denied historical report directories; searching those locations stopped, with no retry, escalation or alternate access. Subsequent reads used named readable files. Existing files were not rolled back.

Source attempt accounting: one test-source creation attempt, successful before the hold; zero helper/runner source attempts; zero source attempts after the hold. Do not describe this lane as sourceattempts0 or the new test as absent. The candidate report-path file now contains the full environment/re-export test draft as proposed bytes plus static AST-review assertions, with no copied implementation. It has not been imported or executed.

Original successful operation provenance: functions.exec awaited tools.apply_patch with an `*** Add File: C:/Dev/qa-visual-automation/tests/backend/test_ocr_child_environment.py` patch containing the synthetic environment fixture, eight expanded environment cases and separate guarded re-export node. Tool result was `{}` with `Script completed`, wall duration 10.9 seconds. This occurred on the 2026-09-26 KST session before the parent's message beginning `Fermat newhelper firstordinarywrite denied; runner untouched, PM informed` established the hold for this lane. The tool output did not expose an absolute start/end timestamp; exact wall-clock time is therefore NOT_RECORDED, not inferred. This was apply_patch, not a PowerShell/FileMode write. Subsequent read-only Get-FileHash verified actual raw66ee202f0843064138f87456d54002062ad6fa752d4e9e755c1d603a00dcc85b.

Future integration must diff the proposed final test against existing actual draft66ee, not create a supposedly absent test file. Helper remains absent separately. Only the report-path candidate may receive proposed diagnostic tests during HOLD.

Fermat subsequently supplied frozen prospective extraction evidence: environment patch db3e8a330827c8ca8661677d74ccfe33c1febd39f70d0600c156e74fe49f3b31; proposed runner raw b2fed1ebec25069821e3ddcd3f7c7368375dbf810575c232dad005b55a4fd314; proposed helper raw 4329d761e0885c40635abe4eba7c1f99114b7dd5ccfc6bb2a52492cad4d757eb. Fermat reports authorized in-memory AST equivalence passed, no module execution. These are author-reported prospective identities, not locally available/importable source or an independent PASS here. Actual runner remains baseline and helper absent.

## Draft nodes and parent-only prospective selection

After PM resolves the source hold and independent review confirms exact implementation:

- Primary environment selection: `python -m pytest --noconftest tests/backend/test_ocr_child_environment.py -k "not runner_reexport"`. Eight parameter-expanded environment cases: credential/unlisted exclusion, exact SystemRoot/WINDIR and scratch/thread constants, absent optional values, three optional paths each relative/absolute with normalization.
- Separate fresh process only: `python -m pytest --noconftest tests/backend/test_ocr_child_environment.py::test_runner_reexport_separate_process`. No runner import occurs at module scope. Guard psycopg.connect before runner import; synthetic get_settings prevents actual settings resolution; no arguments/credentials retained; expected connection count zero. Parent must inspect the entire import graph before approving this check. It must never run in the qualifying observer process.
- Set external plugin autoload disabled for each parent invocation. Use existing approved Python 3.12 and capture interpreter/dependency identity; no installation is authorized. Primary dependencies: pytest plus stdlib and the approved shared helper. Re-export additionally requires existing runner dependencies including SQLAlchemy, psycopg, pydantic-settings, rfc8785, Pillow and schema validation dependencies. No client/catalog/DB fixture is requested.

The synthetic environment fixture replaces os.environ with a synthetic mapping; it never enumerates/copies or reports real ambient values. Optional path cases use tmp_path and monkeypatch only. Module imports remain lazy. No subprocess is launched by these tests.

## Exact prospective review

Evidence-only candidate BACKEND-OCR-001-observer-focused-tests-candidate-09.py provides an unexecuted AST review function: complete child_environment FunctionDef equality; remove the old function and new exact import/re-export and require all remaining runner AST identical; new module permits only docstrings, import os, and the identical function. No source exec or copied implementation. Baseline runner raw SHA-256: 115cbbf2d685f4d637b2f4a352cb0ba67e064058583b460b48218bf580622a82. Baseline containment-test raw SHA-256: e72c2fb79a9bc3b0c0e08f155b5c78f16173d8e02ecc9f8349f2ecab3674af45. Actual comparison by this lane NOT_RUN. Fermat's proposed helper bytes exist at .orchestration/reports/BACKEND-OCR-001-observer-environment-proposed-09.py; the actual backend helper remains absent.

Independent review must additionally confirm unchanged production containment hash, _finish AST/body, _L1_CHILD bytes, oracle/constants and t0..t1 block; diagnostic persistence must precede the final current/headroom sample and gate checks. No numeric/cap/thread/native policy changes.

## Finalized diagnostic proposal, still NOT APPLIED

Frozen signatures: _l1_read_text(path, limit=65536), _l1_snapshot(phase, observer_pid, child_pid=None), _l1_persist_snapshot(path, snapshot). Snapshot keys: phase/started_ns/finished_ns/atomic/cgroup/processes/errors. Cgroup keys memory.current/max/swap.max/stat/events; observer/child process keys pid/ppid/pgrp/start_ticks and VmRSS_bytes/RssAnon_bytes/RssFile_bytes/RssShmem_bytes. Missing fields use None and exception type only. Persistence has 32KiB JSON cap, temp write/flush/fsync/replace. Read Galileo's exact report-path prospective code raw73cb1432d9e23f2381474c9059b68e0149be35d9544b62b478e830134705b5ac and design rawe45b649a278b704dbddf23d4c603845e2ceffdd87741d8c9c7bfab1b95ce87c5. No prospective code imported/executed.

Use fake streams/readers for every /proc and cgroup read, not actual files/native APIs. Exercise the real adopted shortpeak control flow with fake launch/handle, deterministic ready protocol, identity/member/read fakes and blocked pressure gate. Never reproduce try/finally in a test and call that production cleanup coverage. Count the same sole _finish once after a handle exists; invoke unchanged _finish with a fake handle to assert one stop/close. Before-launch diagnostic failure requires zero launch/finish calls. Do not extend scope to arbitrary preexisting recorder callback failures.

Concrete cases are now authored in the report-path candidate: test_diagnostic_snapshot_missing_or_oversized_read (2), test_diagnostic_read_is_max_plus_one (1), test_diagnostic_invalid_output_precedes_file_access (2), test_diagnostic_failure_uses_existing_cleanup_once (7: observer_persist/snapshot/serialize/flush/fsync/replace/headroom). The control-flow cases call eventual adopted _l1_shortpeak with fake Path/os/launch/ready protocol; a counting wrapper calls unchanged _finish on a fake retained handle and requires exactly one stop/close. Before-launch failure requires no launch/finish. Snapshot data is retained in finally/JUnit; headroom case checks exact final current/headroom after persistence; gate writes fail the test. No actual /proc/native/DB access or prospective source execution. The fixture imports only future applied test_ocr_containment, never the report-path proposal.

Primary proposed selection remains `-k "not runner_reexport"`: 8 environment plus 12 diagnostic parameter-expanded cases (20), followed by the separate re-export node (1). These are authored counts, NOT collection results. Existing 12 pure oracle cases and exact shortpeak collection are parent/Galileo scope. External plugin autoload disabled and --noconftest remain required. Imports/assertions require a fresh isolated process; primary diagnostic fixture checks runner and DB modules absent.

## Validation and outstanding items

Frozen proposed focused-test raw SHA-256: 4734956ec3e96339c4dc4e0d80d346891e61b738029a99ed5af0e3ca77fc056a. Exact actual-draft-to-proposal diff saved as BACKEND-OCR-001-observer-focused-tests-diff-09.patch, SHA-256 2ac1ab5de8ea4ebd89645fd09103552a13938d4bb8792fc728068c9c7614a72b. Generated by read-only `git -c core.autocrlf=false diff --no-index` (exit1 means differences), then saved with apply_patch. Diff endpoints explicitly name existing actual test and report-path candidate. Actual draft hash66ee reconfirmed unchanged. No AST parser was executed by this lane; parent may parse these bytes without importing them.

Performed text reads, searches and Get-FileHash only, plus the declared authoring operations. All pytest, collection, Python imports, AST execution, native/Docker/model/DB operations: NOT_RUN. No qualification or admission assertion produced. Capture08 and all prior failure logs untouched.

Remaining: PM source disposition/application authority; independent import/body/timing/cleanup review; integrate proposed final test as a modification of draft66ee only after renewed authority; parent isolated captures with exact frozen hashes and dependency mismatch limitation. Galileo schema and Fermat report-path proposal bytes now exist and are frozen. Actual product helper is still absent; actual product refactor is not applied. The actual draft must not be described as passing or capture-ready.
