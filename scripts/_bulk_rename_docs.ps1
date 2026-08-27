# Bulk replace MindLayer with Orivory in docs and notebooks
# Safe: only .md and .ipynb files

$ErrorActionPreference = "Stop"
$root = $args[0]
if (-not $root) { $root = "." }

Write-Host "Scanning: $root"

$files = Get-ChildItem -Path $root -Recurse -Include *.md,*.ipynb -File |
    Where-Object {
        $_.FullName -notmatch '\\(\.venv|\.git|node_modules|__pycache__|notebooks\\rag_analysis_checkpoint)\\' -and
        $_.FullName -notmatch 'rag_analysis\.ipynb$'
    }

$updated = 0
$skipped = 0

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    $original = $content

    # Brand replacements (case-sensitive order matters: do MindLayer first)
    $content = $content -replace 'MindLayer', 'Orivory'
    $content = $content -replace 'mindlayer\.local', 'orivory.local'
    $content = $content -replace 'mindlayer-demo@', 'orivory-demo@'
    $content = $content -replace 'mindlayer_', 'orivory_'
    $content = $content -replace 'mindlayer-', 'orivory-'

    if ($content -ne $original) {
        Set-Content -Path $file.FullName -Value $content -NoNewline
        $updated++
        Write-Host "UPDATED: $($file.FullName)"
    } else {
        $skipped++
    }
}

Write-Host ""
Write-Host "Total files scanned: $($updated + $skipped)"
Write-Host "Updated: $updated"
Write-Host "Skipped (no match): $skipped"
