$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path -LiteralPath '.env')) {
    $randomBytes = New-Object byte[] 24
    $generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($randomBytes) } finally { $generator.Dispose() }
    $localSecret = [BitConverter]::ToString($randomBytes).Replace('-', '')
    $template = Get-Content -LiteralPath '.env.example' -Raw
    [IO.File]::WriteAllText((Join-Path (Get-Location) '.env'), $template.Replace('REPLACE_WITH_LOCAL_PASSWORD', $localSecret))
    Write-Output '.env created with a random local database password.'
} else {
    Write-Output '.env already exists; preserved.'
}
