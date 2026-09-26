# ARCH-OCR Linux headroom reassessment / Architect02

2026-09-26 KST. ARCH-OCR-001 / P3-RUNTIME-001 follow-up under PHASE-3-linux-headroom-reassessment-01.md. Requested highest Astra/medium; actual model unverified. Read-only design review; execution remains **HOLD**. This report does not activate implementation, image build, native execution or qualification.

Recommendation: a lightweight pytest observer can retain the same production containment implementation and exact fixed L1 pressure/oracle. Remove both unrelated import paths explicitly: suppress conftest loading for this one selected node, and extract the existing child_environment function into a shared stdlib-only production module. Preserve pytest, PID1, the current test node and cleanup. This is a prospective loading/refactoring correction, not a demonstrated headroom cure. A separate PM file claim, exact-diff independent review and execution authorization are required.

## Capture08 facts and limits

Read frozen candidate07, the current test/fixture and relevant import paths, accepted clarification and prior reassessment, and selected raw Capture08 inner-inputs, manifest, JUnit, terminal and log. Backend03 subsequently supplied the matching Mill review08 and Galileo attribution assessment; both were read and their hashes checked. Their complete113 raw/LF validation remains attributed to Backend03/Mill; Architect02 did not duplicate the full packet audit. PM then supplied final BACKEND-OCR-001-linux-capture-manifest-08.json: independently read/hash-matched c3ea85bc957e75446474e1be74121c1995cad102a49735743d81313bfd612cea,20 artifact entries and HEADROOM_PRECONDITION_FAILED_L1_UNPROVED_CLEANUP_CONFIRMED. PM's20-artifact match is attributed to PM, not re-audited here. Backend03 execution scope is completed/BLOCKED; no resumption follows.

The preserved outcome is **JUnit 1 FAIL / 0 error / 0 skip**, at tests/backend/test_ocr_containment.py:328. Baseline readiness was reached with child PID7, nonce-matched ready/touched335544320 bytes, configured increment234881024 bytes and observer PID1. Reaching328 means the preceding parent/group/membership checks and RssAnon>=320MiB assertion passed. The exact RssAnon sample was not saved.

At the headroom read, cap536870912 minus observed headroom20561920 gives **516308992 bytes (492.390625MiB)**. This is arithmetic reconstructed from the assertion, not an independently persisted memory.current field. Headroom is19.609375MiB, below the fixed64..160MiB interval. The residual172.390625MiB after subtracting requested baseline is **not observer RSS**: the baseline is only a lower bound on child anonymous residency, and aggregate charge includes child/runtime, observer, file/cache, kernel and other charged memory. No component attribution, leak diagnosis or measured import cost follows.

The assertion occurs before before_gate checks329-330, facts persistence334-337, t0 at339 and G write340. Child224MiB allocation follows G. No increment attempt, t0/t1, elapsed witness, causal event delta or l1_verdict was produced. Whole-suite0.377s, testcase0.287s, log0.38s and cleanup0.03088249099528184s are not the250ms pressure interval. The oracle after finally was not reached.

Saved initial/helper event snapshots have zero max/oom/oom_kill/oom_group_kill. Natural container exit1 with OOMKilled=false and complete assertion JUnit support ordinary pytest failure, not an observed observer OOM/crash. Candidate audit_result returns UNPROVED_OBSERVER_EXIT on any nonzero exit before parsing JUnit; preserve that raw status without turning its label into a cause. Direct owned-child cleanup is recorded True; helper scope is direct-child-reaped/no residual runnable cgroup work. Manifest confirms exact-owned rm success, cleanup_confirmed=true, stop_requested=false and launch_uncertain=false. This is not a universal orphan-zombie reaping guarantee.

Capture08 therefore proves an unmet test setup precondition, neither successful shortpeak enforcement nor a breach of the runtime contract. Original06 template failure and07 cleanup remain distinct; no residual08 is implied.

## Static import analysis

The selected test requires tmp_path and record_property, both pytest built-ins, plus the parametrize mode. It requests no database/client/catalog fixture. tests/backend/conftest.py defines those fixtures without autouse: importing the fixture module is distinct from executing its database setup or migrations. There is no inspected root tests/conftest.py in the rg inventory. pyproject.toml has testpaths but no additional pytest addopts in its pytest section.

Two independent edges expand the observer import graph:

