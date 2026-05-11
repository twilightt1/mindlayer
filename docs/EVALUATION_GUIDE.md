# Evaluation Guide

How MindLayer measures RAG quality, runs the eval pipeline, and interprets
results.

## TL;DR

```bash
# 1. Offline eval (no LLM, deterministic)
.venv/Scripts/python -m eval.run_eval --mode offline --output-dir eval/results

# 2. Offline eval + RAGAS metrics
.venv/Scripts/python -m eval.run_eval --mode offline --enable-ragas

# 3. Live API eval (requires running server + API key)
.venv/Scripts/python -m eval.run_eval --mode live --api-url http://localhost:8000

# 4. Sweep an experiment
.venv/Scripts/python scripts/eval_experiments.py --experiment topk_sweep \
    --variants topk_3,topk_5,topk_8

# 5. LLM cost benchmark (no API needed)
.venv/Scripts/python eval/benchmarks/run_benchmark.py --mode cost
```

## What gets measured

### Core metrics (always computed)

| Metric | What it measures | Target |
|--------|------------------|--------|
| `source_hit_rate` | % of cases where expected source appears in top-K | ≥ 90% |
| `keyword_coverage` | % of expected keywords found in answer | ≥ 80% |
| `citation_rate` | % of answers containing `[Source N]` markers | ≥ 75% |
| `fallback_accuracy` | % of out-of-scope queries routed correctly | 100% |

### Self-correction metrics

| Metric | What it measures |
|--------|------------------|
| `hallucination_flag_rate` | How often the LLM-as-judge flagged an answer |
| `correction_rate` | Of the flagged ones, how many retries fixed it |

### RAGAS-style metrics (with `--enable-ragas`)

| Metric | What it measures |
|--------|------------------|
| `answer_relevancy` | Token-level overlap between answer and question |
| `context_precision@k` | Fraction of top-k chunks that are relevant |
| `context_recall@k` | Fraction of relevant chunks that are in top-k |
| `faithfulness_simple` | % of answer claims supported by context |
| `hallucination_token_rate` | % of answer tokens not grounded in context |
| `mrr` | Mean reciprocal rank of the first relevant source |
| `ndcg@k` | Normalized discounted cumulative gain at k |

## The eval dataset

`eval/MindLayer_eval_dataset.json` — 18 cases across 6 categories:

| Category | Cases | What it tests |
|----------|-------|---------------|
| api_auth | 3 | API authentication questions |
| billing | 3 | Billing and plan questions |
| webhooks | 3 | Webhook setup / troubleshooting |
| integrations | 2 | Third-party integrations |
| releases | 2 | Product release notes |
| incidents | 2 | Incident response runbook |
| out_of_scope | 3 | "I don't know" path |

Each case has:
- `id` — stable identifier
- `category`
- `query` — the user question
- `expected_sources` — document names that should appear in retrieval
- `expected_keywords` — terms that should appear in the answer
- `should_cite` — whether the answer must contain citations
- `is_in_scope` — whether the case expects a RAG answer

## Reading the report

`eval/results/latest_report.md` contains:

1. **Summary table** — overall metrics
2. **Per-case results** — each case's status + sources
3. **RAGAS section** — when `--enable-ragas` is set
4. **Failed cases** — anything that crossed a threshold
5. **Recommendations** — auto-generated next steps

## Adding new eval cases

```json
{
  "id": "my_new_case_001",
  "category": "api_auth",
  "query": "How do I rotate my API key without downtime?",
  "expected_sources": ["api_authentication_guide.md"],
  "expected_keywords": ["rotation", "overlap", "revoke"],
  "should_cite": true,
  "is_in_scope": true
}
```

Add to `eval/MindLayer_eval_dataset.json`, then re-run.

## Custom thresholds

```bash
.venv/Scripts/python -m eval.run_eval --mode offline \
    --fail-under-source-hit 0.9 \
    --fail-under-keyword-coverage 0.8
```

The eval will exit non-zero if any threshold is missed — useful in CI.

## CI integration

```yaml
- name: Run RAG eval
  run: |
    .venv/Scripts/python -m eval.run_eval --mode offline \
      --output-dir eval/results --fail-under-source-hit 0.9
```

The exit code propagates; pull request is blocked on regression.

## Prompt A/B testing

```bash
# 1. Register a new variant (edit app/agents/prompts/versions.py)
# 2. Run a sweep
.venv/Scripts/python scripts/eval_experiments.py \
    --experiment router_compare \
    --variants router_v1,router_v2
```

Output: `eval/experiments/router_compare_comparison.md` with
side-by-side metrics.

## Cost & latency analysis

```bash
# After running the eval
.venv/Scripts/python -c "from app.observability.cost import CostTracker; \
    t = CostTracker(); print(t.breakdown_by_agent())"
```

Or query the admin endpoint:
```
GET /admin/ai-costs?hours=24
```

## Benchmarking different models

```bash
# Compare cost across all known models
.venv/Scripts/python eval/benchmarks/run_benchmark.py --mode cost

# Real LLM benchmark (requires API key)
.venv/Scripts/python eval/benchmarks/run_benchmark.py --mode llm \
    --models openai/gpt-4o-mini,openai/gpt-4o --n-runs 5
```
