# UPLOAD-001 review rework / Owner 06

Date: 2026-09-25 KST  
Requested disposition: `READY_FOR_REVIEW` owner submission; independent Reviewer08 closure pending  
Formal input: `.orchestration/reports/REVIEW-UPLOAD-001-08.md` SHA-256 `1da2d73e837d62bc4b9926f41b168a56d12bc64bd9ab8c56001640d7c234bab8`  
Formal handoff: `.orchestration/handoffs/REVIEW-UPLOAD-001-08.md` SHA-256 `f182ffe3eb83b7ae193bb7c5efdca4d852c950108bce0822d11fff919dee13cf`

## Scope and result

This correction addresses only uploader findings `R08-P2-REVIEW-006` and `R08-P2-REVIEW-007` in the existing Owner06 scope.

- `006` corrected: non-Windows filesystems are no longer accepted unconditionally. Linux resolves the spool, reads `/proc/self/mountinfo`, matches the resolved path and `st_dev` major/minor to the longest applicable mount, decodes mountinfo octal path escapes, and accepts only an explicit local filesystem allowlist. Representative NFS/CIFS/SMB/FUSE network types and every unknown/volatile type fail closed. Windows retains its `GetDriveTypeW` local-drive decision. Other operating systems fail closed.
- `007` corrected: `config.canonical_backend_origin` delegates to the single `origin.canonicalize_origin` implementation and translates `ValueError` to the existing public `ConfigError`. Binding initialization and `RuntimeConfig` now have one accepted-origin set. Bare `0x` and `0X` are rejected together with hexadecimal/numeric aliases.
- The F29 corpus now checks 10 accepted aliases and 39 rejected boundary inputs through both public entry points, including DNS/IPv4/IPv6/default ports, parser repairs, userinfo, path/query/fragment, IDNA, zones, numeric aliases, malformed labels and ports, bare `0x`/`0X`, and `RuntimeConfig.create` parity.

No actual host mount configuration was changed. No fallback capability guess, network filesystem adoption, rebind, migration, or protocol version change was added.

## Changed files

| File | SHA-256 |
| --- | --- |
| `agent/screenshot_upload/durable_fs.py` | `a362f03cfd846d7e93f411a6b42d141931eb460f1c043679ab50b7e5ad601eca` |
| `agent/screenshot_upload/origin.py` | `3cddfb772b3108af5060dee15b3e51ce67f18905d5b632105b6a4c00b87d4a1a` |
| `agent/screenshot_upload/config.py` | `b4254ded8e240662af83df0783f60c6741fb27888e0d1c583e10c4424858cc18` |
| `tests/upload/test_durable_fs.py` | `5485f962662ee68b35dce2a920ea910bff35cda5006fa262ac579c243f9b6386` |
| `tests/upload/test_origin_binding.py` | `9ba3397419a12f4fdd0dc07c395a78a69631b5381e5a0c1f9807d9fc1492a79f` |

Canonical source manifest: `.orchestration/reports/UPLOAD-001-review-rework-source-manifest-06.txt`. It contains 35 Python-ordinal-sorted, slash-normalized UTF-8 `relative/path sha256` lines for `agent/screenshot_upload`, `tests/upload`, and `pyproject.toml`, with one final LF. Every entry was hashed from the current workspace. Manifest/file aggregate SHA-256: `eefafa7ce16a82b8f30613612968b6acb74b3ba09f3f2f2788547a7937b9c934`.

## Filesystem decision details

Explicitly supported Linux types are `bcachefs`, `btrfs`, `ext2`, `ext3`, `ext4`, `f2fs`, `jfs`, `nilfs2`, `overlay`, `reiserfs`, `xfs`, and `zfs`. Explicit network names include `9p`, AFS, Ceph, CIFS/SMB, Coda, DAVFS, GCS Fuse, GlusterFS, Lustre, NCPFS, NFS, and SSHFS; any `fuse.*` type is rejected as network-backed. All types outside the local allowlist are rejected even when they are not recognized as network-backed.

The parser ignores malformed unrelated mountinfo rows but fails if no valid row matches both the resolved path and device. For bind/nested mounts it selects the longest matching mount point and then the later matching row at equal depth. An unreadable mountinfo file, invalid escape in the only candidate, unsupported platform, unresolved path, unknown type, or unmatched device/path produces `FilesystemProtocolError` before spool binding or mutation.

## Delegation

- `006` was requested as `gpt-5.6-sol/high` with write scope limited to `durable_fs.py` and `test_durable_fs.py`.
- `007` was requested as `gpt-5.6-sol/medium` with write scope limited to `origin.py`, `config.py`, and `test_origin_binding.py`.
- The multi-agent spawn tool accepted those requested model/effort overrides. Completion payloads did not expose a separately auditable runtime model identifier, so actual model identity remains unverified rather than inferred.
- Earlier interrupted agent IDs returned `not_found`; current file hashes still matched the pre-rework submission and no partial test file existed. Only then were replacement agents spawned once with the same disjoint scopes.

## Fresh parent execution evidence

### Windows

