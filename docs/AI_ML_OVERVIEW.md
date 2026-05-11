# MindLayer — AI/ML Architecture Overview

> A deep-dive for technical interviewers, peer reviews, and AI/ML portfolio
> reviewers. Covers the RAG pipeline, agent graph, evaluation framework, and
> ML observability tooling.

---

## 1. System goals

Build a customer-support assistant that:
- Answers from a private Vietnamese knowledge base (PDFs, markdown, runbooks)
- Refuses to answer out-of-scope questions (no hallucination)
- Cites its sources inline
- Recovers gracefully from bad retrievals and bad generations
- Has measurable, testable quality and cost

## 2. RAG pipeline (high level)

```
User query
   │
   ▼
┌────────────┐
│  Router    │  classify intent → chitchat | summarize | rag
└────┬───────┘
     │  (rag)
     ▼
┌────────────┐
│  Memory    │  rewrite + multi-query + HyDE in parallel
└────┬───────┘
     ▼
┌────────────┐
│ Retrieval  │  BM25 (rank_bm25)  ╲
│            │  ChromaDB (cosine)  ╳  RRF fusion  → top-K
│            │  Parent-child cache ┤
└────┬───────┘
     ▼
┌────────────┐
│ Rerank     │  cross-encoder (FlashRank / ColBERT-style)
└────┬───────┘
     ▼
┌────────────┐
│ Compress   │  per-chunk relevance grader → drop low-relevance
└────┬───────┘
     ▼
┌────────────┐
│  Answer    │  LLM with strict context-only instruction + citation markers
└────┬───────┘
     ▼
┌────────────┐
│ Halluc.    │  LLM-as-judge → retry answer up to 3× on failure
└────┬───────┘
     ▼
   final response + sources
```

## 3. Agent graph (LangGraph)

The full request flow is a typed `StateGraph` (`app/graph.py`):

```python
START → router ─┬─ chitchat (no retrieval)  → END
                └─ rag       → retrieval → grade_docs
                                           │
                              ┌────────────┴────────────┐
                              ▼                         ▼
                        context_relevant=True    context_relevant=False
                              │                         │
                              ▼                         ▼
                            answer              retry_retrieval (max 3)
                              │                         │
                              ▼                         │
                       grade_gen (halluc)               │
                              │                         │
                  ┌───────────┴───────────┐             │
                  ▼                       ▼             │
            is_hallucination=False  is_hallucination=True
                  │                       │
                  ▼                       ▼
                 save             retry_answer (max 3)
                  │                       │
                  └─────────►  END  ◄─────┘
```

- **Self-correction** uses conditional edges that check
  `state["context_relevant"]` and `state["is_hallucination"]`.
- **Bounded retries** (max 3) prevent infinite loops.
- **Typed state** ([`AgentState`](app/agents/state.py)) prevents
  field-name typos at runtime.

## 4. Retrieval design

### Hybrid search
- **BM25** ([`app/retrieval/bm25_retriever.py`](app/retrieval/bm25_retriever.py))
  on tokenized + Vietnamese-syllable-segmented text
- **ChromaDB** vector store ([`app/retrieval/vector_store.py`](app/retrieval/vector_store.py))
  with `text-embedding-3-small` (configurable)
- **Reciprocal Rank Fusion** ([`app/retrieval/rrf.py`](app/retrieval/rrf.py))
  to combine ranked lists: `score(d) = Σ 1 / (k + rank_i(d))`, k=60

### Query transformation
Run in parallel with `asyncio.gather`:
1. **Conversation rewrite** — resolve pronouns using last 3 turns
2. **Multi-query** — 3 search variants (router output)
3. **HyDE** — generate a hypothetical answer, embed that

### Parent-child chunking
- Children (256 tokens) are embedded
- Parents (1024 tokens) are returned for context
- Avoids the "small chunks are good for retrieval, large for reading" trade-off

### Cache layers
- **Redis 7200s TTL** — parent chunks keyed by doc id
- **Redis 300s TTL** — full query results

## 5. Agent design

Four agents, each in its own module, each with a versioned prompt variant:

| Agent         | Purpose                                       | LLM call? |
|---------------|-----------------------------------------------|-----------|
| router        | Classify intent, rewrite, generate variants   | yes       |
| retrieval     | Pull chunks (no LLM)                          | no        |
| evaluator     | Per-chunk relevance grading                   | yes       |
| answer        | Compose final answer with citations           | yes       |
| hallucination | LLM-as-judge faithfulness check               | yes       |

Prompts live in [`app/agents/prompts/versions.py`](app/agents/prompts/versions.py)
and are loaded by the [`PromptRegistry`](app/agents/prompts/registry.py).

## 6. Evaluation framework

### Two modes
- **Offline** ([`eval/run_eval.py`](eval/run_eval.py)) — deterministic, no
  LLM calls. Runs against [`eval/MindLayer_eval_dataset.json`](eval/MindLayer_eval_dataset.json)
  (18 cases across 6 categories).
- **Live** — exercises the FastAPI endpoint, captures real latency.

### Metrics
- **Source hit rate** — % of cases where expected source appears in retrieved
- **Keyword coverage** — % of expected keywords found in answer
- **Citation rate** — % of answers containing `[Source N]` markers
- **Fallback accuracy** — % of out-of-scope queries that hit the chitchat path
- **RAGAS-style** (this repo) — faithfulness, context precision@k,
  context recall@k, hallucination token rate, MRR, NDCG@k, answer relevancy

### Self-correction metrics
- Hallucination flag rate
- Correction rate (how often retry fixed the answer)

## 7. Observability & ML engineering tooling

| Tool | Path | Purpose |
|------|------|---------|
| Run tracker | [`app/observability/tracker.py`](app/observability/tracker.py) | MLflow-style run logger, SQLite |
| Experiment orchestrator | [`app/observability/experiments.py`](app/observability/experiments.py) | N-variant sweeps |
| Artifact store | [`app/observability/artifacts.py`](app/observability/artifacts.py) | Save/load prompt versions + configs |
| Cost tracker | [`app/observability/cost.py`](app/observability/cost.py) | Per-call LLM cost, admin API |
| Prompt registry | [`app/agents/prompts/registry.py`](app/agents/prompts/registry.py) | A/B versioned prompts |
| Prompt integration | [`app/agents/prompts/integration.py`](app/agents/prompts/integration.py) | Agent-side helpers |
| Benchmarks | [`eval/benchmarks/`](eval/benchmarks/) | LLM/embedding/reranker/cost |

## 8. What I would do with more time (Phase 2)

Listed in [`implementation_plan.md`](../implementation_plan.md):
- Synthetic dataset generation (use LLM to bootstrap more eval cases)
- Confidence calibration (Platt scaling on grader probabilities)
- Retrieval drift detection (alert on score distribution shift)
- LoRA / PEFT fine-tuning pipeline for the evaluator

---

## References

- LangGraph state machines — https://langchain-ai.github.io/langgraph/
- RAGAS framework — https://docs.ragas.io/
- Cross-encoder reranking (FlashRank) — https://github.com/PrithivirajDamodaran/FlashRank
- ChromaDB — https://www.trychroma.com/
- Reciprocal Rank Fusion — Cormack et al., 2009
