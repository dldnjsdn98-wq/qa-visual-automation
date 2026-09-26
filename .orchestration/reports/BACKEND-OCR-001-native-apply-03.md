# Exact candidate application and harness preparation / Backend03

Status: SOURCE_WRITE_HOLD; independent own-evidence harness preparation STATIC_COMPLETE. Native execution HOLD. Branch/commit null.

Authorization: PHASE-3-native-candidate-apply-01.md approved the exact W1 patch84a8fb80...1f9f and L1 patchd15ebab5...6639 for two files only, plus12 pure oracle cases after fixture-side-effect inspection. Concrete harness preparation is separately allowed as own evidence, without executing it. Any additional production hook needs a precise unapplied diff and separate PM claim.

## Actual application attempt and current files

Both source baseline hashes and both approved patch hashes matched immediately before the attempt. One `git apply --check <W1> <L1>` returned0. One `git apply <W1> <L1>` returned128 with two distinct messages:

```
warning: unable to unlink 'backend/app/workers/ocr_containment.py': Invalid argument
error: unable to write file 'backend/app/workers/ocr_containment.py' mode 100644: Permission denied
```

The wrapper aborted before its planned success record; `native-apply-evidence-03/exact-application-blocked-01.json` explicitly transcribes the returned command result and subsequent read-only hash check. It is not a fabricated preinstalled capture/JUnit result. Its SHA256 is `3ef1df8fb618462946962303368b5c39610569b867ee7a15ac9a8224a953adad`.

Read-only inventory `native-apply-evidence-03/partial-apply-inventory-01.json` confirms:

| File | Bytes | Actual raw / canonical LF SHA256 | Intended canonical LF SHA256 |
| --- | ---: | --- | --- |
| backend/app/workers/ocr_containment.py | 41870 | ef7d7ffe6dbc0b8f620ae9416818614cf9aa9dc5ceb822fdee11d4feca76bec5 | 6129ff42c0789df51c105068cbda48d0b299885f53c491e7d3a777315661467c |
| tests/backend/test_ocr_containment.py | 17831 | 382257cfb9747b2fe9d7aa87fedd5d50d5f853745c483be5b1764c3c958ade1b | 52349c96c31b6c373d8d8c99471b21df64ea5dea4a0a77f52539a884492e0f02 |

Both remain exactly their baseline bytes; neither matches the intended candidate. No partial application observed. Both currently have git status?? (untracked); an empty tracked git diff alone cannot establish unchanged contents, so the baseline hash comparison is authoritative. Files show Archive attribute, not ReadOnly. Declared tool filesystem context was workspace-write within the project, with no escalation requested. Host ACL/token/filesystem cause is UNDETERMINED; the relationship between unlink Invalid argument and write Permission denied is not established.

No repeated git application, alternative writer/copy/replace, ACL/security/identity change, escalation re-request or automatic restoration was attempted. PM explicitly placed the write lane on HOLD after this result; independent own-evidence work continues.

## Pure oracle verification disposition

Actual source AST contains no test_l1_shortpeak_oracle node. The12 newly proposed cases are therefore NOT_RUN, not collected elsewhere or executed from a copied/prospective replacement. No pytest was launched. Static fixture inspection found the proposed function takes only parametrized overrides/expected arguments; tests/backend/conftest.py's database/client/catalog fixtures are not autouse. Imported backend main/db code constructs a SQLAlchemy engine/session factory lazily; the selected pure function would not request DB fixtures or run API handlers. This inspection is preparation only and does not substitute for the missing applied node or claim any executed runtime/test result.

No native opt-in flags, pressure tests, full279 suite, DB, model, container or build actions were executed. Source-write resolution and renewed exact-byte verification are prerequisites before the approved pure selection can run.

## Parallel concrete harness candidates

Galileo reused Astra/medium for a startup-only Windows observer and retained-owner supervisor. A small private suspended-return hook appears necessary; it must be supplied as an unapplied proposed diff against the intended W1 canonical source, not silently added to the blocked product. Initial run remains stdlib startup only, one owned launch/stop, cleanup min(stop_request+2s,total30s), no native package imports. Existing synchronous preownership setup uncertainty must be preserved.

Fermat reused Sol/high for an outer Linux named-container capture candidate, retaining exact ID/name/nonce and natural-exit evidence before cleanup. It must target a future exact-source image rather than reuse image b, and cannot manufacture t1/JUnit/PASS after observer death. Neither harness is authorized for execution here. Independent exact reviews and concrete remaining prerequisites will be recorded below.

Windows same-cause3 and separate cleanup2, original shortpeak SKIP, all product qualification/04/08/admission/AC gates remain unchanged.

Additional evidence detail: the failing inner git apply command's stdout was empty; stderr is reproduced above, exit128. The enclosing Python guard emitted the AssertionError containing that returned result and exited1. No success application record was written because validation aborted. This distinction does not turn the failed write into a successful or partially successful application.

