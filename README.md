# Orivory — AI Second Brain

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=next.js&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Your AI-powered second brain. Open source. Self-hosted. Privacy-first.**

*[Orivory = Open + Memory + Discovery]*

</div>

---

## 🌟 What is Orivory?

Orivory is an open-source, self-hosted AI second brain that transforms scattered information into actionable knowledge. Unlike cloud-based solutions, your data stays on your infrastructure — fully private, customizable, and always under your control.

### Core Philosophy

> **"Store what you know. Ask what you remember. Let insights find you."**

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **🔍 Hybrid Search** | Vector + keyword search with Reciprocal Rank Fusion (RRF) and Jina AI reranking |
| **🤖 Multi-Agent Architecture** | 15+ specialized LangGraph agents with self-correction capabilities |
| **🕸️ Knowledge Graph** | Entity extraction, relation mapping, and automatic cluster detection |
| **🧠 Memory Management** | Time-aware retrieval, context merging, and smart retention gates |
| **💡 Proactive Insights** | AI-powered insight cards that surface patterns you didn't know existed |
| **📡 Real-time Streaming** | SSE token streaming with trace events and intermediate steps |
| **🔗 Multi-Source Ingestion** | Notion, Gmail, Google Drive, web clipper, RSS feeds, file uploads |
| **👥 Team Workspaces** | Shared knowledge bases with workspace-level access control |
| **📊 Analytics** | Usage tracking, DAU metrics, and cost monitoring |
| **🎁 Referral System** | Built-in viral referral system for organic growth |
| **🧩 Open Memory Hub (MVP)** | MCP server so any AI agent can read/write your memory with scoped per-agent tokens and a full access ledger |

### Open Memory Hub (MVP)

