# Linux capture artifact audit 08 / Boole packaging

Packaged only the two parent-confirmed stable08 directories, nonrecursively. Actual model unverified. Twelve files: five outer (command.json, preflight.json, result.json, stdout.log, stderr.log), seven inner (capture.py, source-pins.json, manifest.json, inner-inputs.json, result.xml, terminal.json, container.log). Expected missing files: none. Raw sizes/SHA-256 are in BACKEND-OCR-001-linux-capture-artifacts-08.json, SHA-256 ddb71bde473b427aff882c45fdcbd8dec1e5d7c4f2851db0aa9c9635be484a22.

All four manifest artifact hashes, two outer log hashes and script/pin snapshot hashes match recomputed raw-byte hashes. terminal.json equals manifest.natural_terminal. Outer logs are present and empty. Inner-inputs records observer PID1, the selected shortpeak node and113 source hashes; no source rehash was performed by this packaging.

Actual JUnit: one testcase, one FAILED, zero errors/skips/passes. Failure is “fixed headroom precondition”: observed headroom20561920 bytes is below required64MiB (67108864); allowed upper bound160MiB. Container log independently reports the same assertion and one failed test. No successful pressure/enforcement result is inferred.

Manifest status remains UNPROVED_OBSERVER_EXIT. Natural terminal records exited/running=false, exit1, oom=false. This generic status is not OOM death. Outer result records capture-child exit2 and one attempt; Docker wait command itself exited0 while reporting container exit1.

Cleanup is separately recorded: JUnit owned_tree_stop_confirmed=True and observed_cleanup_seconds=0.03088249099528184; manifest cleanup_confirmed=true, launch_uncertain=false, stop_requested=false. Exactly one plain rm of e09a6dde9cdf0ea91be9c3b2ea00abe646f96c77ba2aaec3deeca9f328f296a6 records exit0 and returns the full ID. There is no stop command in the manifest. These cleanup facts do not turn the failed test into PASS; no live state or additional absence query was performed.

Raw evidence unchanged; original06/07 untouched. Only the new08 artifact JSON and this audit were written. No Docker, tests, native execution, product import, model/DB access, source rehash or recursive search of other directories. No qualification/AC promotion or new execution approval. Parent integration and independent review remain separate.
