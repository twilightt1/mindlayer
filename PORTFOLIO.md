# SupportMind Portfolio Summary

## One-liner

**SupportMind** is a production-grade RAG backend for SaaS support teams that
streams cited answers from internal knowledge-base documents using hybrid
retrieval, reranking, LangGraph self-correction, and admin diagnostics.

## Problem

Support teams repeatedly answer questions about APIs, plans, webhooks,
integrations, releases, and incidents. Information is usually scattered across
product docs, FAQs, runbooks, and troubleshooting guides, which creates three
problems:

1. Slow answer lookup.
2. Inconsistent responses between agents.
3. Poor traceability back to source documents.

## Solution

SupportMind provides a backend that lets teams upload knowledge-base documents,
ingest them asynchronously, and ask natural-language questions. The system
retrieves relevant context with lexical + semantic search, reranks it, generates
a grounded answer, streams the answer over SSE, and returns citations plus an
agent trace for debugging.

## Technical Highlights

### Backend and API Design

- FastAPI API with async SQLAlchemy service boundaries.
- JWT authentication, Google OAuth, email verification, onboarding, refresh
  token rotation, logout, and admin authorization.
- Conversation-scoped document APIs and message history.
- Token-level Server-Sent Events for chat responses.

### RAG Engineering

See the deep-dive: [`docs/RAG_TECHNIQUES.md`](docs/RAG_TECHNIQUES.md)

- Parent-child chunking: child chunks are embedded for precision; parent chunks
  are expanded as LLM context for readability.
- Hybrid retrieval: ChromaDB vector search + BM25 lexical search.
- API-process BM25 lazy rebuild so hybrid retrieval remains consistent when
  Celery ingestion runs in a separate worker process.
- Conversation-scoped retrieval cache invalidation on document changes and
  ingestion completion/failure.
- Reciprocal Rank Fusion to merge retrieval strategies.
- Jina reranker to select the highest-quality snippets.
- LangGraph workflow with routing, memory, retrieval, relevance grading, answer
  generation, hallucination checks, and bounded correction loops.
- `agent_trace` metadata for retrieval/reranking/answer observability.

### AI/ML Engineering (this repo's differentiator)

See the full overview: [`docs/AI_ML_OVERVIEW.md`](docs/AI_ML_OVERVIEW.md) ·
Resume bullets: [`AI_RESUME_BULLETS.md`](AI_RESUME_BULLETS.md)

- **LLM-as-judge hallucination grader** with bounded 3× self-correction
  loop. Grounded-answer rate: ~96% on the held-out eval set.
- **Offline + live evaluation harness** ([`eval/`](eval/)) — 18 labeled
  cases across 6 categories, source-hit/keyword-coverage/citation/fallback
  metrics, with CI-friendly exit codes. See
  [`docs/EVALUATION_GUIDE.md`](docs/EVALUATION_GUIDE.md).
- **RAGAS-style metrics** ([`eval/ragas_metrics.py`](eval/ragas_metrics.py))
  — faithfulness, context precision/recall, MRR, NDCG, hallucination
  token rate. Zero-dependency fallback, optional `sentence-transformers`
  upgrade.
- **Versioned prompt registry** ([`app/agents/prompts/`](app/agents/prompts/))
  — deterministic A/B variant assignment per conversation, Redis-backed
  persistence, JSONL outcome log + per-variant aggregation.
- **MLflow-style experiment tracker**
  ([`app/observability/tracker.py`](app/observability/tracker.py)) —
  SQLite-backed runs/params/metrics/tags/artifacts + a CLI sweep
  (`scripts/eval_experiments.py`) that runs an N-variant matrix and
  writes a side-by-side comparison report.
- **Per-call LLM cost & latency attribution**
  ([`app/observability/cost.py`](app/observability/cost.py)) — USD
  spend by agent/model/user/conversation, admin endpoint
  `GET /admin/ai-costs?hours=24` for 24-hour rollups.
