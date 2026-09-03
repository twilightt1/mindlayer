# Erasure Receipts v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verifiable memory erasure: one `ErasureReceipt` per call recording which rows/links/vectors were cascade-deleted and what the post-deletion adversarial verification pass found — exposed as the MCP `forget_memory` tool and `POST/GET /api/v1/erasure-receipts`.

**Architecture:** New `erasure_receipts` table; one row per erasure call. `app/services/erasure_service.py` owns the cascade per id: ownership check (foreign/missing ids recorded, not deleted) → collect cascade targets BEFORE deletion (children via `parent_id`, entity/source-link counts) → row delete (ORM/DB cascade, same path as `DELETE /api/v1/memories/{id}`) → `safe_delete_from_chroma` for every affected id (children are separately indexed rows) → adversarial verification pass re-querying Chroma and re-counting residual DB rows, recorded per-target. MCP tool (`memory:write`, ledgered as `ACTION_FORGET = "mcp_forget"`) and REST router both funnel through the service. Receipts cascade away with the user (they quote personal memory ids).

**Tech Stack:** FastAPI 0.115, SQLAlchemy 2.0 async + Alembic, ChromaDB via existing `app/retrieval/memory/vector_store.py` seams, Pydantic v2. No new dependencies.

**Spec:** `docs/ideas/open-memory-hub.md` (MVP item 5: cascade deletion + verification report, adversarially verified) + `docs/research/PAPERS_HCI_PRIVACY.md` §3 (3.1 store-side deletion is verifiable; 3.2 deletion must cascade across derived artifacts; 3.3 deletion claims need verification, not trust).

## Global Constraints

- Python 3.12+, ruff line-length 120, target py313 (`pyproject.toml`).
- Ruff gate: **zero NEW findings in touched files** — run `ruff check <touched paths>`. The repo-wide baseline is red (~224 pre-existing findings, e.g. `app/services/experiments_service.py` W293); never run a repo-wide `--fix`.
- All routes under `/api/v1`; routers use `Annotated[User, Depends(get_current_verified_user)]` + `Annotated[AsyncSession, Depends(get_db)]` (pattern: `app/api/v1/memories.py:76-102`, `app/api/v1/agents.py`).
- Postgres is source of truth; Chroma stays best-effort. Erasure side effects go through the monkeypatchable seams only: `safe_delete_from_chroma` (`app/retrieval/memory/write_back.py`) for deletion, `erasure_service._chroma_present_ids` (wraps the new `vector_store.get_memory_ids_present`) for residual checks. Tests never touch real Chroma.
- Migration: new revision `e6f7a8b9c0d1`, `down_revision = "d4e5f6a7b8c9"` (current head). Ruff-clean migration style: `from collections.abc import Sequence`, `str | None`.
- New model follows `app/models/memory_access_log.py` style: `from __future__ import annotations`, `Mapped[...]` columns, `__init__` populating Python-side defaults for transient instances, exports in `__all__` + `app/models/__init__.py`.
- Aware `datetime.now(UTC)` convention (`app/api/v1/agents.py:150`).
- CI-safe tests only: fake DB sessions + monkeypatch like `tests/mcp_hub/test_tools.py` and `tests/services/test_access_ledger_service.py`; no live Postgres/Chroma/Celery in unit tests. Note: the session-scoped autouse `setup_db` fixture in `tests/conftest.py` **skips the whole suite (exit green, 0 run) when Postgres at `localhost:55432` is unreachable** — locally without a DB, "PASS" may show as SKIP; CI provides the DB. `pytest.ini` sets `asyncio_mode = auto`, so bare `async def` tests need no marks.
- Register the new router in `tests/api/test_router_wiring.py:ROUTERS_TO_CHECK`.
- Every task ends with `ruff check` on touched files clean + the touched pytest subset green + a Conventional Commit.

---

### Task 1: ErasureReceipt model + migration

**Files:**
- Create: `app/models/erasure_receipt.py`
- Modify: `app/models/__init__.py` (import + `"ErasureReceipt"` in `__all__`, grouped with `AgentClient`/`MemoryAccessLog`)
- Create: `alembic/versions/e6f7a8b9c0d1_erasure_receipts.py`
- Test: `tests/models/test_erasure_models.py`

**Interfaces:**
- Produces: `ErasureReceipt` — fields `id: uuid.UUID`, `user_id: uuid.UUID` (FK users.id CASCADE), `requested_memory_ids: list[str]` (JSONB, deduped input as strings), `status: str` default `"completed"`, `detail: dict` (JSONB per-target results + verification), `created_at: datetime`. Later tasks import it from `app.models.erasure_receipt`.
- Produces: migration `e6f7a8b9c0d1` (new head), down_revision `"d4e5f6a7b8c9"`.

- [ ] **Step 1: Write the failing test** — `tests/models/test_erasure_models.py`:

```python
"""Unit tests for the ErasureReceipt model: shape and defaults."""
from __future__ import annotations

import uuid

from app.models.erasure_receipt import ErasureReceipt


def test_erasure_receipt_defaults():
    receipt = ErasureReceipt(user_id=uuid.uuid4(), requested_memory_ids=[str(uuid.uuid4())])
    assert receipt.status == "completed"
    assert receipt.detail == {}
    assert len(receipt.requested_memory_ids) == 1


def test_erasure_receipt_empty_targets_default():
    receipt = ErasureReceipt(user_id=uuid.uuid4())
    assert receipt.requested_memory_ids == []
    assert receipt.status == "completed"
```

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/models/test_erasure_models.py -v` → FAIL (ImportError).
- [ ] **Step 3: Write the model** — `app/models/erasure_receipt.py`:

```python
"""Erasure receipts — verifiable proof of what a memory erasure removed.

One row per erasure call (MCP ``forget_memory`` or the REST erasure API).
``detail`` carries the per-target results: which rows/links/vectors were
deleted and what the post-deletion verification pass (re-query Chroma +
residual DB row counts) found. Unlike the append-only access ledger,
receipts carry a FK to ``users`` with CASCADE: they quote personal memory
ids, so they must not outlive the user (open-memory-hub.md MVP item 5).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import TIMESTAMP, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ErasureReceipt(Base):
    __tablename__ = "erasure_receipts"

    id:                   Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id:              Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_memory_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False)
    status:               Mapped[str]       = mapped_column(String(16), default="completed", server_default="completed", nullable=False)
    detail:               Mapped[dict]      = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    created_at:           Mapped[datetime]  = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)

    __table_args__ = (
        Index("ix_erasure_receipts_user_time", "user_id", "created_at"),
    )

    def __init__(self, **kwargs: Any) -> None:
        # SQLAlchemy applies column defaults at flush time only; populate the
        # defaults here as well so transient instances (and unit tests) see them.
        kwargs.setdefault("requested_memory_ids", [])
        kwargs.setdefault("status", "completed")
        kwargs.setdefault("detail", {})
        super().__init__(**kwargs)


__all__ = ["ErasureReceipt"]
```

Then add `from app.models.erasure_receipt import ErasureReceipt` (alphabetical) and `"ErasureReceipt"` to `app/models/__init__.py`.

- [ ] **Step 4: Run test to verify it passes** — `pytest tests/models/test_erasure_models.py -v` → PASS (or SKIP without Postgres).
- [ ] **Step 5: Write the migration** — `alembic/versions/e6f7a8b9c0d1_erasure_receipts.py`:

```python
"""Erasure receipts — verifiable cascade-deletion proof (Open Memory Hub MVP 5)

One row per erasure call. ``requested_memory_ids`` is the deduplicated input;
``detail`` records per-target cascade results plus the post-deletion
verification pass. Receipts cascade away with the user (they quote personal
memory ids, so they must not outlive the user).