Independent reviewers resumed: Hooke Astra/medium for Windows hook/harness, Mill Sol/high for Linux capture. Windows early static review found late native-query completion could promote cleanup after its deadline, missing startup/close cutoff, skipped count observations when handshake failed, and missing ResumeThread==1 gating. These are unexecuted candidate findings being corrected; no new native failure/count is recorded. The additional private hook must expose ownership even if launch finalization blocks, with one post-transfer cleanup owner; it remains a separate unapplied claim, never a workaround for the source-write denial.

Cross-lane source dependency: the Linux capture candidate deliberately requires the exact W1-only helper canonical hash6129ff42...61467c plus L1 test52349c96...2e0f02. A later separately approved Windows private hook will change that same helper again. Therefore this Linux capture/pin version must not be treated as ready against the extra-hook helper; PM must preserve an appropriate frozen source sequence or separately review a repinned capture before execution. No pin is relaxed automatically and no image b fallback is allowed.

## Linux concrete capture: static preparation complete

Frozen script `BACKEND-OCR-001-native-apply-linux-capture-03.py` SHA256 `d0a8e756cdd4cafc394d12a68e527632365aeaf43f6d9ca8cc063763db21d7fd`; plan `BACKEND-OCR-001-native-apply-linux-plan-03.md` SHA256 `4d655c861b205add420a33c317aae4605037b60ea02dac53ee087aa7a3b2d595`. It requires an independently pinned future applied-source manifest and new immutable image ID, rejects old images a/b, verifies host and image source identity, and runs only the shortpeak node in a future PID1 observer. Named-container creation/start uncertainty, exact ID/name/nonce inspection, natural terminal capture before removal and one owned cleanup are explicit. Missing observer/JUnit/timing or forced stop cannot become a scoped L1 PASS.

Mill's independent static review `BACKEND-OCR-001-native-apply-linux-review-03.md`, SHA256 `43a67a75e3b203bb25cbe09cdaee16d0c115704a1f1a10fcb1d37bbb0b885c13`, PASS for prepared candidate only. An earlier missing fixed-helper pin was corrected before this freeze; arbitrary self-consistent helper hashes now fail. Parent AST-only parse PASS is recorded in `native-apply-evidence-03/linux-capture-static-01.json`; the module was not imported or executed. Source-write/pure12 HOLD, actual pin input/new image and later PM invocation/native approval remain prerequisites.

## Windows final candidate: parent static composition verified

Frozen harness SHA256 `be6b865e6ca8be5cea2bedf04bc6ed79dcdb17ed3510c165a393ee882f0d0a11`; plan `cc8fcd7ce40fe2ade92e5dcdc11208b47123fe022880589d68083e6a33227865`; proposed hook `0496d7a5cc18881d7c8fda045969a8314911b1913673dd6372ef7418600c56f3`. Earlier c37b90/b3c1 revisions are superseded. Last independent finding required successful class1 with exactly48 returned/buffer bytes before raw helper anomaly values can count as an extra process. Failed/short queries remain unknown. The candidate now explicitly enforces that condition.

Parent performed exact unified-diff context composition exclusively in memory: baseline -> approved W1 yields canonical6129ff42c0789df51c105068cbda48d0b299885f53c491e7d3a777315661467c; W1 -> proposed hook yields f9f41dc9d09f003a857d6e98c3053279b9616a346f0b34aa97309666c14c6302, matching the harness gate. AST parse of composed helper, harness and embedded child PASS. Evidence is `native-apply-evidence-03/windows-capture-static-01.json`. No prospective helper was written to product, imported or executed.

Static ownership/deadline review: ownership publishes before launcher finalization, no resume without accepted successful completion, sole supervisor stop after publication, ResumeThread==1 before handshake, separate bounded failure count observation concurrent with stop, timely direct/Job proof and handle close, and main-only final evidence snapshot. Prepublication native calls may still block, late ownership may remain unproved, and harness exit cannot prove cleanup; the candidate is explicitly not a hard native cancellation guarantee or production qualification. The additional hook is an unapplied separate PM claim.

## Final disposition and handoff

Hooke independent exact Windows review PASS for prepared static candidate only; review SHA256 `56fd9923f1b179126144e17d508ab7fe20279b533c49b80265276802b782132f`. No blocking static finding remains. Linux independent static PASS also remains valid. Requested allocation was Windows highest Astra/medium and Linux high Sol/high, with separate author/reviewer roles; actual runtime model selection was not independently verified. Integration and source-hash checks were performed by the parent.

Own-scope manifest: `BACKEND-OCR-001-native-apply-manifest-03.json`, excludes itself and includes this final report, final handoff, both candidate/review sets and four evidence records. It does not replace the historic diagnostic index or claim its denied nested evidence was audited. Current two source baselines rechecked unchanged at freeze.

Next owner is PM: determine source-write HOLD disposition, separately claim the precise Windows hook if desired, and preserve Linux W1-only source pin sequencing. Actual source application remains incomplete; pure12 NOT_RUN; both harness executions NOT_RUN. No independent-review PASS authorizes source recovery, build, native invocation or downstream admission. Backend03's authorized nonblocked preparation is complete; no additional automatic action is scheduled.
