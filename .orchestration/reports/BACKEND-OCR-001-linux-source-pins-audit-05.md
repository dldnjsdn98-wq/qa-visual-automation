# Linux source pins 05 / Backend03 evidence sidecar

Status: OWNER_HOST_SOURCE_HASH_AUDIT_COMPLETE; independent Mill review and parent build-context audit pending. No build/native qualification or AC promotion. Requested role: reused Boole evidence owner, Terra/high; actual runtime model identity not attested.

Authority read: `.orchestration/handoffs/PHASE-3-linux-pins-build-01.md`, SHA-256 `2f7090a2cd0f8a1f1939553d3f370f2371ca0dd594e0d027e1d118174e634be8`.
Capture and plan read as text only; no import or execution. Unchanged capture `.orchestration/reports/BACKEND-OCR-001-native-apply-linux-capture-03.py` SHA-256 `d0a8e756cdd4cafc394d12a68e527632365aeaf43f6d9ca8cc063763db21d7fd`, checked again after pin generation.

## Output and membership

New pin input: `.orchestration/reports/BACKEND-OCR-001-linux-source-pins-05.json`.
Raw SHA-256: `d92e20493eb42a3d4d2702b17c3d5559c17cad78e31b364387039e649146f2bc`.
Schema is exactly `schema_version: 1` and `files`; each relative forward-slash path maps to exactly `sha256` and `lf_sha256`, lowercase 64-character hex strings. Count113 is within capture limit128. All nine capture-required paths are included.

| Scope | Count |
| --- | ---: |
| backend, nonhidden and without __pycache__ | 76 |
| worker, nonhidden and without __pycache__ | 28 |
| tests/ocr/fixtures/runtime | 6 |
| pyproject.toml | 1 |
| tests/backend/conftest.py | 1 |
| tests/backend/test_ocr_containment.py | 1 |
| Total | 113 |

Membership was listed with `rg --files --hidden -g '!.*' -g '!**/.*' -g '!**/__pycache__/**' backend worker tests/ocr/fixtures/runtime`, then checked against `rg --files --no-ignore --hidden -g '!**/.*' -g '!**/__pycache__/**' backend worker tests/ocr/fixtures/runtime`; both sets plus the three explicit paths agree exactly. Names were inspected: no hidden, environment, credential, model-weight or model-cache input. Worker profiles/schemas and backend ORM model source modules are code/configuration dependencies, not model weights. No model-cache discovery occurred. Each file passed file-level reparse-point and 16MiB size checks. No claim of a recursive link-security audit.

## Hash method and source identity

PowerShell read each listed file as bytes. SHA-256 used .NET SHA256.HashData. LF bytes were computed using a lossless Latin1 byte-to-string roundtrip with only CRLF replaced by LF, equivalent to `data.replace(b'\r\n', b'\n')`. This rule was applied to every file, including all five PNG fixtures; no decoding as UTF-8, text-only exception, or on-disk normalization. Twenty-one entries have different raw/LF hashes.

After writing the new JSON, it was parsed again and all113 raw/LF pairs were recomputed against current files:113/113 exact matches; no source drift observed between those two reads. This is host hash evidence, not an atomic filesystem snapshot or proof of future image bytes. Parent and independent reviewer must stop on any later drift; no repair or normalization is authorized.

| Required identity | Raw SHA-256 | LF SHA-256 |
| --- | --- | --- |
| backend/app/workers/ocr_containment.py (W1) | 9a47c3348980b4f5d25afafce5407ed067cd974caff2b60b87d2dc5f8228dbd9 | 6129ff42c0789df51c105068cbda48d0b299885f53c491e7d3a777315661467c |
| tests/backend/test_ocr_containment.py (L1) | e72c2fb79a9bc3b0c0e08f155b5c78f16173d8e02ecc9f8349f2ecab3674af45 | 52349c96c31b6c373d8d8c99471b21df64ea5dea4a0a77f52539a884492e0f02 |

Both raw and LF identities match the explicit user pins; LF identities also match the unchanged capture constants and plan. Capture source_pins/verify_sources predicates were inspected statically, not invoked.

## Boundaries and handoff

The unchanged Dockerfile.test copies `alembic.ini` and the entire tests/backend tree in addition to the pinned source directories. Those extra context files are outside the requested113 pin scope. Parent owns the separate frozen build-context archive/manifest and its completeness; these pins alone do not attest the whole Docker context. Mill Sol/high must independently review exact pins and that context before build. No image/source equality is claimed from host hashes alone.

Only this audit and the new05 pin JSON were written. Prior03/04 checkpoints and product/source/lock/recipe files were preserved. No pytest, pure tests, Docker/build, native capture, product import, DB/model access or permission workaround. The initial scoped PowerShell membership command returned exit1 with no output; the subsequent read-only rg listings supplied membership. No source or evidence was repaired. Capture inventory remains parent-owned.

Actual verification: membership comparison, raw/LF hashing and JSON reparse/re-hash as described above. Tests/native/build: NOT_RUN. Current-source test PASS: NOT_INFERRED. Independent review and build-context checks remain pending.
