# BACKEND-UPLOAD-001 — JCS dependency spike

Date: 2026-09-25 KST

Owner: 03 Backend

Status: **spike complete; dependency recommendation ready; product implementation remains BLOCKED**

Difficulty: **중** — bounded package provenance, cross-platform Python 3.12 execution, and canonical-byte verification in disposable environments

Requested model: `gpt-5.6-sol` / `medium`

Actual model: **unverified**; requested dispatch values exist, but no runtime metadata proves the executing model

Branch / commit: null / null; no commit or push

## 1. Decision

Recommend **`rfc8785==0.1.4`** as the Phase 2 JCS serializer, paired with a separate strict JSON parser/domain-validation layer owned by the application.

The package passed the executed RFC 8785/F23 serializer vectors on CPython 3.12.14 on Windows and Linux with identical canonical bytes and hashes. It also rejects non-finite floats, unsafe Python integers, residual surrogates, and non-string object keys. It does not parse raw JSON, so duplicate-key and raw numeric-token checks remain parser responsibilities; that separation is intentional and is not a package defect.

This report authorizes no shared or product edit. `pyproject.toml`, `backend/requirements.lock`, future uploader lock, Backend code, tests, DB, and services remain unchanged. The contract product implementation remains BLOCKED pending corrected-contract acceptance and PM READY/file claims.

## 2. Scope and disposable environments

The spike used only a temporary workspace directory, a disposable Windows virtual environment, and disposable Linux containers. Downloaded artifacts and temporary scripts/environments were removed after evidence capture. Network access was limited to package/repository metadata and artifacts through the normal approval path; no IP connectivity check was performed.

Executed platforms:

| Platform | Runtime | Environment | Result |
| --- | --- | --- | --- |
| Windows | CPython 3.12.14 | temporary `venv`, local downloaded wheels, `pip check` | PASS |
| Linux | CPython 3.12.14 / GCC 14.2.0 | disposable `qa-backend-test-runtime:local` container, read-only artifact mount | PASS |

The downloaded candidate wheels are pure-Python `py3-none-any` artifacts. The same bytes and SHA-256 were used for Windows and Linux; there are no separate native platform wheels to select.

## 3. Candidate provenance and comparison

Metadata was read from exact wheel contents and PyPI release JSON. Repository activity was read from the public repository API on 2026-09-25.

| Candidate | Python / runtime dependencies | License | Maintenance evidence | Executed finding | Decision |
| --- | --- | --- | --- | --- | --- |
| `rfc8785 0.1.4` | `>=3.8`; no runtime dependencies | Apache-2.0 from wheel `LICENSE`; PyPI legacy license field is null | PyPI release 2024-09-27; source repository not archived and pushed 2026-09-16 | all selected serializer/F23 and six packaged upstream reference vectors PASS on Windows/Linux; unsafe Python int rejected | **recommended** |
| `jcs 0.2.1` | `>=3.6.2`; no runtime dependencies | Apache-2.0 | PyPI release/source push 2022-04-10; repository not archived | selected canonical bytes match `rfc8785`; unsafe Python integer is converted through float and is not rejected by serializer | conditional fallback only |
| `canonicaljson 2.0.0` | `>=3.7`; no runtime dependencies | Apache-2.0 | PyPI release 2023-03-15; repository not archived and pushed 2026-05-06 | fails UTF-16 key order, negative-zero canonicalization, and `1`/`1.0` equivalence | reject for RFC 8785 |
| `json-canonical 2.0.0` | `Requires-Python` absent in inspected metadata | Apache metadata is less consistent; no matching source tag | delegated review found last source activity in 2021 | parent did not install or run it; weaker provenance and no Python 3.12 evidence | reject / NOT_RUN locally |

Source references:

- `rfc8785`: `https://github.com/trailofbits/rfc8785.py`, release source tag `v0.1.4`; package documentation identifies a pure-Python RFC 8785 implementation.
- `jcs`: `https://github.com/titusz/jcs`, release source tag `v0.2.1`.
- `canonicaljson`: `https://github.com/matrix-org/python-canonicaljson`, release source tag `v2.0.0`; its own implementation states that keys are sorted by Unicode code point, which is not JCS UTF-16 order.

## 4. Exact artifacts and hashes

PyPI-declared SHA-256 values matched locally downloaded bytes.

