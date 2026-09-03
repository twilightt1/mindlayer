"""Unit tests for the erasure service: cascade, receipts, verification.

DB access is faked (dispatch on compiled SQL, like
tests/services/test_access_ledger_service.py); Chroma is a monkeypatched
seam. CI-safe: no live Postgres, no Chroma.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy.dialects import postgresql

from app.models.erasure_receipt import ErasureReceipt
from app.models.memory import Memory
from app.services import erasure_service
from app.services.erasure_service import erase_memories, list_receipts


def _sql(stmt) -> str:
    return str(stmt.compile(dialect=postgresql.dialect()))


class _FakeScalar:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value


class _FakeRows:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


def _row_query(db):
    return next(s for s in db.statements if "count(" not in _sql(s).lower())


class _FakeDB:
    """Routes compiled SQL for exactly the statements erase_memories/list_receipts run:

    erasure_receipts → read tests (count → total, rows → rows); count( +
    memory_entities/memory_sources → link counts (residual when the statement
    carries a list param); count( + memories → residual children count;
    otherwise the child-id rows query (param = parent id).
    """

    def __init__(self, *, owned=None, child_ids=None, entity_links=0, source_links=0, residual=None, rows=None, total=0):
        self._owned = owned or {}
        self._child_ids = child_ids or {}
        self._entity_links = entity_links
        self._source_links = source_links
        self._residual = residual or {"children": 0, "entity_links": 0, "source_links": 0}
        self._rows = rows or []
        self._total = total
        self.added = []
        self.deleted = []
        self.committed = 0
        self.statements = []

    async def get(self, model, pk):
        return self._owned.get(pk)

    async def execute(self, stmt):
        sql = _sql(stmt).lower()
        self.statements.append(stmt)
        params = stmt.compile(dialect=postgresql.dialect()).params
        if "erasure_receipts" in sql:
            return _FakeScalar(self._total) if "count(" in sql else _FakeRows(self._rows)
        residual = any(isinstance(v, (list, tuple)) for v in params.values())
        if "count(" in sql:
            if "memory_entities" in sql:
                return _FakeScalar(self._residual["entity_links"] if residual else self._entity_links)
            if "memory_sources" in sql:
                return _FakeScalar(self._residual["source_links"] if residual else self._source_links)
            return _FakeScalar(self._residual["children"] if residual else 0)
        parent_id = next(iter(params.values()))
        return _FakeRows(self._child_ids.get(parent_id, []))

    def add(self, obj):
        self.added.append(obj)

    async def delete(self, obj):
        self.deleted.append(obj)

    async def commit(self):
        self.committed += 1

    async def refresh(self, _obj):
        return None


def _memory_row(memory_id, user_id) -> Memory:
    return Memory(id=memory_id, user_id=user_id, title="t", content="c")


@pytest.fixture()
def no_chroma(monkeypatch):
    deleted: list[str] = []

    async def _fake_delete(memory_id):
        deleted.append(str(memory_id))

    async def _no_residual(_ids):
        return set()

    monkeypatch.setattr(erasure_service, "safe_delete_from_chroma", _fake_delete)
    monkeypatch.setattr(erasure_service, "_chroma_present_ids", _no_residual)
    return deleted


async def test_erase_deletes_owned_memory_and_writes_receipt(no_chroma):
    user_id, mid = uuid.uuid4(), uuid.uuid4()
    db = _FakeDB(owned={mid: _memory_row(mid, user_id)}, entity_links=2, source_links=1)

    receipt = await erase_memories(db, user_id, [mid], requested_by="rest_api")

    assert [d.id for d in db.deleted] == [mid]
    assert receipt.status == "completed"
    assert receipt.requested_memory_ids == [str(mid)]
    target = receipt.detail["targets"][0]
    assert target["status"] == "deleted"
    assert target["entity_links"] == 2 and target["source_links"] == 1
    assert target["vectors_deleted"] == [str(mid)]
    assert target["vector_residual"] == [] and target["vector_residual_checked"] is True
    assert target["db_residual"] == {"children": 0, "entity_links": 0, "source_links": 0}
    assert receipt.detail["requested_by"] == "rest_api"
    assert receipt.detail["summary"] == {"requested": 1, "erased": 1, "skipped": 0, "residual_vectors": 0, "residual_rows": 0}
    assert no_chroma == [str(mid)]
    assert db.committed >= 2  # delete commit + receipt commit


async def test_erase_skips_foreign_or_missing_and_still_writes_receipt(no_chroma):
    user_id = uuid.uuid4()
    db = _FakeDB()  # nothing owned

    receipt = await erase_memories(db, user_id, [uuid.uuid4()], requested_by="rest_api")

    assert db.deleted == []
    assert receipt.status == "completed"
    assert receipt.detail["targets"] == [{"memory_id": receipt.requested_memory_ids[0], "status": "not_found_or_foreign"}]
    assert receipt.detail["summary"]["erased"] == 0


async def test_erase_dedups_input_ids(no_chroma):
    user_id, mid = uuid.uuid4(), uuid.uuid4()
    db = _FakeDB(owned={mid: _memory_row(mid, user_id)})

    receipt = await erase_memories(db, user_id, [mid, mid, mid], requested_by="rest_api")

    assert len(receipt.detail["targets"]) == 1
    assert receipt.detail["summary"]["requested"] == 1


async def test_erase_cascades_children_and_deletes_their_vectors(no_chroma):
    user_id, mid, child = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    db = _FakeDB(owned={mid: _memory_row(mid, user_id)}, child_ids={mid: [child]})

    receipt = await erase_memories(db, user_id, [mid], requested_by="rest_api")

    target = receipt.detail["targets"][0]
    assert target["child_memory_ids"] == [str(child)]
    assert sorted(target["vectors_deleted"]) == sorted([str(mid), str(child)])
    assert sorted(no_chroma) == sorted([str(mid), str(child)])


async def test_erase_records_vector_residual(no_chroma, monkeypatch):
    user_id, mid = uuid.uuid4(), uuid.uuid4()
    db = _FakeDB(owned={mid: _memory_row(mid, user_id)})

    async def _still_present(_ids):
        return {str(mid)}

    monkeypatch.setattr(erasure_service, "_chroma_present_ids", _still_present)
    receipt = await erase_memories(db, user_id, [mid], requested_by="rest_api")

    assert receipt.status == "completed_with_residual"
    assert receipt.detail["targets"][0]["vector_residual"] == [str(mid)]
    assert receipt.detail["summary"]["residual_vectors"] == 1


async def test_erase_records_db_residual(no_chroma):
    user_id, mid = uuid.uuid4(), uuid.uuid4()
    db = _FakeDB(owned={mid: _memory_row(mid, user_id)}, residual={"children": 1, "entity_links": 0, "source_links": 0})

    receipt = await erase_memories(db, user_id, [mid], requested_by="rest_api")

    assert receipt.status == "completed_with_residual"
    assert receipt.detail["targets"][0]["db_residual"]["children"] == 1
    assert receipt.detail["summary"]["residual_rows"] == 1


async def test_erase_survives_chroma_outage(no_chroma, monkeypatch):
    user_id, mid = uuid.uuid4(), uuid.uuid4()
    db = _FakeDB(owned={mid: _memory_row(mid, user_id)})

    async def _chroma_down(_ids):
        raise ConnectionError("chroma down")

    monkeypatch.setattr(erasure_service, "_chroma_present_ids", _chroma_down)
    receipt = await erase_memories(db, user_id, [mid], requested_by="rest_api")

    assert receipt.status == "completed"  # verification unknown ≠ residual
    assert receipt.detail["targets"][0]["vector_residual_checked"] is False


@pytest.mark.asyncio
async def test_list_receipts_scopes_every_query_to_user():
    user_id = uuid.uuid4()
    db = _FakeDB(rows=[ErasureReceipt(user_id=user_id)], total=2)

    _rows, total = await list_receipts(db, user_id)

    assert total == 2
    for stmt in db.statements:
        assert user_id in stmt.compile(dialect=postgresql.dialect()).params.values()


@pytest.mark.asyncio
async def test_list_receipts_orders_newest_first():
    db = _FakeDB(rows=[], total=0)

    await list_receipts(db, uuid.uuid4())

    assert "ORDER BY erasure_receipts.created_at DESC" in _sql(_row_query(db))


@pytest.mark.asyncio
async def test_list_receipts_clamps_limit():
    for requested, expected in ((5000, 200), (0, 1), (150, 150)):
        db = _FakeDB(rows=[], total=0)

        await list_receipts(db, uuid.uuid4(), limit=requested)

        assert _row_query(db)._limit_clause.value == expected, f"limit={requested}"
