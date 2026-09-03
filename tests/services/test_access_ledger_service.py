"""Unit tests for the access ledger read-model service. DB access is faked."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy.dialects import postgresql

from app.models.memory_access_log import MemoryAccessLog
from app.services.access_ledger_service import count_for_client, list_entries


def _sql(stmt) -> str:
    return str(stmt.compile(dialect=postgresql.dialect()))


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalars(self):
        return self

    def all(self):
        return self._value

    def scalar_one(self):
        return self._value


class _FakeDB:
    """Routes count queries to ``total``, row queries to ``rows``; records statements."""

    def __init__(self, rows, total=0):
        self._rows = rows
        self._total = total
        self.statements = []

    async def execute(self, stmt):
        self.statements.append(stmt)
        if "count(" in _sql(stmt).lower():
            return _FakeResult(self._total)
        return _FakeResult(self._rows)


def _row_query(db):
    return next(s for s in db.statements if "count(" not in _sql(s).lower())


@pytest.mark.asyncio
async def test_list_entries_scopes_every_query_to_user():
    user_id = uuid.uuid4()
    db = _FakeDB(rows=[MemoryAccessLog(user_id=user_id, action="memory:read")], total=3)

    rows, total = await list_entries(db, user_id)

    assert total == 3
    assert len(rows) == 1 and rows[0].user_id == user_id
    # Both the count and the row query must be scoped to exactly this user.
    for stmt in db.statements:
        assert user_id in stmt.compile(dialect=postgresql.dialect()).params.values()


@pytest.mark.asyncio
async def test_list_entries_orders_newest_first():
    db = _FakeDB(rows=[], total=0)

    await list_entries(db, uuid.uuid4())

    assert "ORDER BY memory_access_logs.created_at DESC" in _sql(_row_query(db))


@pytest.mark.asyncio
async def test_list_entries_clamps_limit():
    for requested, expected in ((5000, 200), (0, 1), (150, 150)):
        db = _FakeDB(rows=[], total=0)

        await list_entries(db, uuid.uuid4(), limit=requested)

        assert _row_query(db)._limit_clause.value == expected, f"limit={requested}"


@pytest.mark.asyncio
async def test_list_entries_clamps_negative_offset():
    db = _FakeDB(rows=[], total=0)

    await list_entries(db, uuid.uuid4(), offset=-5)

    assert _row_query(db)._offset_clause.value == 0


@pytest.mark.asyncio
async def test_list_entries_filters_by_agent_client_when_given():
    user_id, client_id = uuid.uuid4(), uuid.uuid4()
    db = _FakeDB(rows=[], total=1)

    await list_entries(db, user_id, agent_client_id=client_id)

    for stmt in db.statements:
        params = stmt.compile(dialect=postgresql.dialect()).params.values()
        assert user_id in params and client_id in params


@pytest.mark.asyncio
async def test_count_for_client_returns_scalar():
    user_id, client_id = uuid.uuid4(), uuid.uuid4()
    db = _FakeDB(rows=[], total=7)

    assert await count_for_client(db, user_id, client_id) == 7

    stmt = db.statements[0]
    assert "count(" in _sql(stmt).lower()
    params = stmt.compile(dialect=postgresql.dialect()).params.values()
    assert user_id in params and client_id in params