1. Pytest discovers tests/backend/conftest.py. Its top-level imports include SQLAlchemy, Alembic, FastAPI TestClient, app.main, API dependencies and LocalStorage. app.main imports db.engine and the API router; that router imports the catalog/screenshot/verification routes. db.py constructs engine and SessionFactory at import using settings. Engine construction is not proof of a database connection or query. The captured Starlette TestClient warning corroborates that import path, not its memory cost.
2. test_ocr_containment.py imports child_environment from backend.app.workers.ocr. Loading ocr.py imports settings, db.SessionFactory, verification jobs/results services, LocalStorage, ocr_runtime and ocr_source. ocr_runtime imports SQLAlchemy/models/admission. verification_results imports rfc8785, model exports and worker.ocr/schema modules; LocalStorage imports image validation/PIL. Thus --noconftest alone does not make the observer application-independent. These are static reachable paths, not evidence that OCR inference or model loading ran.

The production ocr_containment.py module has stdlib-only imports; backend/__init__.py and backend/app/__init__.py are empty, workers/__init__.py contains a docstring. child_environment itself uses only os and its scratch argument: it constructs an explicit environment allowlist and normalizes optional model/cache paths. This is a natural shared boundary. No need to copy/fork containment, stub SQLAlchemy, remove modules from sys.modules, selectively exec source text, or replace production code with test doubles.

External plugin autoload is already disabled by candidate07. Repeating that flag does not remove conftest or runner imports. The initial capture process uses -I -S but execs python -m pytest without those flags; pytest needs its installed packages. Do not simply add -S to pytest or claim that the initial isolated capture interpreter guarantees isolated test loading.

No full dynamic import inventory or package-by-package charge was measured. Static edges establish an avoidable loading dependency, not how many bytes its removal will recover. Even an isolated observer may fail either end of64..160MiB; an overly light observer can have more than160MiB headroom. Do not add ballast, warm caches or adjust pressures to force that interval.

## Contract versus fixed evidence design

Accepted revision2 retains one300s productive budget,2GiB child RSS bound, parent mutation authority, containment/reap or quarantine, and fail-closed deployment admission. Prior clarification requires continuous enforcement or equivalent and descendant coverage unless absence is proved. Existing cgroup total-charge enforcement is the selected stricter boundary within the qualified dedicated layout; it does not equate aggregate charge to process RSS or qualify arbitrary shared mappings.

The reduced512MiB cap,320MiB baseline,224MiB increment,64..160MiB headroom and strict elapsed<250000000ns are the approved L1 test design. The contract does not independently mandate these numeric fixture values, including250ms. Their empirical status does not authorize weakening them. Retain all five unchanged. Changing a numeric oracle needs an explicit later PM evidence-plan decision and independent review; weakening the contractual resource subject/bound needs contract review. Neither occurs here. No L2 substitution or readiness inference.

Fixture-free execution changes observer workload and therefore the tested setup; it is not evidence for full OCRRunner import footprint, DB threads, real models or production deployment headroom. Its admissible scope remains a synthetic short attempted allocation using the real containment code, with causal enforcement/timing evidence and cleanup if those conditions actually pass.

## Minimal prospective change set (Backend03 owns; NOT APPLIED)

| Exact proposed file | Bounded change and reason |
| --- | --- |
| backend/app/workers/ocr_child_environment.py (new) | Move the exact child_environment body with only import os; keep all current keys, optional path normalization, values and ambient exclusions. One implementation shared by runner and tests. |
| backend/app/workers/ocr.py | Import/re-export child_environment from the new module, removing its old definition. Preserve existing caller API and all runner behavior. This production refactor needs explicit file ownership approval. |
| tests/backend/test_ocr_containment.py | Change only environment-helper import plus bounded pre-gate diagnostic persistence. Retain node, child script, constants, oracle and cleanup. Save current/headroom/exact child RssAnon before the assertion can discard them. |
| .orchestration/reports/BACKEND-OCR-001-linux-headroom-candidate-03.py (new proposed name, subject to PM claim) | Derive a new immutable candidate from07; add --noconftest to only the exact selected-node pytest exec. Preserve PID1 exec, built-in fixtures/plugins, external capture, ownership, deadlines and cleanup. Pin the new helper/test/runner and relevant complete source set. Never edit candidate07 or historical captures. |
| tests/backend/test_ocr_child_environment.py (new proposed test) | Focused environment authority/regression tests for the shared function; execute under conftest-free loading after separate approval. No DB/model dependency needed. |

No change to ocr_containment.py, conftest.py, dependency locks, Dockerfile, contract, profiles or resource flags is proposed. Existing Dockerfile copies backend and tests/backend, so these new files fit its build context. A new exact-source immutable image/pin snapshot is still mandatory after approved edits; old imagea133 cannot represent them. Exact future manifest/evidence paths belong to PM/03, not permission to reuse08.

