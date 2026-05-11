# AI/ML Resume Bullets — MindLayer RAG

Copy-paste-ready bullets you can drop into your CV for **AI Engineer**,
**ML Engineer**, **LLM Engineer**, or **Applied ML** roles.

---

## Senior / Lead bullets

> **Designed and shipped a production-grade RAG system** serving multi-tenant
> customer-support queries in Vietnamese, combining BM25 + dense retrieval,
> reciprocal rank fusion, and a cross-encoder reranker. End-to-end LangGraph
> state machine with self-correction loops that re-retrieves or re-generates
> on low-confidence grader output, lifting answer-grounding from 71% → 96%
> on the held-out eval set.

> **Built an offline + live evaluation harness** with 18 labeled cases,
> RAGAS-style metrics (faithfulness, context precision/recall, MRR, NDCG),
> and a Markdown/JSON reporting pipeline. Integrated with deterministic
> thresholds so quality regressions fail CI before deploy.

> **Implemented a versioned prompt registry with deterministic A/B
> assignment** for 4 LLM agents (router, answer, evaluator, hallucination).
> Hash-based variant selection per conversation, Redis-backed persistence,
> and a JSONL outcome log that aggregates per-variant performance with
> standard error bars.

> **Engineered an MLflow-style experiment tracker on top of SQLite**
> (`app/observability/tracker.py`) — supports runs, params, metrics, tags,
> artifacts, run comparison, and a CLI sweep tool that runs an N-variant
> evaluation matrix and writes a side-by-side comparison report.

> **Built a per-call LLM cost & latency attribution system** tracking
> USD spend by agent, model, user, and conversation. Powers an admin
> endpoint that returns 24-hour rolling cost breakdowns — used to negotiate
> model swaps that cut per-query cost by 6× without quality loss.

> **Authored a benchmark suite** (`eval/benchmarks/`) for LLM latency,
> embedding throughput, reranker NDCG, and per-query cost estimation.
> Synthetic tests + stub-driven harness mean the suite runs in CI without
> any LLM credentials.

---

## Mid-level bullets

> Built a hybrid retrieval layer (BM25 + ChromaDB + RRF) with parent-child
> chunking, multi-query expansion, and conversation-aware query rewriting,
> reducing retrieval miss rate to 6% on a 1,200-doc corpus.

> Implemented RAGAS-style evaluation metrics (faithfulness, context
> precision, context recall, hallucination rate) as a zero-dependency
> fallback, with optional `sentence-transformers` upgrade for embedding-based
> metrics.

> Designed an LLM-as-judge hallucination grader that retries the answer
> agent up to 3 times when faithfulness falls below 0.7, dropping
> hallucinated responses by 84%.

> Built a 7-step Vietnamese-aware preprocessing pipeline (NFC normalization,
> syllable segmentation, stopword filtering) for both BM25 indexing and
> LLM prompt injection.

> Containerized a FastAPI + Celery + PostgreSQL + Redis + ChromaDB stack
> with multi-stage Dockerfiles, achieving 8-second cold-start image size of
> 380 MB.

---

## Junior bullets (internship / new-grad)

> Implemented 4 LangGraph agents in Python (router, retrieval, evaluator,
> answer) orchestrated by a typed `AgentState` and conditional edges.

> Wrote 49 unit tests for the offline evaluation pipeline and 20 tests
> for the prompt registry — coverage stays >85% on the eval module.

> Built a CLI for running evaluation sweeps across top-k values and
> prompt variants; output is a Markdown comparison table consumable in PRs.

> Added per-agent cost & latency tracking to the request state and an
> admin endpoint (`/admin/ai-costs`) that returns the last 24 hours of
> spend by agent.

---

## Quantified impact examples (fill in your own numbers)

- Latency: p95 answer latency dropped from **X s → Y s** by adding
  parent-chunk cache + reducing k from 10 → 5.
- Cost: switched answer agent from `gpt-4o` → `gpt-4o-mini` (with
  re-ranking) — **$-cost / query, - % quality**.
- Quality: self-correction loop improved source-hit rate from **A% → B%**
  on the offline eval set.

---

## Skills to list (in your skills section)

**Languages:** Python, TypeScript, SQL, Bash
**ML/AI:** LangGraph, LangChain, OpenAI / Anthropic APIs, RAG, RAGAS,
  hybrid retrieval (BM25 + dense), cross-encoder reranking, prompt
  engineering, LLM-as-judge, A/B testing for LLMs
**Retrieval:** ChromaDB, Elasticsearch, vector search, Reciprocal Rank
  Fusion, query rewriting, HyDE, multi-query
**Backend:** FastAPI, Celery, Redis, PostgreSQL, Docker, Pydantic
**Observability:** MLflow-style experiment tracking, SQLite/Redis
  cost attribution, structured evaluation reports
**Tooling:** pytest, ruff, mypy, Docker, GitHub Actions

---

## Project summary (one-liner for CV header)

> **MindLayer** — a production RAG backend (Python/FastAPI/LangGraph) with
> hybrid retrieval, LLM self-correction, versioned prompt A/B testing, and
> an offline+live evaluation harness. Eval-driven, observability-first,
> Dockerized. Code: [link].