| Package | Artifact | Size | SHA-256 |
| --- | --- | ---: | --- |
| `rfc8785 0.1.4` | `rfc8785-0.1.4-py3-none-any.whl` | 9,240 | `520d690b448ecf0703691c76e1a34a24ddcd4fc5bc41d589cb7c58ec651bcd48` |
|  | `rfc8785-0.1.4.tar.gz` | 14,321 | `e545841329fe0eee4f6a3b44e7034343100c12b4ec566dc06ca9735681deb4da` |
| `jcs 0.2.1` | `jcs-0.2.1-py3-none-any.whl` | 7,603 | `e23a3e1de60f832d33cd811bb9c3b3be79219cdf95f63b88f0972732c3fa8476` |
|  | `jcs-0.2.1.tar.gz` | 6,886 | `9f20360b2f3b0a410d65493b448f96306d80e37fb46283f3f4aa5db2c7c1472b` |
| `canonicaljson 2.0.0` | `canonicaljson-2.0.0-py3-none-any.whl` | 7,921 | `c38a315de3b5a0532f1ec1f9153cd3d716abfc565a558d00a4835428a34fca5b` |
|  | `canonicaljson-2.0.0.tar.gz` | 10,716 | `e2fdaef1d7fadc5d9cb59bd3d0d41b064ddda697809ac4325dced721d12f113f` |

For reproducible production locks, prefer the reviewed universal wheel and its one hash:

```text
rfc8785==0.1.4 \
    --hash=sha256:520d690b448ecf0703691c76e1a34a24ddcd4fc5bc41d589cb7c58ec651bcd48
```

The sdist hash is recorded for provenance, not as a recommendation to permit source builds. No native build toolchain is needed by the selected wheel.

## 5. Parser and serializer responsibility split

The production pipeline must preserve raw-token evidence before calling `rfc8785.dumps()`:

1. Decode strict UTF-8 and JSON.
2. Use `object_pairs_hook` or an equivalent token-preserving parser path to reject duplicate keys at every depth, including escaped-equivalent spellings.
3. Use `parse_int`, `parse_float`, and `parse_constant` equivalents to reject NaN/Infinity, binary64 overflow, nonzero underflow to zero, and every resulting integral value outside `[-9007199254740991, 9007199254740991]`.
4. Recursively reject U+0000 and residual surrogate code points and preserve every other Unicode scalar without normalization.
5. Apply typed/default/filename normalization from the accepted contract.
6. Pass only the validated Python value to `rfc8785.dumps()`; store its returned bytes directly in `canonical_request BYTEA` and hash those exact bytes.

Serializer duplicate detection was deliberately not tested on an already-created `dict`: duplicate evidence no longer exists at that boundary. `rfc8785` was instead evaluated for its serializer responsibilities. Its own rejection of unsafe Python integers, non-finite floats, surrogate values, and non-string keys is useful defense in depth.

`jcs 0.2.1` can emit the selected canonical bytes after strict parsing, but direct unsafe integer input is converted through binary64 and accepted. This does not make serializer-only duplicate detection a requirement; it does make `jcs` less defensive than `rfc8785` at the application boundary.

## 6. Executed F23 vectors

The same harness file bytes (`SHA-256 9bb6fabfca50f8f755bb0a655d9da6135affd51de74c860aa79883f6f21778a1`) ran on Windows and Linux. Both platforms produced identical JSON Lines results.

### Serializer checks

`rfc8785 0.1.4` passed all selected checks on both platforms:

- UTF-16 order with U+1F600 before U+E000 at root and nested depth;
- RFC numeric sample `333333333.33333329 -> 333333333.3333333`, `1E30 -> 1e+30`, `4.50 -> 4.5`, `2e-3 -> 0.002`, and `1e-27 -> 1e-27`;
- negative zero to `0` and `1`, `1.0`, `1e0` to identical `1`;
- control-character escaping, exact Unicode/no normalization, no BOM or trailing newline;
- rejection of NaN, positive infinity, residual surrogate, and unsafe Python integer.

The compact cross-platform fixture produced:

- canonical hex: `7b226e223a5b312c302c22c3a9222c2265cc81225d2c22f09f9880223a312c22ee8080223a327d`
- SHA-256: `2f2a481c62979b5efb2b700dc0f6d08ef6e6dff6786eb2d7b040dcea201ca4cf`

The complete synthetic fingerprint payload defined by contract fields produced identical `rfc8785` and `jcs` bytes on both platforms:

- byte length: `582`
- SHA-256: `a5a4938ef3aa25cc06bb29711005b0aeb1ecb0f13e898983fb9d2b0faaa009b6`
- metadata includes literal Korean, null, U+1F600, and U+E000; the supplementary key precedes U+E000.

`canonicaljson 2.0.0` produced a different fixture hash, `56c5dd0e84b108a9028f676799c228e6cb249e7d6ab1bdfef2b0580fb8e9918f`, because it emitted Python code-point key order, `1.0`, and `-0.0`. It is unsuitable despite passing the limited RFC numeric list and escape checks.

### Strict parser checks

The disposable strict parser harness passed the same acceptance/rejection matrix on Windows and Linux:

- accepted `1`, `1.0`, `1e0`, negative zero, safe maximum integer, and `5e-324`;
- canonicalized all three one forms to byte `1`;
- rejected duplicate root, nested, and escaped-equivalent keys;
- rejected NaN, Infinity, overflow, `1e-4000` nonzero underflow, unsafe integer, unsafe integral float, U+0000, and residual surrogate.

