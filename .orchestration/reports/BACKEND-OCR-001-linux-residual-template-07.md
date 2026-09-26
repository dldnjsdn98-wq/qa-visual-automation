# Backend03 separate residual recovery and template candidate 07

Task BACKEND-OCR-001 / P3-RUNTIME-001. Status: EXACT_RESIDUAL_REMOVED_ABSENCE_CONFIRMED; candidate static preparation only, native rerun HOLD. Authority PHASE-3-linux-residual-cleanup-01.md. Branch/commit null.

## Separate actual recovery

Original capture06 failed after create because ungrouped label index expressions gave json three arguments; its original manifest remains SHAcd519e114459fe5ee07967b9a536fd8ae4660a6514762f183df61e4008381eb5 and original status UNPROVED_OWNERSHIP_OR_CLEANUP. Recovery07 is separately authorized and does not retroactively turn that attempt into PASS.

Recovery script SHAae059f5dab376b099e9dd422421176847e3c4c82032f2975069a9a3f3382f72e passed parent AST and Mill exact prereview9d3ef2cf501c8d505d3f1abc8cd27df4026c12c7bf91b1951740c604da1c2b17. Parent rechecked both hashes and fresh evidence directory before issuing one ordinary require_escalated tool invocation:

`.pytest_cache/agent-clean-win/Scripts/python.exe -E -B .orchestration/reports/BACKEND-OCR-001-linux-residual-cleanup-07.py --review-sha256 9d3ef2cf501c8d505d3f1abc8cd27df4026c12c7bf91b1951740c604da1c2b17`

Actual tool exit0 (chunk586c09), result EXACT_RESIDUAL_REMOVED_ABSENCE_CONFIRMED, removed=true, absence_confirmed=true, original_manifest_unchanged=true. Parent independently rehashed the original manifest afterward and confirmed exact equality, rather than relying on exit0 or the script flag alone.

Exactly three bounded10s commands occurred:

1. Narrow full-ID formatted inspect exit0. ID affc94c2fe2468fd867c1e80be5878836a9b70868e68f2bff4f54d9c84988e8a, name /qa-l1-3e363b492d1347efbbae6d4de1541353, owner BACKEND-OCR-001-L1-capture-03, nonce3e363b492d1347efbbae6d4de1541353 and requested .Config.Image all matched. Running=false/status=created, both timestamps0001-01-01T00:00:00Z, exit0/OOM=false, memory=swap536870912/networknone/read-only=true. These facts were saved and file-fsynced before removal.
2. Ordinary docker rm exact full ID, exit0/full-ID stdout, no force or volumes.
3. One exact-ID inspection, exit1 with newline-only stdout (strip-empty, not zero bytes) and exact `Error response from daemon: No such container: FULL_ID` stderr. This specific absence evidence establishes removal; a generic nonzero/timeout/daemon error would not.

Both requested .Config.Image and returned .Image were saved as separate fields and actually equaled sha256:a1337c5556ab00f01dac45075f6bbf71ba9198c1b179a83d0210e5879a426d0a in this environment. Do not relabel the observed .Image as exported config0e77 or claim a mismatch that did not occur. The build exported config digest and manifest-list digest remain distinct provenance. No image filesystem/source verification is inferred from either field.

Evidence directory BACKEND-OCR-001-linux-residual-evidence-07 preserves raw stdout/stderr and command/timeout/exit records for every step, validated pre-removal facts and result. Parent audit linux-residual-parent-audit-07.json records independent original-hash preservation and result checks. No start/stop/kill, broad list/prune, image deletion, capture retry, environment/ACL/security change or third-party cleanup occurred. Host bind evidence and image were preserved.

## Unapplied minimum template candidate

After recovery disposition, parent authored separate candidate linux-template-candidate-07.py SHAe669d74fc1f683ad57cf3792860910f65198cbed3f6d0dee91232c36e36d082c and unapplied patch SHA91b45f31aaad4efb8fbb9032d76623ad8cae422f0d57701055e7678986ce9802. Frozen original d0a8e756cdd4cafc394d12a68e527632365aeaf43f6d9ca8cc063763db21d7fd remains unchanged. Only owner and nonce expressions in the shared inspect formatter gain parentheses: json(index...) is represented as `{{json (index .Config.Labels "qa.visual.owner")}}` and analogous nonce. No resource, source/image pin, timing, ownership or cleanup predicate changed.

Static regression evidence linux-template-static-07.json: AST PASS; exactly two changed field strings; reverse replacement recovers exact original LF source; old owner/nonce expressions each have three top-level json arguments, corrected expressions each one; all14 formatted fields have one argument. The checker respects quoted strings and parentheses for this fixed grammar. It is a limited static grouping check, NOT a full Go interpreter, Docker invocation or candidate import/execution. The successful separate recovery demonstrates its own grouped template only; it is not an executed test of the new capture candidate.

## Review and remaining gates

Reused Mill requested Sol/high for recovery prereview, saved-outcome and candidate static review; reused Boole requested Terra/high for new recovery artifact hashes. Actual served model identities remain unverified. Parent retained its existing model as authorized. Original06 independent HOLD and15-artifact packet remain immutable. Original pressure testcase and image-internal raw/LF verification remain NOT_RUN; no pure12/279 repeated. No Windows hook/fourth native probe,DB/model invocation or commit/push/deploy. Windows3/historical cleanup2 unchanged;04/08/admission/allP3AC held.

Final independent outcome/candidate reviews and own07 immutable manifest accompany this report. PM owns any future candidate activation; this packet authorizes no Docker/native reexecution. A separate recovery success resolves the residual only, not L1 runtime qualification.

Final independent outcome review PASS_SCOPED_RESIDUAL_RECOVERY, SHAb3d5ac7771fa23ac0f7ee87c36b5a255c20df46441a320b696f77c2899421d3a. Final candidate review PASS_STATIC_CANDIDATE, SHA622cab6b7d1c70523987749397d86a2d4fdd907fde23d1b280862c8a7baeb7e1. Boole11-artifact residual index SHAb4b2bbbb847ebe3a6f230691c2a8507233c56a15bb5dfe1e986bc7e536b2ac14; auditce47eafe817605d040f49b7da98f1cefa2d5f6cbf376810824e9d46cf11e48b1. PM separately verified original preservation and the saved three-command sequence. Postinspect stdout is one newline byte, not a zero-byte log; the strict predicate compares stripped content.

Final own packet linux-residual-template-manifest-07.json includes recovery/code/reviews/candidate/static evidence and this report/handoff, excludes itself. All authorized07 recovery and preparation work is complete. Further execution remains explicitly unapproved; next owner PM.
