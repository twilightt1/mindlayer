"""Unit tests for MCP hub tools: scope enforcement + ledger writes.

The DB is faked; the retriever and the write-back side effects are
monkeypatched (CI-safe: no Chroma, no Celery, no real Postgres). These tests
call the tool implementations directly — the thin FastMCP wrappers are
exercised by the wiring test in test_server.py.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.mcp_hub import tools as hub_tools
from app.mcp_hub.identity import AgentPrincipal
from app.models.memory import Memory


def _principal(scopes: tuple[str, ...]) -> AgentPrincipal:
    return AgentPrincipal(
        user_id=uuid.uuid4(),
        agent_client_id=uuid.uuid4(),
        name="TestAgent",
        scopes=frozenset(scopes),
    )


def _memory_row(memory_id: uuid.UUID, user_id: uuid.UUID) -> Memory:
    return Memory(
        id=memory_id,
        user_id=user_id,
        title="pg indexing",
        content="Gin indexes speed up postgres lookups",
        tags=["db"],
        salience=0.9,
        captured_at=datetime.now(UTC),
    )


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def first(self):
        return self._rows[0] if self._rows else None


class _FakeDB:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.added = []
        self.deleted = []
        self.committed = 0

    async def execute(self, _stmt):
        return _FakeResult(self.rows)

    def add(self, obj):
        self.added.append(obj)

    async def delete(self, obj):
        self.deleted.append(obj)

    async def commit(self):
        self.committed += 1

    async def refresh(self, _obj):
        return None


class _FakeCtx:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, *exc):
        return False


def _fake_recall(ids):
    async def _recall(_query, _limit):
        return [(mid, 0.9) for mid in ids]

    return _recall


@pytest.fixture()
def reader(monkeypatch):
    p = _principal(("memory:read",))
    db = _FakeDB()
    monkeypatch.setattr(hub_tools, "_current_principal", lambda: p)
    monkeypatch.setattr(hub_tools, "_session", lambda: _FakeCtx(db))
    return p, db


@pytest.fixture()
def writer(monkeypatch):
    p = _principal(("memory:read", "memory:write"))
    db = _FakeDB()
    monkeypatch.setattr(hub_tools, "_current_principal", lambda: p)
    monkeypatch.setattr(hub_tools, "_session", lambda: _FakeCtx(db))
    return p, db


async def test_search_requires_read_scope(monkeypatch):
    p = _principal(())  # no scopes
    monkeypatch.setattr(hub_tools, "_current_principal", lambda: p)
    result = await hub_tools.search_memory(query="postgres")
    assert result == {"error": "scope memory:read required"}


async def test_search_requires_identity(monkeypatch):
    monkeypatch.setattr(hub_tools, "_current_principal", lambda: None)
    result = await hub_tools.search_memory(query="postgres")
    assert result == {"error": "agent identity required"}


async def test_search_returns_results_and_writes_ledger(reader, monkeypatch):
    p, db = reader
    memory = uuid.uuid4()
    db.rows = [_memory_row(memory, p.user_id)]
    monkeypatch.setattr(hub_tools, "_recall_memory_ids", _fake_recall([memory]))
    result = await hub_tools.search_memory(query="postgres indexing")
    assert result["results"][0]["id"] == str(memory)
    ledger = [o for o in db.added if type(o).__name__ == "MemoryAccessLog"]
    assert ledger and ledger[0].action == "mcp_search"
    assert ledger[0].detail["query"] == "postgres indexing"


async def test_add_memory_requires_write_scope(reader):
    result = await hub_tools.add_memory(title="t", content="c")
    assert result == {"error": "scope memory:write required"}


async def test_add_memory_creates_and_logs(writer, monkeypatch):
    p, db = writer
    indexed = []

    async def _fake_index(memory):
        indexed.append(memory)

    monkeypatch.setattr(hub_tools, "index_new_memory", _fake_index)
    result = await hub_tools.add_memory(title="Decision", content="Use pgvector", tags=["db"])
    assert result["title"] == "Decision"
    assert any(type(o).__name__ == "Memory" for o in db.added)
    assert any(type(o).__name__ == "MemoryAccessLog" and o.action == "mcp_add" for o in db.added)
    assert db.committed >= 1
    assert indexed and indexed[0].source_type == "mcp_agent"
    assert indexed[0].source_ref == "agent:TestAgent"
    assert indexed[0].user_id == p.user_id


async def test_delete_requires_write_scope(reader):
    result = await hub_tools.delete_memory(memory_id=str(uuid.uuid4()))
    assert result == {"error": "scope memory:write required"}


async def test_delete_owned_memory_deletes_and_logs(writer, monkeypatch):
    p, db = writer
    removed_from_chroma = []

    async def _fake_chroma_delete(memory_id):
        removed_from_chroma.append(memory_id)

    memory_id = uuid.uuid4()
    db.rows = [_memory_row(memory_id, p.user_id)]
    monkeypatch.setattr(hub_tools, "safe_delete_from_chroma", _fake_chroma_delete)
    result = await hub_tools.delete_memory(memory_id=str(memory_id))
    assert result["deleted"] is True
    assert db.deleted and db.deleted[0].id == memory_id
    ledger = [o for o in db.added if type(o).__name__ == "MemoryAccessLog"]
    assert ledger and ledger[0].action == "mcp_delete"
    assert ledger[0].memory_id == memory_id
    assert removed_from_chroma == [memory_id]
    assert db.committed >= 1


async def test_get_memory_returns_owned_row_and_logs(reader):
    p, db = reader
    memory_id = uuid.uuid4()
    db.rows = [_memory_row(memory_id, p.user_id)]
    result = await hub_tools.get_memory(memory_id=str(memory_id))
    assert result["id"] == str(memory_id)
    assert result["title"] == "pg indexing"
    ledger = [o for o in db.added if type(o).__name__ == "MemoryAccessLog"]
    assert ledger and ledger[0].action == "mcp_get"


async def test_list_recent_returns_rows_and_logs(reader):
    p, db = reader
    memory_id = uuid.uuid4()
    db.rows = [_memory_row(memory_id, p.user_id)]
    result = await hub_tools.list_recent(limit=5)
    assert result["results"][0]["id"] == str(memory_id)
    ledger = [o for o in db.added if type(o).__name__ == "MemoryAccessLog"]
    assert ledger and ledger[0].action == "mcp_list"
    assert ledger[0].detail["returned"] == 1
