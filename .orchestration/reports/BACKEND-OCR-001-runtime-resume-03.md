# BACKEND-OCR-001 runtime-resume final addendum / Backend Engineer 03

- Date: 2026-09-25
- Activation: `.orchestration/handoffs/PHASE-3-runtime-resume-01.md`
- Status: **Backend shared dependency, qualified profile, image and runner integration complete for owner submission.**
- Accepted contract revision 2 SHA-256: `478fafdcf7d3876f9437137e382d41872f100dad40206a280da7551283e8dd44`.
- The prior owner report and handoff remain preserved. This addendum records the later runtime qualification integration.

## Integrated runtime contract

- `pyproject.toml` contains the six exact direct pins: `paddleocr==3.7.0`, `paddlepaddle==3.3.1`, `paddlex[ocr-core]==3.7.2`, `opencv-contrib-python==4.10.0.84`, `RapidFuzz==3.14.6` and `rfc8785==0.1.4`.
- `backend/requirements.lock` contains 96 unique packages and the complete Windows/Linux Worker lock union with hashes. `colorama` and `tzdata` are Windows-only; `uvloop` retains its Linux/CPython marker. Final lock SHA-256: `30c023d97b69a0d4e82a449bb88bc0fb542e95bf5c07674215821bd769661352`.
- Both images use Python 3.12.14 slim trixie and exact native pins `libgl1=1.7.0-1+b2`, `libglib2.0-0=2.84.4-3~deb13u5`, `libgomp1=14.2.0-19`. Both perform hash-locked installation, wheel installation and `pip check`.
- Images package Worker code and schema/profile resources, but no model binary. `/models/ocr` remains an external read-only deployment mount; Paddle caches use `/var/cache/paddle`.
- Four production profiles load under their exact RFC8785 digests. Only the current platform's two profiles are exposed as `AVAILABLE`.
- Backend validates complete runtime package/native-package records, runtime manifest digest, frozen profile schema/digest and exact execution policy before immutable result publication.
- Runner supervision keeps deadline and RSS checks active while a framed IPC result is received. A partial frame cannot block the monitoring loop, truncated frames become retryable `ENGINE_PROCESS_CRASH`, and runtime Python major/minor must exactly match the frozen profile.

Production profile digests:

| Platform/profile | SHA-256 |
| --- | --- |
| Windows unified | `39917d5bf35cd7b538ecd38db6f5c26604cda8370faae0069aa1acc1d2bde916` |
| Windows Korean | `00300d2aebd8097cba3879f8f35cae888c3e7a6b0abd3f426b654e5d7201c679` |
| Linux unified | `89d587ee744e52a53593eae177366efe9b72079d6c0eacecad91c0ec916221ed` |
| Linux Korean | `f4daa25d626111e2ca975c50abceaa838e2a3f5d49bcec69fdeab5cea3723c16` |

## Final execution evidence

- Windows full configured suite: `202 passed, 3 skipped, 1 existing deprecation warning` in 14.14 seconds. Skips were the opt-in real Linux runtime test and two POSIX raw-frame cases.
- An earlier run without `--basetemp` produced 106 setup errors solely from an inaccessible Windows pytest temporary root. The unchanged suite passed after selecting a new workspace-local temporary directory.
- Windows focused runtime/result/packaging regression: `31 passed, 2 skipped, 1 existing warning`.
- Clean Windows Python 3.12 hash installation: 96 packages installed; wheel build, `pip check`, isolated `-I` import from an OS temporary directory outside the source tree, four production profile digests and fixture digest all PASS.
- Linux test image `qa-backend-ocr-runtime:local`: manifest-list/image digest `sha256:81845d5d677a712188bfc7d326448976ca1fff6371a31138f4d19fb50130415c`; exact APT install, hash lock, wheel build and `pip check` PASS.
- Linux production image `qa-backend-ocr-production:local`: manifest-list/image digest `sha256:f5864cffb217c86355c747bb1780a5ad4ac786f65ef01a40696131749df6882f`; build-time `pip check` PASS.
- Linux network-disabled runner/result/packaging regression inside the baked test image: `33 passed, 1 warning` in 4.47 seconds. This includes confirmed partial-header timeout, truncated-frame classification and measured child-RSS enforcement.
- Linux baked-image Backend/Worker boundary against a unique PostgreSQL test database: `52 passed, 1 warning` in 6.59 seconds.
- Linux baked-image real `OCRRunner` to unique PostgreSQL test database, with only the qualified model root mounted read-only: `1 passed, 1 warning` in 7.26 seconds. Run/job, OCR result, verification result, regions and immutable references committed consistently.
- Retained Owner05 qualification: `tests/ocr` 23 passed; Windows/Linux clean hash installation, native import and five-locale actual OCR PASS. Offline English inference completed in 6.65 seconds at about 641 MB peak RSS; Korean completed in 5.80 seconds at about 580 MB. A missing model root fails closed as `MODEL_UNAVAILABLE`.
- PostgreSQL finalize rollback and lost-ack recovery remain covered by the owner suite; no partial result rows survive a writer failure.
- `git diff --check`: PASS; only line-ending conversion notices were emitted.

The 300-second deadline and 2-GiB checks supervise the OCR child, including blocked or partial IPC receive. Synchronous input storage reads occur before child launch and rely on the storage provider's bounded I/O behavior. RSS is sampled from the child PID rather than enforced by an OS cgroup. These implementation limits are retained explicitly and are not represented as a process-tree hard cap.

## Final source snapshot

Manifest: `.orchestration/reports/BACKEND-OCR-001-runtime-resume-source-manifest.txt`.

- scope: `backend/**`, `tests/backend/**`, `pyproject.toml`;
- sorting: `System.StringComparer.Ordinal`;
- file count: 95;
- aggregate SHA-256: `bb9c86a548c31bfb69329024ad992e605c41d10f6e7258c9b81dd5cb2237187f`;
- manifest file SHA-256: `7b3bb7e5638f1e7cbda101bd2e5451f5453c0b547e410b3b9d7d06a3b8e2e23d`;
- matching Worker source aggregate: `058a445d90b7c50897f77f503a31e7dd425ea71f845a70a40666816e3c7a7b94`.

The snapshot includes all current shared Backend files in the assigned scope. Changes owned by other roles outside that scope were neither included nor reverted.

## Remaining gates and change control

This is an owner submission, not PM acceptance. `AC-P3-01..04` remain `NOT_RUN`. Frontend live verification and final Reviewer08 implementation review remain PM-gated. No PM YAML/state file was changed by Backend03.

No commit, merge, push, deployment, user-data deletion, DB initialization/reset, account/security change, IP check or Phase 4 work was performed.