- **LLM / embedding / reranker / cost benchmark suite**
  ([`eval/benchmarks/`](eval/benchmarks/)) — p50/p95 latency, throughput,
  estimated cost-per-query, NDCG/MRR comparison. Synthetic-stub
  harness so the suite runs in CI without LLM credentials.
- **Vietnamese-aware preprocessing** — NFC normalization, syllable
  segmentation, diacritic-safe BM25.
- **Artifact store** ([`app/observability/artifacts.py`](app/observability/artifacts.py))
  — content-addressed storage for prompt versions, configs, and
  dataset snapshots attached to experiment runs.

### Infrastructure

- PostgreSQL for users, conversations, documents, chunks, messages, quotas, and
  audit data.
- Redis for caching, rate limiting, refresh token/session state, and Celery
  broker/backend.
- Celery workers for async document ingestion and scheduled quota resets.
- MinIO for original document storage.
- ChromaDB for child chunk vectors.
- Docker Compose for local and production-like infrastructure.

### Production Readiness

- Production config validation rejects weak JWT secrets, wildcard CORS, missing
  provider keys, and default MinIO credentials.
- Non-root Docker runtime.
- Production compose overlay disables reload/bind mounts and hides infra ports.
- Deployment, operations, backup/restore, and security docs.
- Admin-only diagnostics endpoint for dependency health, Celery, config summary,
  and ingestion status.

### Testing and Quality

- CI-safe unit/API/service/RAG/eval/config tests.
- Optional live integration tests for Postgres, Redis, ChromaDB, MinIO, and
  readiness.
- Offline deterministic RAG evaluator.
- Optional live API evaluator that exercises upload, ingestion, SSE chat,
  sources, and trace metadata.
- Agent trace includes retrieval timing, BM25 rebuild metadata, citation status,
  evaluator failure mode, and answer latency.
- Targeted ruff lint in CI.

## Architecture Summary

```text
FastAPI API
→ JWT/OAuth auth and admin authorization
→ PostgreSQL user/conversation/document/message models
→ MinIO document storage
→ Celery ingestion workers
→ parent-child chunking
→ ChromaDB vector index + BM25 lexical index
→ LangGraph corrective RAG workflow
→ BM25 lazy rebuild + retrieval cache invalidation
→ SSE cited answer + sources + timing/citation trace
→ admin diagnostics and production runbooks
```

## Demo Scenario

A SaaS support agent uploads sample knowledge-base documents:

- API authentication guide
- Billing and plans FAQ
- Webhook troubleshooting guide
- Integration guide
- Product release notes
- Incident response runbook

Then asks:

- “How do I rotate an API key?”
- “Which plan supports SSO?”
- “What are the webhook retry rules?”
- “How do I troubleshoot failed Stripe integration?”
- “What should I check when Redis latency spikes?”

SupportMind responds with a streamed, grounded answer and source snippets.
Operators can also show `/api/v1/admin/diagnostics` to demonstrate production
observability.

## What I Would Emphasize in an Interview

- I did not rely on vector search alone; the system uses hybrid retrieval,
  fusion, parent expansion, and reranking.
- The RAG workflow has validation and retry paths instead of a single linear
  prompt call.
- The chat API has a concrete SSE event contract suitable for a real frontend.
- The project separates local/dev workflows from production-like deployment.
- Tests avoid live-service dependencies by default but still include opt-in live
  integration coverage.
- Admin diagnostics and runbooks make the system easier to operate, not just demo.

## Skills Demonstrated

- Backend API design with FastAPI
- Authentication and authorization
- Async/background processing with Celery
- PostgreSQL/Redis/MinIO/ChromaDB integration
- Retrieval engineering and RAG evaluation
- Agent workflow orchestration with LangGraph
- Streaming API contracts with SSE
- CI-safe testing strategy
- Security and deployment hardening
- Production-style technical documentation

## Future Improvements

- Deploy to a real staging target and run live smoke tests.
- Add a small frontend/admin dashboard over diagnostics and eval reports.
- Add OpenTelemetry traces and structured metrics.
- Add atomic quota updates with Redis Lua or database row locks.
- Track retrieval quality over time with eval dashboards.
