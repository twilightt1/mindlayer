# Phase 0.3: Final cleanup of docstrings and print strings

$ErrorActionPreference = "Stop"
$root = "d:\DL\rag-backend\rag-backend"

$pyFiles = Get-ChildItem -Path $root -Recurse -Include *.py -File |
    Where-Object {
        $_.FullName -notmatch '\\(\.venv|\.git|node_modules|__pycache__)\\' -and
        $_.Name -ne '_bulk_rename_py.ps1'
    }

$updated = 0
foreach ($file in $pyFiles) {
    $content = Get-Content $file.FullName -Raw
    $original = $content

    # Docstring + print/title text replacements
    $content = $content -replace 'SupportMind Offline Eval', 'MindLayer Offline Eval'
    $content = $content -replace 'SupportMind Live API RAG Evaluation', 'MindLayer Live API RAG Evaluation'
    $content = $content -replace 'SupportMind benchmark suite', 'MindLayer benchmark suite'
    $content = $content -replace 'for SupportMind\.', 'for MindLayer.'
    $content = $content -replace 'SupportMind experiments', 'MindLayer experiments'
    $content = $content -replace 'for SupportMind', 'for MindLayer'
    $content = $content -replace 'SupportMind customers', 'MindLayer customers'
    $content = $content -replace 'supportmind knowledge base', 'mindlayer knowledge base'
    $content = $content -replace 'SupportMind\.', 'MindLayer.'

    if ($content -ne $original) {
        Set-Content -Path $file.FullName -Value $content -NoNewline
        $updated++
        Write-Host "UPDATED: $($_.FullName)"
    }
}

Write-Host ""
Write-Host "Files updated: $updated"
