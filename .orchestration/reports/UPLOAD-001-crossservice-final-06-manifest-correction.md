# UPLOAD-001 cross-service Backend manifest correction

Date: 2026-09-25 KST. This is a report-only supplement to `.orchestration/reports/UPLOAD-001-crossservice-final-06.md`, SHA-256 `a6b0c34fefefba6949117067e0f862dd1e0f085cda57da42d12d5b276b2601e0`.

## Correction

The cross-service report records Backend aggregate `d1799260941c7396c4e3931f21eb07e4857e90f7075d84fba962a1f5b672a0fe`. That value used culture-sensitive PowerShell `Sort-Object` ordering and is superseded.

The canonical Backend source manifest is `.orchestration/reports/BACKEND-UPLOAD-001-rework-source-manifest.txt`. It contains exactly 75 UTF-8 lines in `relative/path sha256` form, uses slash-normalized paths, Python ordinal string ordering, and one final LF. Its file SHA-256 and canonical source aggregate are:

`1464c7678cf044f0da996c19cc0174dc31581306e7c011ba98ff1e5d1dc754e5`

The exact generator and correction rationale are preserved in `.orchestration/reports/BACKEND-UPLOAD-001-rework-manifest-addendum.md`, SHA-256:

`e89185a0c8f036d5bcb3a28f048167cc3bbe1c63ecb076b6dfd20e1ec6aa43c5`

Both artifact hashes and the 75-line count were independently checked before this supplement was written.

## Unchanged evidence

This correction changes only the Backend aggregate attribution in the cross-service report. The following evidence remains valid and unchanged:

- cross-service live result: 1 collected, 1 passed in 3.15s;
- Backend final service hash: `backend/app/services/screenshots.py` SHA-256 `3c5e36450160f57f732071f8c9bf4eed5684c978e887f499264eee1f50dc7a2b`;
- Backend storage hash: `backend/app/storage/local.py` SHA-256 `ca93d0dce1418ee0db6b2868fdda5c1328e2cf1958411cb0df2214219f370afc`;
- uploader/test manifest aggregate: `593e1925a36e55b667c752be7cc10ea944f14cf81f034f5d112d23358f7a563e`;
- discarded 201, Backend and uploader restart, exact 200 replay, single receipt/Screenshot/object, and list/detail/content/hash assertions;
- all per-file Backend hashes, image digest, commands, environment details, isolation statements, and cleanup evidence.

No product source, test, original report, PM state, contract, service, database, commit, push, or IP check changed. No test rerun was performed or required. This supplement does not self-accept any task or acceptance criterion.
