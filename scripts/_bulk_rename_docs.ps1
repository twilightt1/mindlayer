# Bulk replace SupportMind with MindLayer in docs and notebooks
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

    # Brand replacements (case-sensitive order matters: do SupportMind first)
    $content = $content -replace 'SupportMind', 'MindLayer'
    $content = $content -replace 'supportmind\.local', 'mindlayer.local'
    $content = $content -replace 'supportmind-demo@', 'mindlayer-demo@'
    $content = $content -replace 'supportmind_', 'mindlayer_'
    $content = $content -replace 'supportmind-', 'mindlayer-'

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
