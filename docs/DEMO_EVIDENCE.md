# Demo Evidence — Phase 15 Live Certification

This document captures the live local certification run for the SupportMind demo
workflow.

## Environment

- Date/time: 2026-06-11 15:37 +07
- OS: Windows
- API base URL: `http://127.0.0.1:8000`
- Runtime mode used for certification:
  - Docker infrastructure services
  - Local virtualenv FastAPI process
  - Local virtualenv Celery worker with `--pool=solo`

## Startup Commands

Infrastructure:

```powershell
docker compose up -d postgres redis chromadb minio
docker compose ps
```

Migrations:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m alembic upgrade head
```

API:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Celery worker:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\celery.exe -A app.tasks.celery_app worker -Q default,ingestion,email --pool=solo -l INFO
```

Demo smoke:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe scripts/demo_smoke.py
```

## Infrastructure Health

`docker compose ps` showed all infrastructure services healthy:

| Service | Host Port | Status |
| --- | ---: | --- |
| Postgres | `55432` | healthy |
| Redis | `6379` | healthy |
| ChromaDB | `8001` | healthy |
| MinIO | `9000/9001` | healthy |

`/ready` returned healthy dependency checks:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "checks": {
    "postgres": {"status": "ok", "latency_ms": 230.16},
    "redis": {"status": "ok", "latency_ms": 188.56},
    "minio": {"status": "ok", "latency_ms": 181.35},
    "chroma": {"status": "ok", "latency_ms": 215.19}
  }
}
```

## Live Smoke Result

The reusable smoke script completed successfully.

### Identity and Conversation

| Step | Result |
| --- | --- |
| Ensure demo user | `supportmind-demo@example.com` verified and onboarded |
| Login | access token received |
| Conversation | `b456faf1-cb01-4341-a820-7b02bc390d89` |

### Uploaded Documents

| File | Document ID | Result |
| --- | --- | --- |
| `api_authentication_guide.md` | `2bd25545-dac2-4391-8377-230290407493` | ready |
| `billing_and_plans_faq.md` | `6fdd77f8-d832-4807-8194-b1e65eff41c3` | ready |
| `webhook_troubleshooting.md` | `2ef1fe79-9f1a-44a5-a2ed-ee23ed458933` | ready |

Celery evidence:

```text
HTTP Request: POST https://openrouter.ai/api/v1/embeddings "HTTP/1.1 200 OK"
HTTP Request: POST http://localhost:8001/.../upsert "HTTP/1.1 200 OK"
BM25 built
Ingestion complete
```

### SSE RAG Questions

| Question | Sources | Event Sequence | Answer Preview |
| --- | ---: | --- | --- |
| `How do I rotate an API key?` | 3 | `status*8 -> token -> sources -> trace -> done` | `To rotate an API key, follow these steps...` |
| `Which plan supports SSO?` | 3 | `status*8 -> token -> sources -> trace -> done` | `The Enterprise plan supports Single Sign-On (SSO)...` |
| `What are the webhook retry rules?` | 2 | `status*8 -> token -> sources -> trace -> done` | `Webhook delivery uses exponential backoff...` |

Each response included these trace keys:

```text
answer
citation
grade_docs
hallucination
parent_expansion
retrieval
router
timing
```

## Notable Runtime Observations

> [!NOTE]
> The first full `docker compose up -d` attempted to build app/worker images and
> failed during `pip install` with a transient `BrokenPipeError` while downloading
> packages. The certification continued with Docker infrastructure services and
> local virtualenv app/worker processes, which is the documented Windows-friendly
> local demo path.

> [!NOTE]
> A stale email task in Redis attempted SendGrid delivery and failed with 401 due
> to local credentials. It did not block ingestion or the RAG smoke workflow.

> [!NOTE]
> The API logged non-blocking evaluator/router warnings during LLM guardrail
> execution. The bounded corrective flow still emitted final `token`, `sources`,
> `trace`, and `done` events for all three demo questions.

## Certification Outcome

Phase 15 certification passed:

- Health passed.
- Readiness passed.
- Demo user setup passed.
- Auth login passed.
- Conversation creation passed.
- Document upload passed.
- Celery ingestion passed.
- OpenRouter embeddings passed.
- Chroma upsert passed.
- BM25 build passed.
- SSE RAG answers passed with sources and trace.
