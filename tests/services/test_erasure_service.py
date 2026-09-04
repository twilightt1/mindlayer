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
    otherwise the descendant-ids query (param = BFS frontier — one id or a
    list of them). BFS children are ownership-aware: ``foreign_child_ids``
    rows belong to another user and are returned only when the statement
    carries no ``user_id`` filter — i.e. when the service dropped the filter.
    """

    def __init__(self, *, owned=None, child_ids=None, entity_links=0, source_links=0, residual=None, rows=None, total=0,
                 foreign_child_ids=None):
        self._owned = owned or {}
        self._child_ids = child_ids or {}
        self._foreign_child_ids = foreign_child_ids or {}
        self._entity_links = entity_links
        self._source_links = source_links
        self._residual = residual or {"children": 0, "entity_links": 0, "source_links": 0}
        self._rows = rows or []
        self._total = total
        self.added = []
        self.deleted = []
        self.committed = 0
        self.rolled_back = False
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
        parent_id = next((v for v in params.values() if isinstance(v, (list, tuple))), None)
        if parent_id is not None:  # BFS frontier: children of every id in it
            found = [cid for pid in parent_id for cid in self._child_ids.get(pid, [])]
            if not any("user_id" in key for key in params):  # unfiltered query → cross-user rows leak in
                found += [cid for pid in parent_id for cid in self._foreign_child_ids.get(pid, [])]
            return _FakeRows(found)
        return _FakeRows(self._child_ids.get(next(iter(params.values()), None), []))

    def add(self, obj):
        self.added.append(obj)

    async def delete(self, obj):
        self.deleted.append(obj)

    async def commit(self):
        self.committed += 1

    async def rollback(self):
        self.rolled_back = True

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
    assert receipt.detail["summary"] == {"requested": 1, "erased": 1, "skipped": 0, "errors": 0, "residual_vectors": 0, "residual_rows": 0}
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
    assert target["affected_memory_ids"] == [str(child)]
    assert target["traversal_depth"] == 1
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


async def test_mid_call_error_still_produces_receipt_with_error_target(no_chroma):
    user_id, first, second = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    db = _FakeDB(owned={
        first: _memory_row(first, user_id),
        second: _memory_row(second, user_id),
    })
    real_delete = db.delete

    async def _fail_on_second(obj):
        if obj.id == second:
            raise RuntimeError("boom on second target")
        await real_delete(obj)

    db.delete = _fail_on_second

    receipt = await erase_memories(db, user_id, [first, second], requested_by="rest_api")

    # Target 1 still erased; target 2 recorded as error; receipt still written.
    target1, target2 = receipt.detail["targets"]
    assert target1["status"] == "deleted" and target1["memory_id"] == str(first)
    assert target2["status"] == "error" and target2["memory_id"] == str(second)
    assert "boom on second target" in target2["error"]
    assert target2["vector_residual_checked"] is False and target2["db_residual"] is None
    assert receipt.status == "completed_with_errors"
    assert db.rolled_back is True  # session poisoning cleared before the receipt commit
    assert receipt.detail["summary"]["erased"] == 1
    assert receipt.detail["summary"]["errors"] == 1


async def test_transitive_descendants_deleted_and_verified(no_chroma, monkeypatch):
    user_id, mid, child, grandchild = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    db = _FakeDB(owned={mid: _memory_row(mid, user_id)}, child_ids={mid: [child], child: [grandchild]})

    verified_ids: list[list[str]] = []

    async def _capture(_ids):
        verified_ids.append(list(_ids))
        return set()

    monkeypatch.setattr(erasure_service, "_chroma_present_ids", _capture)
    receipt = await erase_memories(db, user_id, [mid], requested_by="rest_api")

    target = receipt.detail["targets"][0]
    assert target["affected_memory_ids"] == [str(child), str(grandchild)]
    assert target["traversal_depth"] == 2
    assert sorted(target["vectors_deleted"]) == sorted([str(mid), str(child), str(grandchild)])
    assert sorted(no_chroma) == sorted([str(mid), str(child), str(grandchild)])
    # Verification re-query covers the whole affected set (target + descendants).
    assert verified_ids == [[str(mid), str(child), str(grandchild)]]


async def test_bfs_skips_foreign_user_descendants(no_chroma):
    """The descendant BFS must be ownership-checked: another user's child row is
    never collected, deleted, or disclosed (its vector stays unverified — the
    DB cascade still removes the row, which is unknowable from this scope)."""
    user_id, mid = uuid.uuid4(), uuid.uuid4()
    child, foreign_child = uuid.uuid4(), uuid.uuid4()
    db = _FakeDB(
        owned={mid: _memory_row(mid, user_id)},
        child_ids={mid: [child]},
        foreign_child_ids={mid: [foreign_child]},
    )

    receipt = await erase_memories(db, user_id, [mid], requested_by="rest_api")

    target = receipt.detail["targets"][0]
    assert str(foreign_child) not in target["affected_memory_ids"]
    assert sorted(target["vectors_deleted"]) == sorted([str(mid), str(child)])
    assert sorted(no_chroma) == sorted([str(mid), str(child)])
    # Compiled-SQL guard: every frontier query carries the user_id condition.
    bfs_stmts = [s for s in db.statements if "FROM memories" in _sql(s) and "count(" not in _sql(s).lower()]
    assert bfs_stmts, "BFS frontier statement not captured"
    for stmt in bfs_stmts:
        assert any("user_id" in key for key in stmt.compile(dialect=postgresql.dialect()).params)
    assert receipt.status == "completed"


async def test_depth_cap_flags_residual_status(no_chroma):
    """A 6-level chain vs the 5-level BFS cap: the traversal is truncated, the
    per-target detail flags it, and the receipt status is completed_with_residual."""
    user_id, mid = uuid.uuid4(), uuid.uuid4()
    chain = [uuid.uuid4() for _ in range(6)]  # mid → c1 → … → c6 (6 edges, cap 5)
    child_ids = {mid: [chain[0]]}
    child_ids.update({chain[i]: [chain[i + 1]] for i in range(5)})
    db = _FakeDB(owned={mid: _memory_row(mid, user_id)}, child_ids=child_ids)

    receipt = await erase_memories(db, user_id, [mid], requested_by="rest_api")

    target = receipt.detail["targets"][0]
    assert target["traversal_depth"] == 5
    assert target["depth_capped"] is True
    assert target["vectors_unverified_depth_cap"] == 1  # 6th level stays untracked
    assert target["affected_memory_ids"] == [str(c) for c in chain[:5]]
    assert target["vector_residual"] == []  # verified absence stays its own field
    assert receipt.status == "completed_with_residual"
    assert receipt.detail["summary"]["residual_vectors"] == 0


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