For pre-gate diagnostics, keep bounded observations in PID1, without a helper process/thread in the cgroup. Record a phase label, monotonic timestamp, cap/swap, memory.current, selected memory.stat fields (anon/file/kernel/shmem and relevant components), memory.events, owned PID start identity/group/membership, observer and direct-child VmRSS/RssAnon/RssFile/RssShmem where available. Capture observer-only before launch and baseline-ready before gate. Values are sequential, non-atomic snapshots; do not sum overlapping memory.stat fields or equate summed RSS/PSS to cgroup charge. Bound output and avoid environment/credentials/maps content.

Write those observations before the headroom assertion and preserve them through its failure path. Persistence itself can add charged file/cache/tmpfs overhead. Complete any pre-gate persistence before taking the authoritative final current/headroom and unchanged before_gate event checks; retain that final scalar sample in the existing finally/JUnit path. Recheck identity/liveness as before. Do not insert instrumentation, fsync, import scans or memory sampling into t0..t1. Missing diagnostic fields must be explicit, never guessed. A failed diagnostic/identity/cleanup path must still invoke the existing sole stop owner.

The new candidate may retain the raw broad nonzero-exit label and add a separate precise JUnit outcome. It must not turn every exit1 into a known assertion if XML is missing/malformed. Classification cleanup is not necessary to qualify pressure and must not obscure original08 bytes.

## Required equivalence and review evidence

Before any native attempt, independent static review must verify:

- Production containment bytes remain hash-identical to the frozen helper. Normal module import resolves that file in /app; no alternate helper or patched process/cgroup API.
- The shared environment function has the same body/behavior. Tests cover ambient credential exclusion, SystemRoot/WINDIR preservation, scratch paths/thread limits, optional model/cache absolute paths and re-export compatibility. Do not record real ambient values. This verifies authority preservation, not merely import spelling.
- Fixed _L1_CHILD bytes, constants, _l1_oracle, launch argv -I -S, child env/cwd, identity/nonce/gate/protocol, retained-handle poll, t0/t1 endpoints, event causal requirements, membership/cap/swap rechecks and _finish behavior remain equivalent. Diagnostic changes precede timing and do not bypass assertions or replace FAIL with SKIP.
- --noconftest omits no required fixtures/hooks for this node; collection still selects exactly one shortpeak case, built-in tmp_path/record_property/JUnit remain available, plugin autoload stays disabled. Pin pytest/dependency/runtime identity, optimize0/assertions enabled and effective argv/config. A small saved module-name inventory can verify absent conftest/app/DB/provider modules before launch; record identities only, not sensitive settings.
- Preserve same fresh dedicated512MiB cgroup, swap0, PID1 observer and one direct child, read-only root,128MiB tmpfs, network none, external ownership capture and one-stop cleanup. Do not move the observer outside the cap, add OOM-score preferences, introduce sub-cgroups, change host settings or reset events/caches.
- Retain the current pure oracle negative cases (missing attempt/identity/cleanup/timing,250ms boundary, max-only, no causal denial/kill) and add diagnostic failure-path review/tests so assertion/serialization failure cannot evade cleanup. These checks are future work, not passed here.

Collection checks/import inventories must run only after PM authorizes the exact non-native scope; no pytest collection or application import was executed by02. Do not import the full runner into the qualifying pressure process just to prove the re-export. Verify that compatibility in a separate authorized non-native check.

## Missing measurements and minimal future validation

08 lacks a baseline-before-child cgroup sample, retained exact observer/child RSS, memory.stat decomposition, stage-specific import inventory and persisted final current/headroom. These omissions prevent a measured explanation of the492.390625MiB total. A future isolated run can establish its own composition and precondition; comparing it to this incomplete08 snapshot cannot establish exact causal savings for any package. A controlled matched diagnostic comparison would need a separate later design/authorization if causal attribution remains necessary; no repeated full-import pressure run is required by this recommendation.

After PM accepts the bounded correction and ownership,03 prepares the exact diff and independent review checks the above invariants. PM separately authorizes any image build and **one** changed native shortpeak invocation with immutable image/source/pins, a new evidence namespace and the predeclared diagnostics. This report authorizes none of them.

That one invocation records observer-only and baseline-ready diagnostics, then either rejects setup under the unchanged headroom/identity/events checks or releases the one fixed increment. No retry to hunt for a favorable cache/scheduling state. The timed result qualifies only with the same attempt identity, elapsed<250ms, attributable oom/oom_kill and matching denial/exit-9, unchanged limit, and proven cleanup. A passing scoped L1 result still does not qualify the2GiB/300s production contract or admission.

