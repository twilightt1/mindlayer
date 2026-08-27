# Phase 0.2: Update Python files + rename eval files

$ErrorActionPreference = "Stop"
$root = $args[0]
if (-not $root) { $root = "." }

# --- 1. Rename eval files ---
$oldEvalPy = Join-Path $root "eval\supportmind_offline_eval.py"
$newEvalPy = Join-Path $root "eval\orivory_offline_eval.py"
$oldDataset = Join-Path $root "eval\supportmind_eval_dataset.json"
$newDataset = Join-Path $root "eval\orivory_eval_dataset.json"

if (Test-Path $oldEvalPy) {
    Rename-Item $oldEvalPy $newEvalPy
    Write-Host "RENAMED: $oldEvalPy -> $newEvalPy"
}
if (Test-Path $oldDataset) {
    Rename-Item $oldDataset $newDataset
    Write-Host "RENAMED: $oldDataset -> $newDataset"
}

# --- 2. Bulk replace in Python files (only safe, brand-only replacements) ---
$pyFiles = Get-ChildItem -Path $root -Recurse -Include *.py -File |
    Where-Object {
        $_.FullName -notmatch '\\(\.venv|\.git|node_modules|__pycache__)\\' -and
        $_.FullName -notmatch 'rag_analysis\.py$'
    }

$updated = 0
foreach ($file in $pyFiles) {
    $content = Get-Content $file.FullName -Raw
    $original = $content

    # Brand: supportmind -> orivory local/dev references
    $content = $content -replace 'supportmind\.local', 'orivory.local'
    $content = $content -replace 'supportmind-demo@', 'orivory-demo@'
    $content = $content -replace 'app\.supportmind\.example', 'app.orivory.example'

    # MindLayer -> Orivory replacements
    $content = $content -replace 'MindLayer', 'Orivory'
    $content = $content -replace 'mindlayer\.local', 'orivory.local'

    # Demo smoke title/description
    $content = $content -replace 'SupportMind smoke ', 'Orivory smoke '
    $content = $content -replace 'SupportMind Demo', 'Orivory Demo'
    $content = $content -replace 'SupportMind demo', 'Orivory demo'

    # Eval desc strings
    $content = $content -replace 'with the SupportMind eval suite', 'with the Orivory eval suite'
    $content = $content -replace 'a SupportMind experiment sweep', 'an Orivory experiment sweep'
    $content = $content -replace 'production-like SupportMind demo', 'production-like Orivory demo'
    $content = $content -replace 'Run SupportMind RAG evaluation', 'Run Orivory RAG evaluation'
    $content = $content -replace 'SupportMind RAG Evaluation', 'Orivory RAG Evaluation'

    # Eval dataset path refs (now renamed)
    $content = $content -replace 'supportmind_eval_dataset\.json', 'orivory_eval_dataset.json'
    $content = $content -replace 'supportmind_offline_eval\.py', 'orivory_offline_eval.py'

    # MinIO/db placeholders in test fixtures
    $content = $content -replace 'supportmind-prod-minio', 'orivory-prod-minio'
    $content = $content -replace 'supportmind:strong-db-password', 'orivory:strong-db-password'

    if ($content -ne $original) {
        Set-Content -Path $file.FullName -Value $content -NoNewline
        $updated++
        Write-Host "UPDATED PY: $($file.FullName)"
    }
}

# --- 3. Update JSON dataset content ---
$datasetPath = Join-Path $root "eval\orivory_eval_dataset.json"
if (Test-Path $datasetPath) {
    $content = Get-Content $datasetPath -Raw
    $original = $content
    $content = $content -replace 'X-SupportMind-Signature', 'X-Orivory-Signature'
    if ($content -ne $original) {
        Set-Content -Path $datasetPath -Value $content -NoNewline
        Write-Host "UPDATED JSON: $datasetPath"
    }
}

Write-Host ""
Write-Host "Python files updated: $updated"
Write-Host "Done."
