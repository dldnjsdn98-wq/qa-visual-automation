# BACKEND-UPLOAD-001 rework source-manifest addendum

Date: 2026-09-25 KST. No source file or test result changed for this addendum.

The rework report's source aggregate `d1799260941c7396c4e3931f21eb07e4857e90f7075d84fba962a1f5b672a0fe` was produced with PowerShell `Sort-Object`, whose culture-sensitive ordering is not the submitted Python ordinal-sort rule. It must not be used as the canonical source aggregate.

The canonical per-file manifest is `BACKEND-UPLOAD-001-rework-source-manifest.txt`. It contains exactly 75 UTF-8 lines in the form `relative/path sha256`, paths normalized to `/`, sorted by Python's ordinal string ordering, and one final LF. Its file SHA-256, which is also the corrected source aggregate, is:

`1464c7678cf044f0da996c19cc0174dc31581306e7c011ba98ff1e5d1dc754e5`

Exact generation command from repository root:

```powershell
& 'C:\Users\dldnj\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -c "import hashlib,pathlib,subprocess; paths=subprocess.check_output(['rg','--files','backend','tests/backend'],text=True,encoding='utf-8').splitlines()+['pyproject.toml']; paths=sorted({p.replace(chr(92),'/') for p in paths}); data=('\n'.join(f'{p} {hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()}' for p in paths)+'\n').encode('utf-8'); out=pathlib.Path('.orchestration/reports/BACKEND-UPLOAD-001-rework-source-manifest.txt'); out.write_bytes(data); print('count='+str(len(paths))); print('aggregate='+hashlib.sha256(data).hexdigest())"
```

Observed output:

```text
count=75
aggregate=1464c7678cf044f0da996c19cc0174dc31581306e7c011ba98ff1e5d1dc754e5
```

This correction supersedes only the aggregate value in the rework report/handoff. The listed individual source hashes, image digest, test commands and results remain unchanged. No source drift, product edit or test rerun is inferred.
