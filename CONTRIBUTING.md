# Contributing to MindLayer

Thank you for your interest in contributing to MindLayer! This document provides guidelines and instructions for contributing.

---

## Code of Conduct

By participating in this project, you agree to maintain a welcoming and respectful environment for everyone.

---

## How Can I Contribute?

### 🐛 Reporting Bugs

Before opening a bug report:
1. Search existing issues to avoid duplicates
2. Use the bug report template
3. Include:
   - Clear description of the issue
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment (Python version, OS, etc.)
   - Error messages/logs

### 💡 Suggesting Features

We welcome feature suggestions! Please:
1. Check the roadmap and existing issues
2. Describe the feature clearly
3. Explain the use case and benefits
4. Consider backward compatibility

### 🔧 Pull Requests

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/mindlayer.git
   cd mindlayer
   ```
3. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```
4. **Make your changes**
5. **Test** your changes:
   ```bash
   pytest tests/ -v
   ```
6. **Lint** your code:
   ```bash
   ruff check app/ tests/
   ```
7. **Commit** with clear messages:
   ```bash
   git commit -m "feat: add new feature"
   git commit -m "fix: resolve issue with..."
   ```
8. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
9. **Open a Pull Request**

---

## Development Setup

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- PostgreSQL 15+, Redis 7+

### Quick Setup

```bash
# Clone repository
git clone https://github.com/twilightt1/mindlayer.git
cd mindlayer

# Start infrastructure
docker compose up -d

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/api/test_auth.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Code Style

We use:
- **Ruff** for linting and formatting
- **Black** compatible formatting
- **Type hints** required for new code

```bash
# Check code style
ruff check app/ tests/

# Auto-fix issues
ruff check --fix app/ tests/
```

---

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: resolve a bug
docs: update documentation
style: code style changes (formatting, etc.)
refactor: code refactoring
test: add or update tests
chore: maintenance tasks
```

Examples:
- `feat: add referral system`
- `fix: resolve auth token refresh issue`
- `docs: update API documentation`

---

## Project Structure

```
mindlayer/
├── app/                    # Main application
│   ├── api/v1/            # API endpoints
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

## Labels

| Label | Description |
|-------|-------------|
| `bug` | Bug reports |
| `enhancement` | New features |
| `documentation` | Documentation improvements |
| `good first issue` | Easy tasks for newcomers |
| `help wanted` | Seeking contributors |
| `question` | Questions and discussions |

---

## Questions?

- Open a [Discussion](https://github.com/twilightt1/mindlayer/discussions)
- Check [existing issues](https://github.com/twilightt1/mindlayer/issues)

---

Thank you for contributing to MindLayer! 🚀
