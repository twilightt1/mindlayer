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

- Parent-child chunking: child chunks are embedded for precision; parent chunks
  are expanded as LLM context for readability.
- Hybrid retrieval: ChromaDB vector search + BM25 lexical search.
- Reciprocal Rank Fusion to merge retrieval strategies.
- Jina reranker to select the highest-quality snippets.
- LangGraph workflow with routing, memory, retrieval, relevance grading, answer
  generation, hallucination checks, and bounded correction loops.
- `agent_trace` metadata for retrieval/reranking/answer observability.

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
→ SSE cited answer + sources + agent trace
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
