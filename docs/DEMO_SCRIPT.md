# Demo Script

This script is designed for a 5-minute portfolio/interview walkthrough of
MindLayer.

## Prerequisites

- Docker services are running.
- Database migrations have been applied.
- API is running at `http://localhost:8000`.
- A demo user exists, or registration/login is available.
- Sample documents are available in [sample_docs](file:///d:/DL/rag-backend/rag-backend/sample_docs).

Useful setup commands:

```powershell
docker compose up -d
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Start the Celery worker in a second terminal. On Windows, use `--pool=solo`:

```powershell
.\.venv\Scripts\celery.exe -A app.tasks.celery_app worker -Q default,ingestion,email --pool=solo -l INFO
```

Run the end-to-end demo smoke workflow:

```powershell
.\.venv\Scripts\python.exe scripts/demo_smoke.py
```

The smoke script seeds a verified/onboarded local demo user, logs in through the
API, creates a conversation, uploads sample docs, waits for ingestion, asks the
standard demo questions via SSE, and verifies answer tokens, sources, and trace
events.

## 1. Open With the Problem

Talking point:

> Support teams often answer the same API, billing, webhook, and incident
> questions from scattered docs. MindLayer turns those docs into cited,
> traceable answers and exposes enough diagnostics to operate the system.

## 2. Show Health and Readiness

```powershell
curl.exe -fsS http://localhost:8000/health
curl.exe -fsS http://localhost:8000/ready
```

Talking point:

> `/health` checks API liveness. `/ready` checks service dependencies like
> Postgres, Redis, MinIO, and ChromaDB.

## 3. Register or Login

Register:

```powershell
curl.exe -sS -X POST http://localhost:8000/api/v1/auth/register `
  -H "Content-Type: application/json" `
  -d '{"email":"demo@example.com","password":"DemoPassword123!"}'
```

Login after verification/onboarding:

```powershell
curl.exe -sS -X POST http://localhost:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email":"demo@example.com","password":"DemoPassword123!"}'
```

Save the access token:

```powershell
$env:ACCESS_TOKEN="paste-access-token-here"
```

Talking point:

> Auth includes email verification, onboarding, refresh tokens, logout, OAuth,
> soft-delete handling, and admin authorization.

## 4. Create a Conversation

```powershell
curl.exe -sS -X POST http://localhost:8000/api/v1/chat/conversations `
  -H "Authorization: Bearer $env:ACCESS_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"title":"MindLayer demo"}'
```

Save the id:

```powershell
$env:CONVERSATION_ID="paste-conversation-id-here"
```

## 5. Upload a Sample Document

```powershell
curl.exe -sS -X POST "http://localhost:8000/api/v1/chat/conversations/$env:CONVERSATION_ID/documents" `
  -H "Authorization: Bearer $env:ACCESS_TOKEN" `
  -F "file=@sample_docs/api_authentication_guide.md"
```

Save the document id:

```powershell
$env:DOCUMENT_ID="paste-document-id-here"
```

Poll ingestion status:

```powershell
curl.exe -sS "http://localhost:8000/api/v1/chat/conversations/$env:CONVERSATION_ID/documents/$env:DOCUMENT_ID" `
  -H "Authorization: Bearer $env:ACCESS_TOKEN"
```

Talking point:

> Upload stores the original file in MinIO, queues Celery ingestion, extracts
> text, chunks content, stores metadata in Postgres, caches parents in Redis,
> and embeds child chunks into ChromaDB.

## 6. Ask a Question With SSE Streaming

```powershell
curl.exe -N -X POST "http://localhost:8000/api/v1/chat/conversations/$env:CONVERSATION_ID/message" `
  -H "Authorization: Bearer $env:ACCESS_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"query":"How do I rotate an API key?"}'
```

Expected event types:

```text
status → token → sources → trace → done
```

Talking point:

> The backend streams token events while LangGraph runs retrieval, reranking,
> answer generation, validation, persistence, and trace collection.

## 7. Show Sources and Agent Trace

In the SSE response, point out:

- `sources`: filename, snippet, rerank score
- `trace`: routing, retrieval, correction, and generation metadata
- `retry_count`: bounded self-correction attempts

Talking point:

> The project is designed for debuggability. If the answer is poor, the trace
> shows which retrieval/reranking/validation steps were involved.

## 8. Show Admin Diagnostics

Requires an admin token:

```powershell
$env:ADMIN_ACCESS_TOKEN="paste-admin-token-here"

curl.exe -sS -H "Authorization: Bearer $env:ADMIN_ACCESS_TOKEN" `
  http://localhost:8000/api/v1/admin/diagnostics
```

What to highlight:

- Postgres/Redis/MinIO/ChromaDB/Celery checks
- secret-safe runtime config summary
- document ingestion counts
- recent failures
- stuck processing documents

Talking point:

> `/ready` is a lightweight readiness gate. Admin diagnostics is a deeper
> operator view and intentionally excludes secrets.

## 9. Run Offline Evaluation

```powershell
.\.venv\Scripts\python.exe eval/run_eval.py --mode offline --output-dir eval/results --top-k 5
```

Talking point:

> The project includes deterministic evals so retrieval quality can be checked
> in CI without depending on live providers.

## 10. Close With Production Readiness

Show docs:

- [README.md](file:///d:/DL/rag-backend/rag-backend/README.md)
- [ARCHITECTURE_OVERVIEW.md](file:///d:/DL/rag-backend/rag-backend/docs/ARCHITECTURE_OVERVIEW.md)
- [DEPLOYMENT_GUIDE.md](file:///d:/DL/rag-backend/rag-backend/docs/DEPLOYMENT_GUIDE.md)
- [OPERATIONS_RUNBOOK.md](file:///d:/DL/rag-backend/rag-backend/docs/OPERATIONS_RUNBOOK.md)
- [SECURITY_CHECKLIST.md](file:///d:/DL/rag-backend/rag-backend/docs/SECURITY_CHECKLIST.md)

Talking point:

> The goal was to demonstrate an end-to-end RAG backend: not just prompting, but
> ingestion, retrieval engineering, streaming, evals, CI, deployment guardrails,
> and operational diagnostics.

## Backup Questions to Ask During Demo

- “Which plan supports SSO?”
- “Why am I getting a 401 error?”
- “What are the webhook retry rules?”
- “How do I troubleshoot failed Stripe integration?”
- “What should I check when Redis latency spikes?”
