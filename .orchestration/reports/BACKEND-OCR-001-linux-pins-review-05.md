# Linux pins/build-context independent review 05

Disposition: PASS for the exact frozen input packet and parent single-build gate under PHASE-3-linux-pins-build-01.md. This is static preparation/build-input acceptance, not a build result, image-internal verification, native execution approval, or production/AC admission. Requested reviewer role: reused Sol/high; actual model identity is not attested.

## Frozen identities (SHA-256)

All paths below are relative to .orchestration/reports/.

| Artifact | SHA-256 |
| --- | --- |
| BACKEND-OCR-001-linux-source-pins-05.json | d92e20493eb42a3d4d2702b17c3d5559c17cad78e31b364387039e649146f2bc |
| BACKEND-OCR-001-linux-source-pins-audit-05.md | 1edd8bfd9012e7615f230a0ead3c19cd84b73edeeaf1d3de3880617f4824dd22 |
| BACKEND-OCR-001-linux-build-evidence-05/context-manifest.json | a42bb46f1119f200cc5ee9a43363094bdc4c22db51dd8e1a2f13b1f8c96ce120 |
| BACKEND-OCR-001-linux-build-evidence-05/context.tar | 36230ae59062c2dde4575dfb1e5230b69a383d7abf1bed08366aa39a71c3a6c9 |
| BACKEND-OCR-001-linux-build-capture-05.py | 9a49a694e90f7fd733e46c21d2831f78767cbd3f1a3b49caa6ce26b46521243d |
| BACKEND-OCR-001-native-apply-linux-capture-03.py | d0a8e756cdd4cafc394d12a68e527632365aeaf43f6d9ca8cc063763db21d7fd |

## Predicate and completeness review

Read the unchanged capture source_pins/verify_sources functions; did not import or invoke them. Independently parsed the final JSON in PowerShell: schema1, exactly113 entries, all nine mandatory paths, permitted relative forward-slash paths without hidden/traversal components, and exactly sha256/lf_sha256 lowercase64-hex fields. All113 pairs equal their frozen context entries; exact membership comparison produced no differences.

The set is backend76 + worker28 + selected test/conftest2 + pyproject1 + runtime fixtures6. It fits128 and covers the selected node's local import/resource closure, including conftest -> application/router -> services/models/storage/validation and worker package initializers, profiles and schemas. The DB fixture is not autouse and the selected node requests tmp_path/mode/record_property, not database/client/catalog. Importing the DB engine definition does not itself establish a DB connection. Unrelated backend tests need not occupy capture pins; their copied bytes remain in context provenance.

W1 helper LF equals 6129ff42c0789df51c105068cbda48d0b299885f53c491e7d3a777315661467c; L1 test LF equals 52349c96c31b6c373d8d8c99471b21df64ea5dea4a0a77f52539a884492e0f02. No Windows-hook repin, predicate relaxation or normalization occurred. Raw equality remains mandatory independently of LF equality, including for binary fixtures.

## Context and build boundary

Independently inspected all139 unique manifest names and recomputed current-host raw hashes, CRLF-to-LF byte hashes, and byte lengths for all139: no mismatch. Rehashed the tar itself. Parent independently reports139/139 raw archive members match; this reviewer did not separately extract/reparse the archive. Static wrapper inspection confirms it checks ordered tar membership, regular-file type and member raw hashes before Docker. Frozen names contain no environment files, credentials, caches, model weights, or orchestration files. This is scoped membership review, not a repository-wide secret scan.

The unchanged recipe COPY closure is represented: backend, worker, tests/backend, tests/ocr/fixtures/runtime, root pyproject.toml/alembic.ini, plus .dockerignore. Root alembic.ini and .dockerignore correctly remain outside the capture's permitted pin namespace. An allowlisted tar avoids sending unrelated root data. Parent reports historical recipe/lock/pyproject equality and containment of its prior15 sources; those historical comparisons are parent evidence, not independently repeated here.

Wrapper review found no blocking issue for this exact invocation: pins/review/context/tar identities and source equality gate Docker; one build reads frozen tar stdin, uses the unchanged recipe, linux/amd64, --pull=false, and a pins-derived tag. Only restricted image metadata is inspected; no container run or retry path exists. Source-after checks cover all139 entries and drift overrides success. Invoke ordinary Python without -O/-OO or PYTHONOPTIMIZE, because gates use assert. A supplied review hash is an external gate binding, not automatic parsing of this disposition.

Base is a mutable tag and --pull=false does not forbid resolving an absent base. Retain actual build-log base resolution alongside pre-build metadata; pre-inspect alone is not proof of the resolved build base. This recipe build still uses its authorized apt/pip operations. No reproducibility or image-internal source equality is inferred from host hashes. Later capture must independently verify both raw and LF image bytes and receive its separate execution approval.

## Work performed and limitations

Only this new review file was written. Read-only source inspection, JSON/membership comparisons and hashing were performed. No product/author edits, source normalization, harness import, pytest, build, Docker, native/API probe, DB or model operation was performed. An audit-filename rg discovery encountered access-denied unrelated report subdirectories; no retry or workaround was attempted, and subsequent reads used the returned exact audit path. Build/native results remain NOT_RUN by this reviewer. Freeze applies only to the identities above; drift requires reassessment.