These checks exercise the required division: the parser rejects malformed/domain-invalid source before the serializer receives a value.

### Packaged upstream reference vectors

The exact `rfc8785-0.1.4` sdist includes test assets copied from the Apache-2.0 reference implementation. All six packaged input/output/outhex groups matched on Windows and Linux:

| Vector | Bytes | SHA-256 |
| --- | ---: | --- |
| `arrays` | 32 | `099601b171cafed97c333f8878d68e7f8c8f795412adb34b2fdcf0e7c7beac42` |
| `french` | 130 | `d99d0ebdcb0033cb858cfa830ae46bc0fb3309413b271f1da828c89901a27ed5` |
| `structures` | 98 | `605f65004ec2db7692522a0852c22f1c989e036d547e88963d1a3143cf3195d5` |
| `unicode` | 30 | `0d99aad92a125196ff887876643fd3206786a84ddce2cee52ba4ad256d2381d3` |
| `values` | 118 | `2d5e01a318d0f0879ab568c4be289c8b1f64ef8921a53c6277d5e069978baacb` |
| `weird` | 214 | `6af595a9aa80110b964b4de3f82a05fa6ae7423005019bacfa2620dddc4e94d1` |

The package's optional 100-million-number ES6 file is not distributed in the sdist and was **NOT_RUN**. Full project acceptance must retain focused numeric boundary cases and may add the large upstream corpus in CI only if its cost and provenance are approved.

## 7. Install and packaging result

Windows disposable venv:

- installed the exact three candidate wheels with `--no-index --no-deps`;
- `pip check`: PASS, “No broken requirements found”;
- selected wheel runtime/F23/reference vectors: PASS.

Linux disposable container:

- installed `rfc8785 0.1.4` from the same read-only wheel without index access;
- `pip check`: PASS, “No broken requirements found”;
- selected wheel runtime/F23/reference vectors: PASS.

PM packaging direction is incorporated into the future change plan:

- Phase 2 remains one unified root distribution; preserve every current base dependency.
- After explicit shared-file activation, Backend 03 is the single editor of `pyproject.toml` and should add `rfc8785>=0.1.4,<0.2` to root runtime dependencies, add `agent*` to package discovery, and incorporate role 06's approved agent `httpx` extra/request in the same serialized edit.
- `backend/requirements.lock` pins the selected exact wheel for the Backend/base environment.
- The separate role 06 lock remains a separate reproducible artifact but must include **base plus agent/test dependencies**, including the same exact JCS version, and must support a clean `pip check`. It is not an agent-only subset and is not a packaging split.
- Lock generation must use the reviewed wheel hash above and must not silently add the sdist or an unreviewed later release.

None of those future edits were made in this spike.

## 8. Limits and remaining activation checks

PASS in this spike means package installation and the recorded canonical/parser vectors passed in disposable Python 3.12 Windows/Linux environments. It is not product acceptance.

NOT_RUN or out of scope:

- malformed raw UTF-8 byte-sequence handling through the eventual multipart/parser implementation;
- the optional 100-million-number ES6 corpus;
- PostgreSQL JSONB/binary64 roundtrip and exact `canonical_request BYTEA` persistence;
- clean installation of the future full unified root distribution and both final hash-locked requirement sets;
- Backend/uploader production implementation parity, HTTP behavior, receipt creation boundaries, and all AC-P2 tests;
- any corrected-contract impact beyond current JCS section 3.

Before dependency edits, PM must accept this recommendation, activate the corrected contract, and grant Backend 03 the single serialized shared-file claim. After edits, repeat both-platform clean installs, `pip check`, F23 vectors, Backend/uploader parity, and JSONB roundtrip using committed test fixtures rather than this deleted temporary harness.

## 9. Commands and evidence classification

Executed from `C:\Dev\qa-visual-automation`:

- bundled Python `--version` and pip version: PASS (`Python 3.12.14`);
- `pip index versions` for candidates through approved network access: PASS;
- exact wheel and sdist downloads plus SHA-256 comparison with PyPI JSON: PASS;
- wheel METADATA/LICENSE/source inspection: PASS;
- Windows temporary venv install, `pip check`, F23 harness, and six packaged reference vectors: PASS;
- existing local Linux image version check, disposable installs, `pip check`, same F23 harness, and six reference vectors: PASS;
- repository archived/activity metadata lookup: PASS;
- IP connectivity checks: NOT_RUN by instruction;
- product/shared-file/lock edits, DB/services, commits, and pushes: NOT_RUN.

Two read-only delegated analyses supplied independent candidate/provenance and F23 vector design evidence. The parent independently downloaded, hashed, installed, executed, compared, and integrated the selected evidence. Delegated requested model was Sol/medium; actual model remains unverified.
