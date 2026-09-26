# Focused test readiness freeze

No tests executed by this lane. Parent owns every captured execution. Windows native lane unavailable after diagnostic02; no third native probe authorized here. Existing failure evidence and prior passing captures retain their own source identities.

## Deterministic ready selection

Run these node IDs (each relative to tests/backend/):

- test_ocr_runner.py::test_unknown_stage_then_stop_memory_event_keeps_quarantine_without_fail
- test_ocr_runner.py::test_transport_rechecks_deadline_before_productive_command (3 parameters)
- test_ocr_runner.py::test_runner_serializes_large_unicode_input_as_utf8_not_ascii_escapes
- test_ocr_source_read.py::test_utf8_snapshot_near_8mib_uses_separate_input_envelope
- test_ocr_source_read.py::test_output_cap_not_enlarged_by_input_limit
- test_ocr_source_read.py::test_wire_completes_partial_header_and_payload_writes
- test_ocr_source_read.py::test_wire_nonprogressing_writer_fails_without_spinning (2 parameters)

Ten cases, no native child or DB. These are scheduling/protocol tests, not proof of OS containment.

## Linux non-pressure native ready selection

Use a dedicated, already constrained cgroup-v2 runtime; for a 512 MiB container with no extra swap set QA_OCR_NATIVE_CONTAINMENT_TEST=1 and QA_OCR_NATIVE_LIMIT_BYTES=536870912. Leave QA_OCR_NATIVE_PRESSURE_TEST unset. Existing image must contain this exact source; no source edits during capture.

- tests/backend/test_ocr_containment.py::test_native_effective_boundary_is_verified_before_workload_and_after
- tests/backend/test_ocr_containment.py::test_native_stop_of_actual_blocking_source_reader (open/read/close)
- tests/backend/test_ocr_runner.py::test_native_real_runner_deadline_and_transport_cleanup (open/read/partial/truncated/remaining)

Nine cases. Execute preflight first, then the selected supervision slice only after parent review. The runner slice retains actual _launch, explicit isolated environment, _execute, framed pipes, stage acknowledgement, stop and transport cleanup, substituting only a controlled standalone child and test memory limit. The child imports actual ocr_source via runpy and reads actual source through read_source; records entry markers and checks DB-related imports/environment. This covers the source import/input/read gate, not all qualified native adapter imports. Timeout must remain ENGINE_TIMEOUT; quarantine is not accepted as proven cleanup. Final diagnostic properties are recorded even on assertion failure.

## Not ready / retained limitations

Pressure test remains draft; do not execute it as qualification. Descendant completion marker can precede pressure; short-peak duration is unavailable if the allocator is killed, and file-mapped pressure may be reclaimed without a breach. A cgroup event alone cannot prove a peak lasted less than 250 ms. Parent/container exit137 must remain raw failed evidence without invented JUnit. Windows shared/file-mapped/native-thread enforcement remains unqualified.

Actual realrunner tests remain gated. The qualification-only admission provider injection is explicitly not production readiness and is shared by API and runner.

## Frozen SHA-256

- test_ocr_runner.py: ce19f02cffe361236cf18408e2cfd8a51d5b224bebc6c5d2e0ada196ba614d00
- test_ocr_source_read.py: a267eaee13cd7dc9e5bf4192e476753a158ce080caee7a0b1bea8b69d7bef5ad
- test_ocr_containment.py: c9560fead64ad7fc7d6a1ed395f194b97101c346b7689dd2fa0b5c3d8bb6d0ae
- test_ocr_runtime_db.py: fb73c8ffe0206e612113d53587e55a647e86727a3385ad81ae06cad7d6a0b4b5
- test_ocr_runtime_integration.py: 98f7737d2db4c8e624b6d6abac0658c4c5295801238412eabd9a2ae68f2a5fbf

Whitespace check: git diff --check returned exit0. No pytest/collection/AST/native workload executed for this readiness review.
