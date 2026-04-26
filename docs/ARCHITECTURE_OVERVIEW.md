# Architecture Overview

This document summarizes the production-style backend architecture for
SupportMind. For detailed LangGraph node behavior, see
[architecture.md](file:///d:/DL/rag-backend/rag-backend/docs/architecture.md).

## System Context

```mermaid
graph TD
    User[Support Agent / Frontend] --> API[FastAPI API]
    API --> Auth[Auth and User Lifecycle]
    API --> Chat[Conversations, Documents, SSE Chat]
    API --> Admin[Admin and Diagnostics]

    Auth --> Postgres[(PostgreSQL)]
    Auth --> Redis[(Redis)]
    Chat --> Postgres
    Chat --> Redis
    Chat --> MinIO[(MinIO)]
    Chat --> Celery[Celery Worker]
    Admin --> Postgres
    Admin --> Redis

    Celery --> Ingestion[Document Ingestion Pipeline]
    Ingestion --> MinIO
    Ingestion --> Postgres
    Ingestion --> Redis
    Ingestion --> Chroma[(ChromaDB)]

    Chat --> RAG[LangGraph RAG Workflow]
    RAG --> Chroma
    RAG --> BM25[BM25 Lexical Index]
    RAG --> Jina[Jina Reranker]
    RAG --> LLM[OpenRouter / LLM Provider]
    RAG --> SSE[SSE Response Stream]
```

## Core Components

| Component | Role |
| :--- | :--- |
| **FastAPI** | HTTP API for auth, users, chat, documents, admin, health, and readiness. |
| **PostgreSQL** | Durable relational data: users, conversations, documents, chunks, messages, quotas, settings, audit logs. |
| **Redis** | Rate limiting, refresh token/session state, parent chunk cache, Celery broker/backend. |
| **Celery** | Background document ingestion and scheduled quota reset tasks. |
| **MinIO** | Object storage for uploaded source documents. |
| **ChromaDB** | Vector database for child chunk embeddings. |
| **BM25** | Lexical retrieval over parent chunks. |
| **Jina Reranker** | Cross-encoder reranking for final context precision. |
| **LangGraph** | Agent workflow orchestration and corrective RAG routing. |
| **OpenRouter / LLM** | Answer generation and agent reasoning. |

## Request Flows

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Auth API
    participant DB as PostgreSQL
    participant Redis
    participant Email as Email Provider

    Client->>API: POST /api/v1/auth/register
    API->>DB: Create user + verification session
    API->>Email: Queue/send verification code
    Client->>API: POST /api/v1/auth/verify-email/otp
    API->>DB: Mark user verified
    API-->>Client: Onboarding-scoped access token
    Client->>API: POST /api/v1/auth/onboarding
    API->>DB: Save profile state
    API->>Redis: Store refresh token/session state
    API-->>Client: Access + refresh tokens
```

### Document Ingestion Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Chat API
    participant MinIO
    participant DB as PostgreSQL
    participant Celery
    participant Redis
    participant Chroma

    Client->>API: POST /chat/conversations/{id}/documents
    API->>MinIO: Store original file
    API->>DB: Create document status=pending
    API->>Celery: Queue process_document
    API-->>Client: 202 accepted + document id
    Celery->>MinIO: Read uploaded file
    Celery->>Celery: Extract text and chunk
    Celery->>DB: Store parent/child chunks
    Celery->>Redis: Cache parent chunks
    Celery->>Chroma: Store child embeddings
    Celery->>DB: Mark document ready or failed
```

### Chat/RAG Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Chat API
    participant Graph as LangGraph
    participant DB as PostgreSQL
    participant Redis
    participant Chroma
    participant Jina
    participant LLM

    Client->>API: POST /chat/conversations/{id}/message
    API-->>Client: SSE status=start
    API->>Graph: Start AgentState
    Graph->>DB: Load conversation memory
    Graph->>Chroma: Vector retrieval
    Graph->>Redis: Parent cache lookup
    Graph->>Graph: BM25 + RRF + parent expansion
    Graph->>Jina: Rerank candidate context
    Graph->>LLM: Generate grounded answer
    LLM-->>API: Token deltas
    API-->>Client: SSE token events
    Graph->>LLM: Grounding/answer checks
    Graph->>DB: Save messages + agent trace
    API-->>Client: SSE sources + trace + done
```

### Operations Flow

```mermaid
sequenceDiagram
    participant Operator
    participant API as FastAPI API
    participant Diag as Diagnostics Service
    participant Infra as Dependencies
    participant DB as PostgreSQL

    Operator->>API: GET /health
    API-->>Operator: API liveness
    Operator->>API: GET /ready
    API->>Infra: Postgres/Redis/MinIO/Chroma checks
    API-->>Operator: ok or degraded
    Operator->>API: GET /api/v1/admin/diagnostics
    API->>Diag: Build secret-safe diagnostics
    Diag->>Infra: Dependency + Celery checks
    Diag->>DB: Ingestion counts/failures/stuck docs
    API-->>Operator: Checks + config summary + ingestion status
```

## Data Boundaries

- Conversations and documents are scoped by authenticated user.
- Parent chunk fallback retrieval is scoped by conversation to avoid cross-user
  context leakage.
- Admin APIs require `require_admin`.
- Diagnostics excludes secrets such as JWT keys, provider API keys, database
  URLs, Redis URLs, MinIO secrets, access tokens, and refresh tokens.

## Reliability and Deployment Boundaries

- Local development uses [docker-compose.yml](file:///d:/DL/rag-backend/rag-backend/docker-compose.yml).
- Production-like validation overlays [docker-compose.prod.yml](file:///d:/DL/rag-backend/rag-backend/docker-compose.prod.yml).
- Production mode rejects unsafe placeholder config at startup.
- `/ready` is a dependency readiness gate.
- `/api/v1/admin/diagnostics` is an authenticated operator view.
- Offline eval is deterministic and CI-safe; live API eval is opt-in.
