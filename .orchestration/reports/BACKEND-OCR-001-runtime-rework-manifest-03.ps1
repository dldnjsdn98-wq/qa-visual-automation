$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$taskPaths = [System.Collections.Generic.List[string]]::new()
foreach ($part in @('backend', 'tests/backend')) {
    Get-ChildItem -LiteralPath (Join-Path $taskRoot $part) -File -Recurse |
        Where-Object { $_.FullName -notmatch '[\\/](__pycache__|\.pytest_cache)[\\/]' -and $_.Extension -notin @('.pyc', '.pyo') } |
        ForEach-Object { $taskPaths.Add($_.FullName.Substring($taskRoot.Length + 1).Replace('\', '/')) }
}
$taskPaths.Add('pyproject.toml')
$taskPaths.Sort([System.StringComparer]::Ordinal)
$taskLines = foreach ($relative in $taskPaths) {
    $digest = (Get-FileHash -LiteralPath (Join-Path $taskRoot $relative) -Algorithm SHA256).Hash.ToLowerInvariant()
    "$relative $digest"
}
$taskPayload = ($taskLines -join "`n") + "`n"
$taskHasher = [System.Security.Cryptography.SHA256]::Create()
$taskAggregate = [BitConverter]::ToString($taskHasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($taskPayload))).Replace('-', '').ToLowerInvariant()
$taskHeader = @(
    'BACKEND-OCR-001 runtime-rework BLOCKED DRAFT checkpoint; not qualification',
    ('generated_utc=' + [DateTime]::UtcNow.ToString('o')),
    'sorting=System.StringComparer.Ordinal', 'path_separator=/',
    'line_format=<relative-path><space><lowercase-sha256>',
    'scope=backend/** + tests/backend/** + pyproject.toml',
    ('count=' + $taskPaths.Count), ('aggregate_sha256=' + $taskAggregate),
    'status=BLOCKED_DRAFT_NOT_READY_FOR_REVIEW', ''
) -join "`n"
$taskOutput = Join-Path $PSScriptRoot 'BACKEND-OCR-001-runtime-rework-draft-source-manifest.txt'
if (Test-Path -LiteralPath $taskOutput) { throw 'Checkpoint already exists; do not overwrite evidence.' }
[IO.File]::WriteAllText($taskOutput, $taskHeader + "`n" + $taskPayload, [Text.UTF8Encoding]::new($false))
Write-Output "count=$($taskPaths.Count) aggregate=$taskAggregate"
Get-FileHash -LiteralPath $taskOutput -Algorithm SHA256
