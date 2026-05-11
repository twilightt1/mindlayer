# Verify: list remaining supportmind references excluding intentional ones

$ErrorActionPreference = "SilentlyContinue"
$root = "d:\DL\rag-backend\rag-backend"

$results = Get-ChildItem -Path $root -Recurse -File |
    Where-Object {
        $_.FullName -notmatch '\\(\.venv|\.git|node_modules|__pycache__)\\' -and
        $_.Name -notmatch '_bulk_rename.*\.ps1$' -and
        $_.Name -ne 'REBRAND_NOTES.md' -and
        $_.Name -ne 'latest_report.json'
    } |
    Select-String -Pattern 'supportmind' -CaseSensitive:$false

if ($results) {
    Write-Host "Remaining references:"
    $results | ForEach-Object {
        Write-Host ("  {0}:{1}: {2}" -f $_.Path, $_.LineNumber, ($_.Line.Trim().Substring(0, [Math]::Min(100, $_.Line.Trim().Length)))
    )
    Write-Host ""
    Write-Host "Total: $($results.Count) references"
} else {
    Write-Host "OK: No remaining supportmind references."
}