Revision ID: e6f7a8b9c0d1
Revises: d4e5f6a7b8c9
Create Date: 2026-09-02 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "e6f7a8b9c0d1"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "erasure_receipts",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_memory_ids", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(16), nullable=False, server_default="completed"),
        sa.Column("detail", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_erasure_receipts_user_id", "erasure_receipts", ["user_id"])
    op.create_index("ix_erasure_receipts_user_time", "erasure_receipts", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_erasure_receipts_user_time", table_name="erasure_receipts")
    op.drop_index("ix_erasure_receipts_user_id", table_name="erasure_receipts")
    op.drop_table("erasure_receipts")
```

- [ ] **Step 6: Lint + subset** — `ruff check app/models/erasure_receipt.py app/models/__init__.py alembic/versions/e6f7a8b9c0d1_erasure_receipts.py tests/models/test_erasure_models.py` → 0 errors; `pytest tests/models -q` → green (PASS or SKIP).
- [ ] **Step 7: Commit** — `git commit -m "feat: erasure receipts model + migration"`.

---

### Task 2: Erasure service (cascade + adversarial verification)

**Files:**
- Create: `app/services/erasure_service.py`
- Modify: `app/retrieval/memory/vector_store.py` (append `get_memory_ids_present` after `get_existing_memory_ids_sync`)
- Test: `tests/services/test_erasure_service.py`

**Interfaces:**
- Consumes: `ErasureReceipt` (Task 1); `Memory.parent_id` (`app/models/memory.py:53`); `MemoryEntity` (`app/models/entity.py:141`), `MemorySource` (`app/models/source.py:105`) — both link tables have `memory_id` FK `ondelete="CASCADE"`; `safe_delete_from_chroma(memory_id: UUID | str) -> None` (never raises — `app/retrieval/memory/write_back.py:45`).
- Produces (used by Tasks 3–4):
  - Constants `ERASURE_STATUS_COMPLETED = "completed"`, `ERASURE_STATUS_RESIDUAL = "completed_with_residual"`, `NOT_FOUND_OR_FOREIGN = "not_found_or_foreign"`.
  - `async def erase_memories(db: AsyncSession, user_id: uuid.UUID, memory_ids: list[uuid.UUID], *, requested_by: str) -> ErasureReceipt` — order-preserving dedup (`dict.fromkeys`); one receipt per call. `detail` = `{"requested_by": str, "targets": list[dict], "summary": {"requested": int, "erased": int, "skipped": int, "residual_vectors": int, "residual_rows": int}}`. Per-target deleted dict: `{"memory_id": str, "status": "deleted", "child_memory_ids": list[str], "entity_links": int, "source_links": int, "vectors_deleted": list[str], "vector_residual": list[str], "vector_residual_checked": bool, "db_residual": {"children": int, "entity_links": int, "source_links": int}}`; skipped: `{"memory_id": str, "status": "not_found_or_foreign"}`. Receipt `status` = `completed_with_residual` iff any residual vector/DB row detected.
  - `async def list_receipts(db: AsyncSession, user_id: uuid.UUID, *, limit: int = 50, offset: int = 0) -> tuple[list[ErasureReceipt], int]` — newest first, `limit` clamped into [1, 200], negative offset clamped to 0 (exact `access_ledger_service.list_entries` semantics).
  - `async def _chroma_present_ids(memory_ids: list[str]) -> set[str]` — verification seam (monkeypatched in tests).
  - `async def get_memory_ids_present(memory_ids: list[str]) -> set[str]` in `vector_store.py`.

- [ ] **Step 1: Add the vector-store verification helper** — append to `app/retrieval/memory/vector_store.py`:

```python
async def get_memory_ids_present(memory_ids: list[str]) -> set[str]:
    """Return the subset of ``memory_ids`` that still exist in the collection.

    Verification seam for erasure receipts: after deletion the erasure
    service re-queries the collection through this helper and records any
    ids still present as residuals. Async counterpart of
    :func:`get_existing_memory_ids_sync`.
    """
    if not memory_ids:
        return set()
    collection = await _get_collection()
    found = await collection.get(ids=memory_ids, include=[])
    return {str(i) for i in (found.get("ids") or [])}
```

(`collection.get` returns a `GetResult` TypedDict; the `found.get("ids", [])` idiom already exists at `vector_store.py:273`. No unit test for this thin wrapper — exercised via the monkeypatched service seam.)

- [ ] **Step 2: Write the failing test** — `tests/services/test_erasure_service.py`:

```python
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

    rows, total = await list_receipts(db, user_id)

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
```

- [ ] **Step 3: Run to verify it fails** — `pytest tests/services/test_erasure_service.py -v` → FAIL (ImportError: `erasure_service`).
- [ ] **Step 4: Implement** — `app/services/erasure_service.py`:

```python
"""Memory erasure with verifiable receipts — Open Memory Hub MVP item 5.

One call → one ``ErasureReceipt``. Per memory id: ownership check (foreign/
missing ids recorded, never deleted), cascade targets collected BEFORE
deletion (papers §3.2), row delete via the ORM cascade, ``safe_delete_from_chroma``
for every affected id, then an adversarial verification pass (papers §3.3):
re-query Chroma + re-count residual DB rows; any hit flips the receipt to
``completed_with_residual``. v0 verification = absence-checks of every
derived artifact; KG re-inference probing is a tracked follow-up.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import MemoryEntity
from app.models.erasure_receipt import ErasureReceipt
from app.models.memory import Memory
from app.models.source import MemorySource
from app.retrieval.memory.write_back import safe_delete_from_chroma

log = logging.getLogger(__name__)

ERASURE_STATUS_COMPLETED = "completed"
ERASURE_STATUS_RESIDUAL = "completed_with_residual"
NOT_FOUND_OR_FOREIGN = "not_found_or_foreign"

_MAX_LIMIT = 200


async def _chroma_present_ids(memory_ids: list[str]) -> set[str]:
    """Verification seam — re-query the Chroma collection for residual ids.

    Monkeypatched in tests; the vector-store helper is imported lazily so a
    missing/failed Chroma import cannot break the DB erasure.
    """
    from app.retrieval.memory.vector_store import get_memory_ids_present

    return await get_memory_ids_present(memory_ids)


async def _verify_absent(memory_ids: list[uuid.UUID]) -> set[str] | None:
    """Return ids still present in Chroma, or ``None`` when Chroma is down.

    ``None`` = verification unknown — recorded as ``vector_residual_checked:
    false`` without failing the erasure (Postgres is the source of truth).
    """
    try:
        return await _chroma_present_ids([str(m) for m in memory_ids])
    except Exception as exc:
        log.warning("Chroma residual check failed: %s", exc, extra={"memory_ids": [str(m) for m in memory_ids]})
        return None


async def _db_residual_counts(db: AsyncSession, memory_ids: list[uuid.UUID]) -> dict[str, int]:
    """Re-count cascade targets after deletion; anything > 0 is a residual."""
    children = (await db.execute(
        select(func.count(Memory.id)).where(Memory.parent_id.in_(memory_ids))
    )).scalar_one()
    entity_links = (await db.execute(
        select(func.count()).select_from(MemoryEntity).where(MemoryEntity.memory_id.in_(memory_ids))
    )).scalar_one()
    source_links = (await db.execute(
        select(func.count()).select_from(MemorySource).where(MemorySource.memory_id.in_(memory_ids))
    )).scalar_one()
    return {"children": int(children), "entity_links": int(entity_links), "source_links": int(source_links)}


async def _erase_one(db: AsyncSession, user_id: uuid.UUID, memory_id: uuid.UUID) -> dict[str, Any]:
    """Erase one owned memory and return its per-target receipt entry."""
    row = await db.get(Memory, memory_id)
    if row is None or row.user_id != user_id:
        return {"memory_id": str(memory_id), "status": NOT_FOUND_OR_FOREIGN}

    # Collect cascade targets BEFORE deletion (receipt must describe what went away).
    child_ids = list((await db.execute(
        select(Memory.id).where(Memory.parent_id == memory_id)
    )).scalars().all())
    entity_links = (await db.execute(
        select(func.count()).select_from(MemoryEntity).where(MemoryEntity.memory_id == memory_id)
    )).scalar_one()
    source_links = (await db.execute(
        select(func.count()).select_from(MemorySource).where(MemorySource.memory_id == memory_id)
    )).scalar_one()

    affected = [memory_id, *child_ids]
    await db.delete(row)  # ORM cascade: children + links go with it (DB CASCADE too)
    await db.commit()

    vectors_deleted = []
    for vid in affected:
        await safe_delete_from_chroma(vid)  # never raises (write_back.py)
        vectors_deleted.append(str(vid))

    present = await _verify_absent(affected)
    db_residual = await _db_residual_counts(db, affected)
    return {
        "memory_id": str(memory_id),
        "status": "deleted",
        "child_memory_ids": [str(c) for c in child_ids],
        "entity_links": int(entity_links),
        "source_links": int(source_links),
        "vectors_deleted": vectors_deleted,
        "vector_residual": sorted(present) if present is not None else [],
        "vector_residual_checked": present is not None,
        "db_residual": db_residual,
    }


async def erase_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    memory_ids: list[uuid.UUID],
    *,
    requested_by: str,
) -> ErasureReceipt:
    """Erase every owned memory among ``memory_ids`` and write one receipt."""
    unique_ids = list(dict.fromkeys(memory_ids))
    targets: list[dict[str, Any]] = [await _erase_one(db, user_id, mid) for mid in unique_ids]
    erased = sum(1 for t in targets if t["status"] == "deleted")
    residual_vectors = sum(len(t["vector_residual"]) for t in targets if t["status"] == "deleted")
    residual_rows = sum(sum(t["db_residual"].values()) for t in targets if t["status"] == "deleted")

    receipt = ErasureReceipt(
        user_id=user_id,
        requested_memory_ids=[str(m) for m in unique_ids],
        status=ERASURE_STATUS_RESIDUAL if (residual_vectors or residual_rows) else ERASURE_STATUS_COMPLETED,
        detail={
            "requested_by": requested_by,
            "targets": targets,
            "summary": {
                "requested": len(unique_ids),
                "erased": erased,
                "skipped": len(unique_ids) - erased,
                "residual_vectors": residual_vectors,
                "residual_rows": residual_rows,
            },
        },
    )
    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)
    return receipt


async def list_receipts(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ErasureReceipt], int]:
    """List a user's receipts newest first, with the unpaginated total count.

    ``limit`` is clamped into [1, 200] and a negative ``offset`` to 0 — same
    contract as ``access_ledger_service.list_entries``.
    """
    total = (await db.execute(
        select(func.count(ErasureReceipt.id)).where(ErasureReceipt.user_id == user_id)
    )).scalar_one()
    rows = (await db.execute(
        select(ErasureReceipt)
        .where(ErasureReceipt.user_id == user_id)
        .order_by(ErasureReceipt.created_at.desc())
        .offset(max(offset, 0))
        .limit(max(1, min(limit, _MAX_LIMIT)))
    )).scalars().all()
    return list(rows), total


__all__ = [
    "ERASURE_STATUS_COMPLETED",
    "ERASURE_STATUS_RESIDUAL",
    "NOT_FOUND_OR_FOREIGN",
    "erase_memories",
    "list_receipts",
]
```

- [ ] **Step 5: Run to verify it passes** — `pytest tests/services/test_erasure_service.py -v` → PASS (or SKIP).
- [ ] **Step 6: Lint + subset** — `ruff check app/services/erasure_service.py app/retrieval/memory/vector_store.py tests/services/test_erasure_service.py` → 0 errors; `pytest tests/services -q` → green.
- [ ] **Step 7: Commit** — `git commit -m "feat: erasure service (cascade erase + adversarial verification)"`.

---

### Task 3: MCP tool `forget_memory` + ledger action

**Files:**
- Modify: `app/mcp_hub/identity.py` (add `ACTION_FORGET` after `ACTION_DELETE`, extend `__all__`)
- Modify: `app/mcp_hub/tools.py` (add `forget_memory`, extend `__all__`)
- Modify: `app/mcp_hub/server.py` (register the FastMCP wrapper after `delete_memory`)
- Modify: `tests/mcp_hub/test_server.py` (one wiring test)
- Test: `tests/mcp_hub/test_forget_tool.py`

**Interfaces:**
- Consumes: `erase_memories(db, user_id, memory_ids, *, requested_by) -> ErasureReceipt` (Task 2); the tool seams `_current_principal()` / `_session()` / `_ledger_entry(principal, action, *, memory_id=None, detail=None)` in `app/mcp_hub/tools.py`.
- Produces: `ACTION_FORGET = "mcp_forget"` (exported in `identity.py.__all__`); `async def forget_memory(memory_ids: list[str]) -> dict[str, Any]` returning exactly `{"receipt_id": str, "status": str, "erased": int, "skipped": int, "invalid": list[str]}` on success, or `{"error": ...}` (`"agent identity required"` / `"scope memory:write required"` / `"invalid memory id"`) — never raises.

- [ ] **Step 1: Add the action constant** — in `app/mcp_hub/identity.py`:

```python
ACTION_FORGET = "mcp_forget"
```

plus `"ACTION_FORGET"` in that module's `__all__`.

- [ ] **Step 2: Write the failing test** — `tests/mcp_hub/test_forget_tool.py` (same seams as `tests/mcp_hub/test_tools.py`):

```python
"""Unit tests for the forget_memory MCP tool: scope enforcement + ledger."""
from __future__ import annotations

import uuid

import pytest

from app.mcp_hub import tools as hub_tools
from app.mcp_hub.identity import ACTION_FORGET, AgentPrincipal
from app.models.erasure_receipt import ErasureReceipt
from app.services.erasure_service import ERASURE_STATUS_COMPLETED


def _principal(scopes: tuple[str, ...]) -> AgentPrincipal:
    return AgentPrincipal(user_id=uuid.uuid4(), agent_client_id=uuid.uuid4(), name="TestAgent", scopes=frozenset(scopes))


def _receipt(user_id: uuid.UUID, memory_id: uuid.UUID, *, erased: int, skipped: int) -> ErasureReceipt:
    return ErasureReceipt(
        id=uuid.uuid4(),
        user_id=user_id,
        requested_memory_ids=[str(memory_id)],
        status=ERASURE_STATUS_COMPLETED,
        detail={"summary": {"requested": 1, "erased": erased, "skipped": skipped, "residual_vectors": 0, "residual_rows": 0}},
    )


class _FakeDB:
    def __init__(self):
        self.added = []
        self.committed = 0

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed += 1


class _FakeCtx:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, *exc):
        return False


@pytest.fixture()
def writer(monkeypatch):
    p = _principal(("memory:read", "memory:write"))
    db = _FakeDB()

    async def _fake_erase(db_, user_id, memory_ids, *, requested_by):
        assert user_id == p.user_id
        assert requested_by == "agent:TestAgent"
        return _receipt(user_id, memory_ids[0], erased=len(memory_ids), skipped=0)

    monkeypatch.setattr(hub_tools, "_current_principal", lambda: p)
    monkeypatch.setattr(hub_tools, "_session", lambda: _FakeCtx(db))
    monkeypatch.setattr(hub_tools, "erase_memories", _fake_erase)
    return p, db


async def test_forget_requires_identity(monkeypatch):
    monkeypatch.setattr(hub_tools, "_current_principal", lambda: None)
    assert await hub_tools.forget_memory(memory_ids=[str(uuid.uuid4())]) == {"error": "agent identity required"}


async def test_forget_requires_write_scope(monkeypatch):
    monkeypatch.setattr(hub_tools, "_current_principal", lambda: _principal(("memory:read",)))
    assert await hub_tools.forget_memory(memory_ids=[str(uuid.uuid4())]) == {"error": "scope memory:write required"}


async def test_forget_all_invalid_ids(monkeypatch):
    monkeypatch.setattr(hub_tools, "_current_principal", lambda: _principal(("memory:write",)))
    assert await hub_tools.forget_memory(memory_ids=["not-a-uuid"]) == {"error": "invalid memory id"}


async def test_forget_calls_erasure_service_returns_summary_and_logs(writer):
    p, db = writer
    mid = uuid.uuid4()
    result = await hub_tools.forget_memory(memory_ids=[str(mid)])

    assert result["erased"] == 1 and result["skipped"] == 0
    assert result["invalid"] == []
    assert result["status"] == ERASURE_STATUS_COMPLETED
    assert uuid.UUID(result["receipt_id"])
    ledger = [o for o in db.added if type(o).__name__ == "MemoryAccessLog"]
    assert ledger and ledger[0].action == ACTION_FORGET == "mcp_forget"
    assert ledger[0].detail["receipt_id"] == result["receipt_id"]
    assert ledger[0].detail["requested"] == [str(mid)]
    assert db.committed >= 1


async def test_forget_filters_invalid_ids_and_reports_them(writer, monkeypatch):
    p, _ = writer
    seen: list[list[uuid.UUID]] = []

    async def _spy(db_, user_id, memory_ids, *, requested_by):
        seen.append(list(memory_ids))
        return _receipt(user_id, memory_ids[0], erased=len(memory_ids), skipped=0)

    monkeypatch.setattr(hub_tools, "erase_memories", _spy)
    good = str(uuid.uuid4())
    result = await hub_tools.forget_memory(memory_ids=[good, "nope"])

    assert [str(m) for m in seen[0]] == [good]
    assert result["invalid"] == ["nope"]
```

- [ ] **Step 3: Run to verify it fails** — `pytest tests/mcp_hub/test_forget_tool.py -v` → FAIL (AttributeError/ImportError).
- [ ] **Step 4: Implement the tool** — in `app/mcp_hub/tools.py` add `ACTION_FORGET` to the identity import block, add `from app.services.erasure_service import erase_memories`, then after `delete_memory`:

```python
async def forget_memory(memory_ids: list[str]) -> dict[str, Any]:
    """Erase memories + every derived artifact, with a verification receipt.

    Requires ``memory:write``. Foreign/missing ids are recorded in the
    receipt as ``not_found_or_foreign`` (never an existence leak). Every
    authorized call appends one ``mcp_forget`` ledger row pointing at the
    receipt; the receipt carries the per-target cascade + verification detail.
    """
    principal = _current_principal()
    if principal is None:
        return IDENTITY_ERROR
    if not principal.can_write():
        return WRITE_SCOPE_ERROR
    valid: list[UUID] = []
    invalid: list[str] = []
    for raw in memory_ids:
        try:
            valid.append(UUID(raw))
        except ValueError:
            invalid.append(raw)
    if not valid:
        return {"error": "invalid memory id"}
    async with _session() as db:
        receipt = await erase_memories(db, principal.user_id, valid, requested_by=f"agent:{principal.name}")
        summary = receipt.detail.get("summary", {})
        db.add(
            _ledger_entry(
                principal,
                ACTION_FORGET,
                detail={
                    "receipt_id": str(receipt.id),
                    "requested": [str(m) for m in valid],
                    "erased": summary.get("erased", 0),
                    "skipped": summary.get("skipped", 0),
                },
            )
        )
        await db.commit()
    return {
        "receipt_id": str(receipt.id),
        "status": receipt.status,
        "erased": summary.get("erased", 0),
        "skipped": summary.get("skipped", 0),
        "invalid": invalid,
    }
```

plus `"forget_memory"` in the module's `__all__`.

- [ ] **Step 5: Register the FastMCP wrapper** — in `app/mcp_hub/server.py`, after the `delete_memory` wrapper inside `_build_server()`:

```python
    @mcp.tool()
    async def forget_memory(memory_ids: list[str], ctx: Context = None) -> dict[str, Any]:
        """Erase memories and derived artifacts with a verification receipt (memory:write)."""
        return await _call_with_identity(hub_tools.forget_memory(memory_ids=memory_ids), ctx)
```

- [ ] **Step 6: Wiring test** — append to `tests/mcp_hub/test_server.py`:

```python
async def test_build_mcp_server_registers_forget_tool():
    server = build_mcp_server()
    tools = await server.list_tools()
    assert any(t.name == "forget_memory" for t in tools)
```

- [ ] **Step 7: Run to verify it passes** — `pytest tests/mcp_hub -v` → PASS (or SKIP).
- [ ] **Step 8: Lint + commit** — `ruff check app/mcp_hub tests/mcp_hub` → 0 errors; `pytest tests/mcp_hub tests/services -q` → green; `git commit -m "feat: forget_memory MCP tool with erasure receipts"`.

---

### Task 4: REST API `/api/v1/erasure-receipts`

**Files:**
- Create: `app/api/v1/erasure.py`
- Modify: `app/api/v1/router.py` (import `erasure` + `include_router`)
- Modify: `tests/api/test_router_wiring.py` (append `"app.api.v1.erasure"` to `ROUTERS_TO_CHECK`)
- Modify: `app/schemas/Orivory.py` (append after `AccessLogListResponse`)
- Test: `tests/api/test_erasure_router.py` (wiring-level, no live DB)

**Interfaces:**
- Consumes: `erase_memories`, `list_receipts` (Task 2); `ErasureReceipt` (Task 1); the `access-log` endpoint style in `app/api/v1/agents.py:114-134`.
- Produces REST API:
  - `POST /api/v1/erasure-receipts` body `{"memory_ids": [UUID, ...]}` → `201` receipt item (`memory_ids` min 1, max 100; `requested_by="rest_api"`; always scoped to `current_user.id`).
  - `GET /api/v1/erasure-receipts?limit=&offset=` → `{"items": [...], "total": int}` newest first (limit default 50, ge=1 le=200).
  - `GET /api/v1/erasure-receipts/{receipt_id}` → receipt item; 404 when missing or foreign (no existence leak).
- Produces schemas: `ErasureReceiptCreate(memory_ids: list[UUID])`, `ErasureReceiptItem(id, user_id, requested_memory_ids: list[UUID], status, detail, created_at)`, `ErasureReceiptListResponse(items, total)`.

- [ ] **Step 1: Write the failing test** — `tests/api/test_erasure_router.py`:

```python
"""Wiring tests for the erasure-receipts router — CI-safe, no live DB."""
from __future__ import annotations

import uuid

import pytest
from fastapi.routing import APIRoute
from pydantic import ValidationError

from app.api.v1.erasure import router
from app.schemas.Orivory import ErasureReceiptCreate, ErasureReceiptItem


def test_erasure_routes_registered():
    paths = {route.path for route in router.routes if isinstance(route, APIRoute)}
    assert "/erasure-receipts" in paths
    assert "/erasure-receipts/{receipt_id}" in paths


def test_erasure_create_rejects_empty_list():
    with pytest.raises(ValidationError):
        ErasureReceiptCreate(memory_ids=[])


def test_erasure_create_rejects_oversized_batch():
    with pytest.raises(ValidationError):
        ErasureReceiptCreate(memory_ids=[uuid.uuid4() for _ in range(101)])


def test_receipt_item_schema_fields():
    assert set(ErasureReceiptItem.model_fields) == {
        "id", "user_id", "requested_memory_ids", "status", "detail", "created_at",
    }
```

- [ ] **Step 2: Run to verify it fails** — `pytest tests/api/test_erasure_router.py -v` → FAIL (ImportError: `app.api.v1.erasure`). (`list_receipts` itself is covered by the Task 2 tests.)
- [ ] **Step 3: Add schemas** — append to `app/schemas/Orivory.py`:

```python
# ─── Erasure receipts (Open Memory Hub MVP 5) ───────────────────────────────


class ErasureReceiptCreate(BaseModel):
    """Request body for ``POST /api/v1/erasure-receipts`` — erase + verify."""
    memory_ids: list[UUID] = Field(min_length=1, max_length=100)


class ErasureReceiptItem(BaseModel):
    """One erasure receipt: what was requested and what verification found."""
    id:                   UUID
    user_id:              UUID
    requested_memory_ids: list[UUID]
    status:               str
    detail:               dict
    created_at:           datetime

    model_config = ConfigDict(from_attributes=True)


class ErasureReceiptListResponse(BaseModel):
    items: list[ErasureReceiptItem]
    total: int
```

(`UUID`, `datetime`, `Field`, `ConfigDict`, `BaseModel` are already imported in that file.)

- [ ] **Step 4: Implement the router** — `app/api/v1/erasure.py`:

```python
"""
Erasure receipts API — verifiable memory erasure (Open Memory Hub MVP 5).

Endpoints:
    POST /api/v1/erasure-receipts          erase memories owned by the caller
    GET  /api/v1/erasure-receipts          list receipts, newest first, user-scoped
    GET  /api/v1/erasure-receipts/{id}     fetch one receipt

Foreign/unknown memory ids are recorded in the receipt as
``not_found_or_foreign`` — never deleted, no existence leak. Receipts quote
personal memory ids, so they cascade away with the user.
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.erasure_receipt import ErasureReceipt
from app.models.user import User
from app.schemas.Orivory import (
    ErasureReceiptCreate,
    ErasureReceiptItem,
    ErasureReceiptListResponse,
)
from app.services.erasure_service import erase_memories, list_receipts
from app.utils.dependencies import get_current_verified_user

router = APIRouter(prefix="/erasure-receipts", tags=["erasure"])


@router.post("", response_model=ErasureReceiptItem, status_code=status.HTTP_201_CREATED)
async def create_erasure_receipt(
    body: ErasureReceiptCreate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ErasureReceiptItem:
    """Erase the given memories (caller-owned only) and return the receipt."""
    receipt = await erase_memories(db, current_user.id, body.memory_ids, requested_by="rest_api")
    return ErasureReceiptItem.model_validate(receipt)


@router.get("", response_model=ErasureReceiptListResponse)
async def list_erasure_receipts(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ErasureReceiptListResponse:
    """Erasure receipts for the current user, newest first."""
    rows, total = await list_receipts(db, current_user.id, limit=limit, offset=offset)
    return ErasureReceiptListResponse(
        items=[ErasureReceiptItem.model_validate(row) for row in rows],
        total=total,
    )


@router.get("/{receipt_id}", response_model=ErasureReceiptItem)
async def get_erasure_receipt(
    receipt_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ErasureReceiptItem:
    """Fetch one receipt. Foreign or unknown ids read as 404 (no existence leak)."""
    receipt = await db.get(ErasureReceipt, receipt_id)
    if not receipt or receipt.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Erasure receipt not found.")
    return ErasureReceiptItem.model_validate(receipt)
```

- [ ] **Step 5: Wire the router** — in `app/api/v1/router.py` add `erasure` to the `from app.api.v1 import (...)` list (alphabetical, after `entities`) and `api_router.include_router(erasure.router)` next to `api_router.include_router(agents.router)`; in `tests/api/test_router_wiring.py` append `"app.api.v1.erasure"` to `ROUTERS_TO_CHECK`.
- [ ] **Step 6: Run to verify it passes** — `pytest tests/api/test_erasure_router.py tests/api/test_router_wiring.py -v` → PASS.
- [ ] **Step 7: Lint + commit** — `ruff check app/api/v1/erasure.py app/api/v1/router.py app/schemas/Orivory.py tests/api/test_erasure_router.py` → 0 errors; `pytest tests/api tests/services -q` → green; `git commit -m "feat: erasure receipts REST API"`.

---

### Task 5: Docs + one-pager status

**Files:**
- Modify: `docs/API.md` (new "14. Erasure Receipts" section + ToC entry 14)
- Modify: `README.md` (one paragraph in the "Open Memory Hub (MVP)" section)
- Modify: `docs/ideas/open-memory-hub.md` (check off MVP item 5)

- [ ] **Step 1: API.md** — add `14. [Erasure Receipts](#14-erasure-receipts)` to the Table of Contents after entry 13, and this section at the end of the file (before the closing `---` footer):

````markdown
## 14. Erasure Receipts

Erasing a memory removes the row **and every derived artifact** (child chunks, entity links, source links, ChromaDB vectors), then runs a post-deletion verification pass (re-query the vector store, re-count residual rows). Each erasure call returns one **receipt** with per-target results and a `completed` / `completed_with_residual` status. Receipts are user-scoped and are deleted with the user.

### POST /api/v1/erasure-receipts

Erase memories owned by the caller. Foreign or unknown ids are recorded as `"not_found_or_foreign"` — never deleted, no existence leak.

**Request:**

```bash
curl -s -X POST https://api.orivory.io/api/v1/erasure-receipts \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"memory_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"]}'
```

| Field        | Type   | Required | Description                                     |
|--------------|--------|----------|-------------------------------------------------|
| `memory_ids` | UUID[] | Yes      | 1–100 memory ids (duplicates are deduplicated)  |

**Response `201 Created`** (abridged — `detail.targets[]` carries one entry per requested id with the shape produced by Task 2):

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "requested_memory_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
  "status": "completed",
  "detail": {
    "targets": [
      {
        "memory_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "status": "deleted",
        "child_memory_ids": [],
        "entity_links": 2,
        "source_links": 1,
        "vectors_deleted": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
        "vector_residual": [],
        "vector_residual_checked": true,
        "db_residual": {"children": 0, "entity_links": 0, "source_links": 0}
      }
    ],
    "summary": {"requested": 1, "erased": 1, "skipped": 0, "residual_vectors": 0, "residual_rows": 0}
  }
}
```

`status` is `completed_with_residual` when verification found leftover vectors or DB rows; `vector_residual_checked: false` means Chroma was unreachable during verification (the DB delete still succeeded).

### GET /api/v1/erasure-receipts

List the current user's receipts, newest first. Query: `limit` (default 50, max 200), `offset`.

### GET /api/v1/erasure-receipts/{id}

Fetch one receipt. Unknown or other users' receipts return `404`.

### MCP

Agents with the `memory:write` scope can call the `forget_memory` MCP tool (endpoint `/mcp`) with `{"memory_ids": ["<uuid>", ...]}`; it returns the receipt summary and appends an `mcp_forget` row to the access ledger.
````

- [ ] **Step 2: README.md** — in the "Open Memory Hub (MVP)" section, add after the access-ledger paragraph:

```markdown
Erasure is verifiable: `POST /api/v1/erasure-receipts` (or the MCP `forget_memory` tool) cascades a deletion across rows, links and vectors, then re-checks every derived artifact and returns a receipt — `completed` or `completed_with_residual`.
```

- [ ] **Step 3: One-pager status** — in `docs/ideas/open-memory-hub.md`, change MVP item 5 from

```
5. **Erasure receipts v0** — cascade deletion + verification report (RAG-store deletion: literature xác nhận sạch hơn weight-level; adversarially verified).
```

to

```
5. ✅ **Erasure receipts v0** — cascade deletion + verification report (RAG-store deletion: literature xác nhận sạch hơn weight-level; adversarially verified). (backend done 2026-09-02; v0 verification = absence-checks, adversarial re-inference probing pending)
```

- [ ] **Step 4: Full verification** — `ruff check app/models/erasure_receipt.py app/services/erasure_service.py app/api/v1/erasure.py app/mcp_hub alembic/versions/e6f7a8b9c0d1_erasure_receipts.py tests/models/test_erasure_models.py tests/services/test_erasure_service.py tests/api/test_erasure_router.py tests/mcp_hub` → 0 errors; `pytest tests/models tests/services tests/api tests/mcp_hub -q` → green.
- [ ] **Step 5: Commit** — `git commit -m "docs: erasure receipts v0 (API, README, one-pager status)"`.

---

## Follow-ups (explicitly NOT in this plan)

- **Deeper adversarial verification** — v0 verifies by absence-checks (vectors + DB rows). Papers §3.3 shows facts can be re-inferred from correlated knowledge; add KG-correlation probing + LLM-judge protocol before claiming "adversarially verified" in marketing.
- **Knowledge-graph residual scrub** — `Entity`/`Relation` nodes are user-scoped and survive memory deletion; the receipt records link counts but v0 does not prune orphaned entities/relations (papers §3.2's multi-document de-anonymization risk). Own follow-up.
- **Erasure Receipts UI** page in `frontend/` (list receipts, show per-target detail).
- Ledger rows are intentionally **never** erased by an erasure call (append-only audit: the ledger records that a memory was accessed *before* deletion) — revisit only with a legal requirement.
- Retro-scrub job: replay receipts' `vector_residual`/`db_residual` findings against the reindex task, for erasures that happened while Chroma was down.
- Export/import paths (MVP item 3) and ClawHub skill (item 2) — own plans.
