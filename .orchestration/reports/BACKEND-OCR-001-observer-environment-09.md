# Child environment extraction / Fermat Sol high

Status: BLOCKED_SOURCE_WRITE; NOT IMPLEMENTED. Requested Sol/high; actual model
unverified. Read PM PHASE-3-linux-observer-refactor-01 and Architect
ARCH-OCR-linux-headroom-reassessment-02 before the one authorized ordinary write.

Exclusive intended files: backend/app/workers/ocr.py and new
backend/app/workers/ocr_child_environment.py. No other source/test ownership taken.
New API was coordinated to Galileo and Descartes as:
`from backend.app.workers.ocr_child_environment import child_environment`.
The runner would import/re-export that same name without changing call sites.

## Exact write result

The existing runner hash matched the supplied baseline. Inspection found mixed
line endings (320 CRLF in378 LF terminators); its child_environment definition
uses CRLF. The prepared in-memory transformation copied the exact function text,
added only import os to the new helper, removed the old definition, and inserted
one runner import. UTF-8 round-trip bytes were checked before any write. No whole
file line-ending normalization was intended.

The first ordinary write attempted FileMode.CreateNew/FileAccess.Write for
`C:\Dev\qa-visual-automation\backend\app\workers\ocr_child_environment.py`.
PowerShell exited1 at File.Open with:
`Access to the path 'C:\Dev\qa-visual-automation\backend\app\workers\ocr_child_environment.py' is denied.`

Stop-on-error prevented the subsequent runner write from being reached. No retry,
escalation, alternate writer, ACL change or permission bypass was attempted. This
was a filesystem access-denied result, not an automatic approval-review rejection.

## Readback / exact state

- New helper: absent (Test-Path False), no new raw/LF hash exists.
- Runner raw SHA256 remains
  `115cbbf2d685f4d637b2f4a352cb0ba67e064058583b460b48218bf580622a82`.
- Parent baseline ocr-before.py has the same raw SHA256.
- Runner canonical LF SHA256 remains
  `beb0151967587f2197089f3119dd423623b8c642f590e7b7647500a85f723e2f`.
- Resulting product diff: none. Equivalence of an implemented extraction cannot
  be claimed because no extraction was written. Existing implementation unchanged.

Parent, Galileo and Descartes received the denial/state/API message. Galileo must
not pin baseline runner as an applied refactor or invent a helper identity. Parent
owns disposition and any future explicitly authorized source action. Independent
test-author work may continue, but integrated tests/imports/candidate readiness
remain held until actual helper/runner source exists and is reviewed.

No tests, module imports, Python/AST, Docker/native/DB/model operations were run by
this lane. Only authorized read-only content/hash checks and the failed ordinary
source creation were attempted; this own report records their outcome. No change
to containment, fixtures, recipes, locks, profiles, contract or numerical oracle.

## Later authorized prospective-only evidence

Parent explicitly authorized in-memory generation/AST/equivalence after the source
denial. Static generator used `.pytest_cache/agent-clean-win/Scripts/python.exe -`
with stdin source, importing only ast/difflib/hashlib/json/pathlib. It read the
baseline, constructed strings in memory, parsed AST (never compiled/executed or
imported prospective modules), and wrote only this lane's .patch and JSON evidence.
Exit0. No source write was retried. Helper remains absent and runner still matches
the baseline byte-for-byte after generation. Earlier NOT_RUN AST status above
describes the initial denied-write step; the following static checks are now done.

- Unified patch: BACKEND-OCR-001-observer-environment-09.patch,
  SHA256 `db3e8a330827c8ca8661677d74ccfe33c1febd39f70d0600c156e74fe49f3b31`.
- Machine-readable prospective facts:
  BACKEND-OCR-001-observer-environment-prospective-09.json.
- Prospective runner raw: `b2fed1ebec25069821e3ddcd3f7c7368375dbf810575c232dad005b55a4fd314`.
- Prospective runner LF: `3eecadf757f4ad945f67ff02c7f4347efda342e491ed85250780010d7d55d9f1`.
- Prospective helper raw: `4329d761e0885c40635abe4eba7c1f99114b7dd5ccfc6bb2a52492cad4d757eb`.
- Prospective helper LF: `06f2ca8428fca1740d77b3b9dd7515eeecbf28d9760cc87b3688f6501fd23c0d`.

