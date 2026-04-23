# SupportMind Portfolio Summary

## One-liner

**SupportMind** is a production-oriented RAG backend for SaaS support teams,
enabling cited answers over product docs, API references, billing FAQs,
troubleshooting guides, integration docs, release notes, and incident runbooks.

## Problem

Support teams waste time searching scattered documentation and often answer
repeated product/API questions manually. SupportMind centralizes support
knowledge and returns grounded answers with source context.

## Technical Highlights

- Built a FastAPI backend with JWT auth, Google OAuth, onboarding, refresh token
  rotation, and admin authorization.
- Implemented asynchronous document ingestion with Celery workers, Redis, MinIO,
  PostgreSQL, and ChromaDB.
- Designed a parent-child chunking strategy where child chunks are embedded and
  parent chunks are used as LLM context.
- Combined vector search and BM25 lexical search with Reciprocal Rank Fusion.
- Added Jina reranking for higher precision context selection.
- Orchestrated the RAG flow with LangGraph: routing, memory, retrieval, answer,
  grounding check, and message persistence.
- Stored `agent_trace` metadata to debug routing, retrieval, reranking, and
  answer-generation behavior.
- Hardened security by replacing wildcard CORS, avoiding refresh tokens in query
  params, using one-time OAuth redirect exchange codes, blocking soft-deleted
  users, and scoping parent retrieval by conversation.

## Architecture Summary

```text
FastAPI API
→ JWT/OAuth auth
→ PostgreSQL user/conversation/document/message models
→ MinIO document storage
→ Celery ingestion workers
→ parent-child chunking
→ ChromaDB vector index + BM25 lexical index
→ LangGraph RAG workflow
→ cited SSE answer + source snippets + agent trace
```

## Demo Scenario

A SaaS support agent uploads mock knowledge-base documents:

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

SupportMind retrieves the relevant source document and generates a grounded answer
with source snippets.

## Skills Demonstrated

- Backend API design
- Authentication and authorization
- Async/background processing
- Retrieval engineering
- Vector databases
- RAG quality evaluation
- Agent workflow orchestration
- Dockerized infrastructure
- Security and reliability hardening
- Technical documentation for production-style systems

## Future Improvements

- True token-level SSE streaming.
- Atomic quota updates with Redis Lua or database row locks.
- CI pipeline with PostgreSQL, Redis, and ChromaDB services.
- Frontend dashboard for support-agent demo.
- RAG evaluation against live API responses.
