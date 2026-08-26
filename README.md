# Orion Mind — Open Source AI Second Brain

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/twilightt1/orivory?style=for-the-badge)
![Forks](https://img.shields.io/github/forks/twilightt1/orivory?style=for-the-badge)

**Your AI-powered second brain. Open source. Self-hosted. Privacy-first.**

*[Orivory = Orion (constellation) + Memory]*

</div>

---

## 🌟 What is Orion Mind?

Orion Mind is an open-source, self-hosted AI second brain that helps you capture, organize, and retrieve your personal knowledge. Unlike cloud-based solutions, your data stays on your infrastructure — fully private and customizable.

### Core Philosophy

> **"Store what you know. Ask what you remember. Always cite your sources."**

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **🔍 Hybrid Search** | Vector + keyword search with RRF fusion and Jina reranking |
| **🧠 Memory Recall** | Ask questions in natural language, get cited answers |
| **🕸️ Knowledge Graph** | Entity extraction, relations, and cluster detection |
| **🤖 AI Agents** | LangGraph-powered workflow with self-correction |
| **📡 Real-time Streaming** | SSE token streaming with trace events |
| **👥 Multi-user** | Teams, workspaces, shared knowledge bases |
| **📊 Analytics** | Usage tracking and DAU metrics |
| **🎁 Referrals** | Built-in viral referral system |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- PostgreSQL 15+, Redis 7+

### One-Command Setup

```bash
# Clone and start
git clone https://github.com/twilightt1/orivory.git
cd orivory
docker compose up -d

# Install dependencies
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure and run
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for API documentation.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client (Web/CLI)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   Auth   │  │   Chat   │  │ Memories │  │ Analytics│       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  PostgreSQL   │  │    Redis     │  │    MinIO     │
│  (Metadata)  │  │   (Cache)    │  │  (Storage)   │
└───────────────┘  └───────────────┘  └───────────────┘
                            │
                            ▼
                   ┌───────────────┐
                   │   Celery      │
                   │  (Workers)    │
                   └───────┬───────┘
                           │
                           ▼
                   ┌───────────────┐
                   │   ChromaDB    │
                   │  (Vectors)   │
                   └───────────────┘
```

---

## 📁 Project Structure

```
orivory/
├── app/                    # Python backend
│   ├── api/v1/           # REST API endpoints
│   ├── models/           # SQLAlchemy models
│   ├── services/         # Business logic
│   ├── agents/           # LangGraph agents
│   └── retrieval/        # RAG pipeline
├── frontend/              # Next.js web app
├── tests/                # Test suite
├── scripts/              # Utility scripts
└── docs/                 # Documentation
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy |
| **AI/ML** | LangGraph, ChromaDB, Jina Reranker |
| **Database** | PostgreSQL, Redis |
| **Storage** | MinIO (S3-compatible) |
| **Queue** | Celery |
| **Frontend** | Next.js 14, TypeScript |
| **Infrastructure** | Docker, Docker Compose |

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
```

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
feat: add new feature
fix: resolve a bug
docs: update documentation
refactor: code refactoring
test: add or update tests
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

</div>

---

<div align="center">

**⭐ Star us on GitHub if Orion Mind helps you build your second brain!**

*Orion Mind — Your AI Second Brain from the Stars* ⭐🐺

</div>
