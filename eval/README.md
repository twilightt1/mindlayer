# RAG Evaluation Framework

This directory contains deterministic evaluation tooling for the SupportMind RAG demo.
The default evaluation is **offline and CI-safe**: it uses `sample_docs/` and does
not require the API server, database, ChromaDB, Redis, MinIO, or LLM keys.

## Components

| File | Purpose |
|---|---|
| `supportmind_eval_dataset.json` | Golden dataset of questions, expected sources, keywords, and fallback expectations. |
| `metrics.py` | Deterministic metric helpers for source hit, keyword coverage, citations, fallback accuracy, and summaries. |
| `reporting.py` | Markdown and JSON report generation helpers. |
| `run_eval.py` | Offline evaluation runner that writes reports to `eval/results/`. |
| `supportmind_offline_eval.py` | Legacy lightweight keyword sanity check kept for reference. |

## Dataset Schema

Each item in `supportmind_eval_dataset.json` uses this shape:

```json
{
  "id": "api_auth_001",
  "query": "How do I rotate an API key?",
  "category": "api_auth",
  "expected_sources": ["api_authentication_guide.md"],
  "expected_keywords": ["rotate", "API key", "Settings", "Developer"],
  "should_fallback": false
}
```

Out-of-scope examples set `expected_sources` and `expected_keywords` to empty
lists and use `should_fallback: true`.

## Metrics

| Metric | Meaning |
|---|---|
| `source_hit_rate` | Whether expected source files appeared in returned sources. |
| `keyword_coverage` | Whether answer/source text contains expected support keywords. |
| `citation_rate` | Whether answers include a citation marker or returned source metadata. |
| `fallback_accuracy` | Whether out-of-scope cases fallback and in-scope cases do not. |
| `avg_latency_ms` | Average deterministic evaluation runtime per case. |
| `hallucination_flag_rate` | Placeholder-compatible metric for future live/API eval traces. |
| `correction_rate` | Placeholder-compatible metric for future self-correction traces. |

## Running Evaluation

From the repository root:

```bash
python eval/run_eval.py --output-dir eval/results --top-k 5
```

The runner writes:

- `eval/results/latest_report.md`
- `eval/results/latest_report.json`

Optional threshold checks:

```bash
python eval/run_eval.py \
  --output-dir eval/results \
  --top-k 5 \
  --fail-under-source-hit 0.80 \
  --fail-under-keyword-coverage 0.70
```

If a threshold is not met, the command exits non-zero.

## Testing Metric Logic

```bash
python -m pytest --confcutdir=tests/eval tests/eval/test_eval_metrics.py -q
```

## Continuous Evaluation Strategy

### 1. Offline Evaluation in CI

The default CI runs deterministic metric tests and a smoke evaluation. This gives
fast regression coverage without infrastructure or secrets.

### 2. Live/API Evaluation Later

For deeper end-to-end validation, add a separate non-blocking workflow that:

1. Starts Postgres, Redis, ChromaDB, MinIO, API, and Celery.
2. Uploads `sample_docs/` through the API.
3. Waits for ingestion to complete.
4. Sends each dataset query through `/api/v1/chat/.../message`.
5. Scores returned sources, citations, fallback behavior, latency, and trace data.

Keep that workflow separate from the default CI because it depends on service
startup, API keys, and LLM latency.

### 3. Dataset Expansion

When a real query fails or produces weak citations, add it to the dataset with:

- the expected source document
- key phrases that should appear
- whether it should fallback
- the category impacted