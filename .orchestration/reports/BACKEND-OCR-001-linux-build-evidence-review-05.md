# Linux build evidence crosscheck 05 / Backend03 sidecar

Status: recorded build/metadata evidence consistent within the eight authorized input files. Supplements the completed Mill prebuild gate; grants no new execution approval.

- build-before records build_attempts=0; build-result records build_attempts=1, exit_code=0 and BUILD_AND_METADATA_PASS. Recorded argv is identical: docker build --platform linux/amd64 --pull=false --progress=plain -f backend/Dockerfile.test -t qa-backend-ocr-l1:20260926-pins-d92e20493eb4 -, with context.tar as stdin. This verifies recorded attempt count, not an independent daemon history.
- Recorded time: 2026-09-25 16:22:02.840677 UTC through 16:23:40.721142 UTC. Pins SHA d92e20493eb42a3d4d2702b17c3d5559c17cad78e31b364387039e649146f2bc; completed prebuild review SHA d009d91ca5c33f55122825b15b86706698a4e575142f7253841583383592e566. These are recorded identities; those separate files were not reread.
- Recomputed build.log raw SHA matches build-result.build_log_sha256 exactly. Log shows image export completion and build-time pip check reporting “No broken requirements found.” Neither is a product-test result.
- Compared build-before.source_before, build-result.source_before and build-result.source_after: each has139 entries, every raw/LF pair matches, no differing or missing entries. All15 distinct paths listed in parent-context-audit.previous15_paths are included. No duplicate source rehash was performed.
- Parent audit records unchanged historical Dockerfile.test, requirements.lock and pyproject.toml hashes and pre-freeze139 verification. These are parent-recorded provenance, not a fresh context/archive audit by this sidecar.
- Saved image-inspect stdout parses to ID sha256:a1337c5556ab00f01dac45075f6bbf71ba9198c1b179a83d0210e5879a426d0a, linux/amd64; ID, RepoDigests and platform match build-result. Inspect exit0; stderr empty. Build log exports this same manifest-list digest. Its separate config digest is sha256:0e77a02ec7416ae4eeca6242bd589b8311acc4f1fc1849a0bd57e3a214581bcc; do not substitute config digest for the recorded inspected ID.
- Base pre-inspect exit1 has newline-only stdout and “No such image: python:3.12.14-slim-trixie” stderr. This establishes missing local pre-inspect metadata, not a failed build or verified base image ID. Actual build log FROM/resolution records docker.io/library/python:3.12.14-slim-trixie@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9.

All input paths below are under .orchestration/reports/BACKEND-OCR-001-linux-build-evidence-05/. SHA-256 values were computed from raw bytes.

| Input | SHA-256 |
| --- | --- |
| build-before.json | aaa7b40af9e5ecbbdbf01c9739f4b9807794896bb8a031644ecdef1f90f2ee2d |
| build-result.json | 4f2f7e0792b76e24125b3cf6f76808865e5e119e9ba6a4c0bb589b7aeea53b27 |
| build.log | 209762ed893e1be9627c02334f4903b8f46bbebf939b7a85e93f44f020cc540f |
| image-inspect-stdout.log | b7a38a0fe03e21666d67c0c6864e1fa2c725458d88eca63d0e094867845642ab |
| image-inspect-stderr.log | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| base-inspect-stdout.log | 01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b |
| base-inspect-stderr.log | 909c374f60eb4da23a22bc5c28dc22d0f5c74f58a7be0fdc0186a96d5de140f5 |
| parent-context-audit.json | 023b64fc536d969880ce9e7681dbad82a29302f42e5f7441686cbd2e44c05cfb |

Limits: image-internal source verification remains NOT_VERIFIED/NOT_RUN, as the result and parent audit explicitly record. Host recorded equality and successful COPY/build do not prove image-internal raw/LF equality. Native execution remains NOT_RUN. No Docker/build/tests/product import/native/model/DB command or source rehash was performed for this review. Only this new report was written; prior evidence remains immutable. No runtime qualification, AC promotion or further execution authorization is inferred.
