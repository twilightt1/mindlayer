# MindLayer — Open Source AI Second Brain

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
  <img src="https://img.shields.io/badge/Chat-Open%20Source-brightgreen?style=for-the-badge" alt="Open Source" />
</p>

<p align="center">
  <a href="https://github.com/twilightt1/mindlayer/stargazers"><img src="https://img.shields.io/github/stars/twilightt1/mindlayer?style=social" alt="Stars"></a>
  <a href="https://github.com/twilightt1/mindlayer/network/members"><img src="https://img.shields.io/github/forks/twilightt1/mindlayer?style=social" alt="Forks"></a>
  <a href="https://github.com/twilightt1/mindlayer/issues"><img src="https://img.shields.io/github/issues/twilightt1/mindlayer" alt="Issues"></a>
</p>

---

**MindLayer** is an open-source, self-hosted AI second brain. It captures what you read, write, clip, and think — and lets you ask questions and get cited answers from your own knowledge.

**100% Self-Hosted** • **Your Data Stays Private** • **Fully Customizable**

---

## ✨ Features

| Category | Capabilities |
|----------|-------------|
| **💬 Chat & Recall** | Natural language Q&A with cited answers from your memories |
| **📝 Memory Capture** | Manual notes, file uploads, web clips, RSS feeds |
| **🔍 Hybrid Search** | Vector (ChromaDB) + keyword (BM25) + RRF fusion + reranking |
| **🕸️ Knowledge Graph** | Entity extraction, relations, clusters, graph visualization |
| **🤖 AI Agents** | LangGraph-powered recall workflow with self-correction |
| **📡 Real-time Streaming** | SSE token streaming with sources and trace events |
| **👥 Multi-user** | Teams, workspaces, shared knowledge bases |
| **📊 Analytics** | Usage tracking, DAU, feature adoption metrics |
| **🎁 Referrals** | Built-in viral referral system |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- PostgreSQL 15+, Redis 7+

### 1. Clone the Repository

```bash
git clone https://github.com/twilightt1/mindlayer.git
cd mindlayer
```

### 2. Start Infrastructure

```bash
docker compose up -d
```

### 3. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Run Migrations

```bash
alembic upgrade head
```

### 6. Start the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for API docs.

---

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   FastAPI   │────▶│  PostgreSQL │
│  (Web/CLI)  │     │     API     │     │   (Memory)  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│    Redis    │   │   MinIO     │   │   Celery    │
│   (Cache)   │   │  (Storage)  │   │  (Workers)  │
└─────────────┘   └─────────────┘   └──────┬──────┘
                                           │
                                           ▼
                                    ┌─────────────┐
                                    │  ChromaDB   │
                                    │  (Vectors)  │
                                    └─────────────┘
```

---

## 📁 Project Structure

```
mindlayer/
├── app/                    # Main application
│   ├── api/v1/            # API endpoints
│   │   ├── auth.py        # Authentication
│   │   ├── chat.py        # Chat & recall
│   │   ├── memories.py    # Memory management
│   │   ├── insights.py    # AI insights
│   │   ├── discovery.py   # Knowledge discovery
│   │   ├── referral.py    # Referral system
│   │   └── analytics.py   # Analytics
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   ├── agents/            # LangGraph agents
│   └── retrieval/         # RAG retrieval
├── frontend/              # Next.js frontend
├── tests/                 # Test suite
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

---

## 🤝 Contributing

We welcome contributions! Please see our contributing guide:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run linting
ruff check app/ tests/
```

---

## 🐛 Reporting Issues

Found a bug? [Open an issue](https://github.com/twilightt1/mindlayer/issues/new) with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details

---

## 📄 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agentic workflows
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [PostgreSQL](https://www.postgresql.org/) - Relational database
- [Redis](https://redis.io/) - Caching and queues
- [Next.js](https://nextjs.org/) - React framework

---

<p align="center">
  <strong>MindLayer</strong> — Your AI Second Brain, Open Source Forever
</p>