Any MCP-capable agent can connect to your second brain. You register an agent client, get a scoped token (`memory:read` / `memory:write`), and point the agent at the MCP endpoint — every call is recorded in the access ledger ("which AI read what, when"). See [docs/API.md — Agent Clients & MCP Hub](docs/API.md#13-agent-clients--mcp-hub).

```bash
# 1. Register an agent client (as your logged-in user)
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Claude Desktop", "scopes": ["memory:read", "memory:write"]}'

# 2. Copy the returned token (oa_...  — shown exactly once)

# 3. Connect your MCP client to http://localhost:8000/mcp with header
#    X-Orivory-Agent-Token: oa_...
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Next.js Frontend (Web)                       │
│  Landing | Chat | Memories | Discovery | Insights | Analytics   │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST API + SSE
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │   Auth   │ │   Chat   │ │ Memories │ │Discovery │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Sources │ │ Insights │ │Analytics │ │ Workspaces│      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              LangGraph Multi-Agent System              │    │
│  │  Router → Context → Retrieval → Grounding → Answer   │    │
│  └────────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Ingestion Pipeline (Celery)               │    │
│  │  Notion | Gmail | Drive | RSS | Web | Files           │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
│   PostgreSQL     │ │    Redis    │ │     MinIO      │
│   (Metadata)     │ │   (Cache)   │ │    (Storage)   │
└─────────────────┘ └─────────────┘ └─────────────────┘
                              │
                              ▼
                     ┌─────────────┐
                     │   ChromaDB  │
                     │  (Vectors)  │
                     └─────────────┘
```

---

## 📁 Project Structure

```
orivory/
├── app/                          # Python backend
│   ├── api/v1/                   # REST API endpoints
│   │   ├── auth.py              # Authentication (OAuth, JWT)
│   │   ├── chat.py              # Chat & conversation
│   │   ├── memories.py          # Memory management
│   │   ├── discovery.py         # Proactive discovery
│   │   ├── insights.py          # Insight cards
│   │   ├── sources.py           # Data source management
│   │   ├── entities.py          # Knowledge graph entities
│   │   ├── workspaces.py        # Team workspaces
│   │   ├── analytics.py         # Usage analytics
│   │   ├── referral.py          # Referral system
│   │   ├── sse.py              # Server-Sent Events
│   │   └── admin.py             # Admin endpoints
│   ├── agents/                   # LangGraph multi-agent system
│   │   ├── router_agent.py      # Query routing & classification
│   │   ├── memory_agent.py      # Memory operations
│   │   ├── crag_agent.py        # Corrective RAG with self-correction
│   │   ├── discovery_agent.py    # Proactive insight discovery
│   │   ├── insight_agent.py     # Insight generation
│   │   ├── answer_agent.py      # Final answer synthesis
│   │   ├── hallucination_agent.py # Hallucination detection
│   │   ├── evaluator_agent.py    # Answer quality evaluation
│   │   ├── feedback_agent.py    # User feedback processing
│   │   ├── grounding.py         # Grounding responses in facts
│   │   ├── retention_gate.py    # Memory retention decisions
│   │   ├── graph_context_agent.py # Knowledge graph queries
│   │   ├── personal_context_agent.py # Personal context extraction
│   │   └── prompts/             # Agent prompt management
│   │       ├── registry.py       # Prompt version control
│   │       ├── variants.py       # Prompt variants
│   │       └── integration.py    # Prompt integration
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── user.py              # User & authentication
│   │   ├── memory.py            # Memory chunks
│   │   ├── document.py          # Document metadata
│   │   ├── document_chunk.py    # Document chunking
│   │   ├── insight.py           # Generated insights
│   │   ├── entity.py            # Knowledge graph entities
│   │   ├── conversation.py      # Chat conversations
│   │   ├── message.py           # Chat messages
│   │   ├── source.py            # Data sources
│   │   ├── workspace.py         # Team workspaces
│   │   └── referral.py          # Referral tracking
│   ├── services/                 # Business logic services
│   ├── tasks/                   # Celery background workers
│   ├── ingestion/               # Multi-source data ingestion
│   │   └── connectors/          # Source connectors
│   │       ├── notion.py         # Notion integration
│   │       ├── gmail.py          # Gmail integration
│   │       ├── google_drive.py   # Google Drive integration
│   │       ├── rss.py            # RSS feed parsing
│   │       ├── web_clipper.py    # URL content extraction
│   │       ├── file_upload.py    # File processing
│   │       └── registry.py       # Connector registry
│   ├── graph/                    # Knowledge graph
│   │   ├── extraction.py        # Entity extraction
│   │   ├── clustering.py         # Cluster detection
│   │   └── builder.py            # Graph construction
│   ├── retrieval/                # RAG retrieval pipeline
│   │   └── memory/
│   │       ├── retriever.py      # Vector + keyword retrieval
│   │       ├── query_rewriter.py # Query expansion
│   │       └── context.py        # Context preparation
│   ├── middleware/              # FastAPI middleware
│   │   ├── logging_middleware.py # Structured logging
│   │   ├── rate_limiter.py      # Rate limiting
│   │   └── response_cache.py    # Response caching
│   ├── observability/            # Monitoring & tracking
│   │   ├── cost.py              # LLM cost tracking
│   │   ├── tracker.py           # Usage tracking
│   │   ├── experiments.py       # A/B testing
│   │   └── artifacts.py          # Trace artifacts
│   └── config.py                # Configuration management
├── frontend/                     # Next.js web application
│   ├── src/
│   │   ├── app/                 # App Router pages
│   │   │   ├── page.tsx         # Landing page
│   │   │   ├── chat/            # Chat interface
│   │   │   ├── memories/        # Memory dashboard
│   │   │   ├── discovery/       # Discovery feature
│   │   │   ├── insights/        # Insights dashboard
│   │   │   ├── analytics/       # Analytics dashboard
│   │   │   ├── workspaces/      # Workspace management
│   │   │   ├── documents/       # Document management
│   │   │   └── settings/        # User settings
│   │   ├── components/
│   │   │   ├── landing/         # Landing page sections
│   │   │   ├── chat/           # Chat UI components
│   │   │   ├── memories/       # Memory dashboard widgets
│   │   │   ├── insights/       # Insight card components
│   │   │   ├── discovery/      # Discovery widgets
│   │   │   ├── workspaces/     # Workspace components
│   │   │   ├── layout/         # Layout components
│   │   │   ├── onboarding/     # Onboarding flows
│   │   │   └── ui/             # Shared UI primitives
│   │   └── lib/
│   │       ├── api/            # API client functions
│   │       ├── sse.ts          # SSE client
│   │       └── utils.ts        # Utility functions
│   └── package.json
├── tests/                       # Test suite
├── scripts/                     # Utility scripts
├── docs/                        # Documentation
├── Dockerfile                   # Container definition
├── docker-compose.yml          # Local development
├── docker-compose.prod.yml     # Production deployment
├── pyproject.toml             # Python dependencies
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.12+, FastAPI 0.115, SQLAlchemy 2.0 |
| **AI/ML** | LangGraph, ChromaDB, Jina AI Reranker |
| **Agents** | 15+ specialized agents with self-correction |
| **Database** | PostgreSQL 16, Redis 7 |
| **Vector Store** | ChromaDB |
| **Storage** | MinIO (S3-compatible) |
| **Queue** | Celery + Flower |
| **Frontend** | Next.js 14, TypeScript 5, Radix UI |
| **Styling** | Tailwind CSS 3.4, Framer Motion |
| **Infrastructure** | Docker, Docker Compose |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- PostgreSQL 16+, Redis 7+

### One-Command Setup

```bash
# Clone and start all services
git clone https://github.com/twilightt1/orivory.git
cd orivory

# Start infrastructure
docker compose up -d postgres redis chromadb minio

# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start the frontend
cd frontend
pnpm install
pnpm dev
```

### Using Docker Compose (Full Stack)

```bash
# Start everything with Docker Compose
docker compose up -d

# View logs
docker compose logs -f app

# Access services
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Flower (Celery): http://localhost:5555
# - MinIO Console: http://localhost:9001
```

Visit [http://localhost:3000](http://localhost:3000) for the web app.

---

## 🔑 Key Concepts

### Multi-Agent System

Orivory uses a sophisticated multi-agent architecture where specialized agents collaborate to deliver accurate, grounded responses:

1. **Router Agent** — Classifies queries and routes to appropriate agents
2. **Memory Agent** — Manages memory operations (create, read, update, delete)
3. **Context Agents** — Extracts personal context, merges contexts, queries knowledge graph
4. **Retrieval Agents** — Performs hybrid search with reranking
5. **Grounding Agent** — Ensures responses are grounded in retrieved facts
6. **Correction Agent** — Self-corrects when hallucinations are detected
7. **Answer Agent** — Synthesizes final, cited responses
8. **Discovery Agent** — Proactively finds patterns and insights
9. **Insight Agent** — Generates actionable insight cards

### Corrective RAG (CRAG)

Unlike traditional RAG, Orivory implements Corrective RAG with:
- Self-evaluation of retrieval quality
- Automatic web search fallback for poor retrieval
- Hallucination detection before response delivery
- Quality scoring and filtering

### Proactive Discovery

Orivory doesn't just answer questions — it surfaces insights you didn't know to look for:

- **Pattern Detection** — Finds recurring themes across memories
- **Relationship Discovery** — Identifies hidden connections between entities
- **Trend Analysis** — Tracks changes over time
- **Anomaly Detection** — Surfaces unusual patterns

### Memory Architecture

- **Chunked Storage** — Documents split for optimal retrieval
- **Time-Aware** — Memories weighted by recency and relevance
- **Retention Gates** — Smart decisions on what to remember
- **Context Merging** — Combines multiple memory contexts

---

## 📊 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/*` | Authentication (login, register, OAuth) |
| `POST /api/v1/chat` | Send chat message with streaming response |
| `GET /api/v1/memories` | List and search memories |
| `POST /api/v1/memories` | Create new memory |
| `GET /api/v1/discovery` | Get proactive insights |
| `POST /api/v1/sources` | Connect data source |
| `GET /api/v1/insights` | List generated insights |
| `GET /api/v1/workspaces` | List workspaces |
| `POST /api/v1/workspaces` | Create workspace |
| `GET /api/v1/analytics` | Usage analytics |

Full API documentation available at `/docs`.

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md).

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run linting
ruff check app/ tests/

# Format code
ruff format app/ tests/
```

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org):

```bash
feat: add new feature
fix: resolve a bug
docs: update documentation
refactor: code refactoring
test: add or update tests
agent: modify agent behavior
```

---

## 🐛 Reporting Issues

Found a bug? [Open an issue](https://github.com/twilightt1/orivory/issues) with:

- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 🙏 Built With

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-FF6B35?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-5B21B6?style=for-the-badge&logo=chroma&logoColor=white)](https://www.trychroma.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Radix UI](https://img.shields.io/badge/Radix%20UI-161617?style=for-the-badge&logo=radixui&logoColor=white)](https://www.radix-ui.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)

</div>

---

<div align="center">

**⭐ Star us on GitHub if Orivory helps you build your second brain!**

*Orivory — AI Second Brain* ⭐

</div>