Stop conditions: source/image drift; unexpected imports/participants; unknown identity; nonzero setup pressure counters; cap/swap mismatch; missing readiness; headroom outside either bound; ambiguous attempt/cause; missing/negative/>=250ms elapsed; observer loss; malformed evidence; or unproved cleanup. Preserve actual FAIL/SKIP/unproved classification as applicable, stop only positively owned work, retain evidence/quarantine uncertainty and return to PM. No cap/baseline/increment/headroom/timing tuning, padding, L2 switch, alternate probe, unchanged rerun or automatic next phase.

## Checked input identities

SHA-256 below are independently read locally by02; only selected records were checked, not another113-file certification. Inner paths refer to .orchestration/reports/BACKEND-OCR-001-native-apply-linux-evidence-03-08/.

| File | SHA-256 |
| --- | --- |
| docs/architecture/phase-3-ocr-contract.md | 478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44 |
| reports/ARCH-OCR-runtime-clarification-02.md under .orchestration | 8eed0822dee5781b8fb23187f1a24a1d1ff1014a14f5bee59e2bc99f42795375 |
| reports/ARCH-OCR-native-reassessment-02.md under .orchestration | 7fa4ba3b9452bd35317a051104aa9f18d4ca22e652ac25c0c8a628b7c1108a7c |
| reports/BACKEND-OCR-001-linux-template-candidate-07.py under .orchestration; inner capture.py | e669d74fc1f683ad57cf3792860910f65198cbed3f6d0dee91232c36e36d082c |
| tests/backend/test_ocr_containment.py | e72c2fb79a9bc3b0c0e08f155b5c78f16173d8e02ecc9f8349f2ecab3674af45 |
| backend/app/workers/ocr_containment.py | 9a47c3348980b4f5d25afafce5407ed067cd974caff2b60b87d2dc5f8228dbd9 |
| backend/app/workers/ocr.py | 115cbbf2d685f4d637b2f4a352cb0ba67e064058583b460b48218bf580622a82 |
| tests/backend/conftest.py | 5561e5cd0d490b9385075b9d8a34b725752223ffda695c8bf51c6c610e2da79b |
| inner inner-inputs.json | 86ca0ce4e60b92a6582a6053e9aa428cff56283764e0136a3e87b889f265a755 |
| inner result.xml | 2dd0078d5f4dc71542f0835f13f9aea796115c77e20ed1a9e2744dbe10d084cb |
| inner manifest.json | f0181c98ceb794d25d76bf6fb38692cffac9309ffb3f5f1bd183e4f13469e0dd |
| inner terminal.json | 2441c977ae2de6a476ca1bc66f371e448d9ddfdda9a819f6c035417a9886f545 |
| reports/BACKEND-OCR-001-linux-capture-review-08.md under .orchestration | 8c1571bd9359dc550df3fa3b5d11fbd9b9b6a9130415ab960b705a157bd21fba |
| reports/BACKEND-OCR-001-linux-headroom-assessment-08.md under .orchestration | 8893cff8bd6473bf3d5f75119ad265afb5088cec7270938cee402067a0a720b2 |

Candidate pins record test LF52349c96c31b6c373d8d8c99471b21df64ea5dea4a0a77f52539a884492e0f02 and containment LF6129ff42c0789df51c105068cbda48d0b299885f53c491e7d3a777315661467c. Raw and LF identities are distinct. Old reassessment helper/test hashes describe earlier code, not candidate07.

## Actual work and handoff

Only this report and paired handoff were authored. Performed read-only rg/Get-Content/shallow listing and Node fs/crypto JSON/hash inspection. Final hashes of contract, containment, runner, test, conftest and candidate07 match the initial inspected identities; both authored documents passed UTF-8 replacement-character and explicit HOLD/NOT_RUN checks. Two guessed worker module .py paths were absent; schemas is a package and its __init__.py was read. No denied historical directory was accessed, no approval workaround used. No native/API/Docker/build/pytest/import/model/DB/dependency operation occurred. All proposed tests and measurements are **NOT_RUN**. Existing08 failure and cleanup are reviewed saved evidence, not newly executed tests.

No subagent was duplicated: Backend03's existing Galileo facts assessment and Mill audit were reused as supporting evidence;02 owns design/equivalence. Windows same-cause3, historical cleanup2, all AC/04/08/admission gates remain unchanged. No commit/push. PM's next decision is whether to authorize the exact proposed bounded correction and later review stages; no numeric change is requested. Until then execution stays **HOLD**.