Environment: bundled CPython 3.12.14; new `.pytest_cache/upload-review-rework-win` venv; `pip install --require-hashes -r agent/screenshot_upload/requirements.lock`; Linux-only uvloop marker correctly ignored; `pip check` returned `No broken requirements found`.

1. Origin/config targeted:

   `python -B -m pytest tests/upload/test_origin_binding.py -q -p no:cacheprovider`

   Result: **92 passed in 0.58s**.

2. Filesystem targeted:

   `python -B -m pytest tests/upload/test_durable_fs.py -q -p no:cacheprovider`

   Result: **17 passed, 1 skipped in 0.04s**. The skip is the actual Linux mountinfo check; the actual Windows local-drive check ran.

3. Complete uploader synthetic suite, live option omitted:

   `python -B -m pytest tests/upload -ra -p no:cacheprovider`

   Result: **135 collected; 133 passed, 2 skipped in 1.65s**. Skips: opt-in live integration and actual Linux mountinfo check.

### Linux

Environment: `qa-backend-upload-final:local`, Debian 13 / Python 3.12.14, Windows workspace mounted read-only, source copied to `/tmp/upload-review-rework`, all copied `__pycache__`/`.pyc` removed, new `/tmp/upload-review-rework-venv`, hash-locked install and `pip check` PASS. Bytecode count under the execution source was zero before and after.

Command:

`PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 python -m pytest tests/upload -ra -p no:cacheprovider --basetemp=/tmp/upload-review-rework-pytest`

Result: **135 collected; 133 passed, 2 skipped in 1.30s**. The actual Linux `/proc/self/mountinfo` test ran successfully on the runtime's explicitly supported local mount. Skips: opt-in live integration and actual Windows drive classification. Evidence interval: `2026-09-25T01:15:18Z` through `2026-09-25T01:15:29Z`.

### Matching corrected Backend cross-service

Matched Backend03 artifacts:

- `.orchestration/reports/BACKEND-UPLOAD-001-review-rework-03.md`: `095d641be32bce1d0c66672c875a34493c96555acca604a53c21ad96dfafa0a4`;
- `.orchestration/handoffs/BACKEND-UPLOAD-001-review-rework-03.md`: `1881739c037e5f0dfdc191807ff7dbef10b81f4e295b6bf8d4ac2efd0cdad322`;
- 77-file Backend manifest: `a8b5225bceb106cc3e09883eb3e68c2a28d659f8c0ee9ec65eb6974ffa7696a0`.

The new Windows venv first installed the current project wheel with `--no-deps --no-build-isolation`; `pip check` remained PASS. The original checked-in integration then ran without a temporary plugin:

`python -B -m pytest tests/upload/integration/test_live_response_loss.py --run-live-upload -vv -p no:cacheprovider`

Result: **1 passed in 6.24s**. The test owned an ephemeral PostgreSQL 17 container, random database, temporary Backend storage and uploader spool; discarded the real first 201; restarted Backend and uploader; replayed as exact 200; and verified one COMPLETED receipt, one Screenshot, one object, stable ID/time/Location, list/detail/content and original hash.

The corrected Backend overload response is 503 `REQUEST_OVERLOADED` with `Retry-After: 1`; existing uploader policy treats all 5xx as transient and already retains bounded retry identity/state behavior.

## Preserved failures and corrections

- The 006 subagent's first synthetic test design used real temp-path device IDs against fixed synthetic mount IDs: `1 passed, 16 failed, 1 skipped`. After isolating the parser seam, a second design still had one real-platform assertion error: `16 passed, 1 failed, 1 skipped`. It corrected the design, then reported Windows and Linux `17 passed, 1 skipped` plus binding `92 passed` on each platform. These initial failures were test-design failures, not accepted final results.
- The parent's first matching cross-service attempt failed before uploader behavior because the fresh venv contained lock dependencies but not the current project package. The child helper returned 1 with `ModuleNotFoundError: agent` instead of its synthetic response-loss exit 97. The test cleanup ran. Installing the current project wheel corrected the environment; the one retry passed. This initial result is not represented as product PASS or FAIL.

## Static and cleanup checks

- Source whitespace scan for `agent/screenshot_upload` and `tests/upload`: PASS.
- Review report and handoff remained byte-identical at their formal hashes.
- `qa-upload-live*` and `qa-upload-review-rework-linux-06` container queries returned no remnants after execution.
- No product file outside Owner06 scope, root `pyproject.toml`, contract, Backend, Frontend, PM YAML/state, user capture, shared service configuration, or host mount was changed.
- No Commit, Push, deployment, user/shared database initialization or reset, account/security action, or IP check was performed. The only database creation was the disposable synthetic live-test database described above.

## Disposition and limits

Owner06 requests `READY_FOR_REVIEW` for the corrected 006/007 source and matching owner evidence. The formal independent disposition remains `CHANGES_REQUESTED`; AC-P2-01 and AC-P2-03 remain Reviewer `FAIL`, while AC-P2-02 and AC-P2-04 remain `NOT_RUN`, until PM and Reviewer08 independently update them. The fresh results above are owner evidence and are not relabeled independent acceptance.