These are UNAPPLIED identities, not on-disk product hashes. Static parsing of both
prospective modules passed. Exact function text and AST are equal to baseline;
new helper top-level nodes are only import os and that function. Removing the old
definition and the proposed single re-export import gives identical runner ASTs.
All unaffected runner byte sequences and mixed line endings are preserved by the
in-memory replacement. No git apply/check, module import, pytest or runtime check
was performed in this lane. Parent retains source application and execution gates.

## Exact failed ordinary-write command attribution

Tool: tools.exec_command via functions.exec, PowerShell, workspace cwd,
default sandbox, no escalation. Exit1. The submitted command was:

```powershell
$ErrorActionPreference='Stop'
$refactorRoot=(Get-Location).Path
$runnerPath=Join-Path $refactorRoot 'backend/app/workers/ocr.py'
$helperPath=Join-Path $refactorRoot 'backend/app/workers/ocr_child_environment.py'
$utf8NoBom=[Text.UTF8Encoding]::new($false,$true)
$runnerBytes=[IO.File]::ReadAllBytes($runnerPath)
if ((Get-FileHash -LiteralPath $runnerPath -Algorithm SHA256).Hash.ToLower() -ne '115cbbf2d685f4d637b2f4a352cb0ba67e064058583b460b48218bf580622a82') { throw 'Runner baseline drift; no write attempted' }
if ([IO.File]::Exists($helperPath)) { throw 'New helper already exists; no write attempted' }
$runnerText=$utf8NoBom.GetString($runnerBytes)
if ([Convert]::ToBase64String($utf8NoBom.GetBytes($runnerText)) -ne [Convert]::ToBase64String($runnerBytes)) { throw 'UTF8 byte roundtrip mismatch; no write attempted' }
$functionStart=$runnerText.IndexOf('def child_environment(scratch):')
$classStart=$runnerText.IndexOf('class OCRRunner:', $functionStart)
if ($functionStart -lt 0 -or $classStart -le $functionStart) { throw 'Function boundary mismatch' }
$exactFunction=$runnerText.Substring($functionStart,$classStart-$functionStart)
$importAnchor='from backend.app.workers.ocr_runtime import DeadlinePolicy, OneOperation, load_metadata'
if (($runnerText.Split([string[]]@($importAnchor),[StringSplitOptions]::None)).Count -ne 2) { throw 'Import anchor mismatch' }
$runnerAfter=$runnerText.Remove($functionStart,$classStart-$functionStart).Replace($importAnchor,('from backend.app.workers.ocr_child_environment import child_environment' + "`r`n" + $importAnchor))
$helperAfter='import os' + "`r`n`r`n`r`n" + $exactFunction.TrimEnd([char[]]"`r`n") + "`r`n"
$helperStream=$null
try {
  $helperStream=[IO.File]::Open($helperPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
  $helperBytes=$utf8NoBom.GetBytes($helperAfter)
  $helperStream.Write($helperBytes,0,$helperBytes.Length)
} finally { if ($null -ne $helperStream) { $helperStream.Dispose() } }
'HELPER_SINGLE_WRITE_OK'
[IO.File]::WriteAllBytes($runnerPath,$utf8NoBom.GetBytes($runnerAfter))
'RUNNER_SINGLE_WRITE_OK'
```

Reported failure: ParentContainsErrorRecordException at line22, File.Open,
`Access to the path 'C:\Dev\qa-visual-automation\backend\app\workers\ocr_child_environment.py' is denied.`
Neither success marker was emitted. Runner write was not executed. This command
is a historical record, not permission or a request to repeat it.

## Final prospective raw files (not importable product changes)

Per explicit parent authorization, saved exact proposed bytes only under reports:

- BACKEND-OCR-001-observer-environment-proposed09.py: raw
  `4329d761e0885c40635abe4eba7c1f99114b7dd5ccfc6bb2a52492cad4d757eb`,
  LF `06f2ca8428fca1740d77b3b9dd7515eeecbf28d9760cc87b3688f6501fd23c0d`.
- BACKEND-OCR-001-runner-proposed09.py: raw
  `b2fed1ebec25069821e3ddcd3f7c7368375dbf810575c232dad005b55a4fd314`,
  LF `3eecadf757f4ad945f67ff02c7f4347efda342e491ed85250780010d7d55d9f1`.

Readback equalled prepared bytes and previously recorded hashes; original mixed
runner line endings remain preserved. Actual runner baseline was rechecked and
helper still absent. No import/compile/exec of either proposal, source retry or
permission action. Parent/PM retains implementation HOLD; Mill reviews proposals.
