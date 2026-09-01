"""Tests for SourceSyncService idempotency (app/ingestion/dispatcher.py).

Regression coverage for two classes of bug:
1. Lazy-loading MemorySource.memory on an AsyncSession raises MissingGreenlet
   (the lookup now eager-loads with selectinload).
2. Re-sync of previously-synced items must skip/update, not re-error.

These tests need the test database; they skip when it is unavailable
(consistent with the rest of the DB-backed suite).
"""
from uuid import uuid4

import pytest

from app.ingestion.dispatcher import SourceSyncService
from app.ingestion.types import ConnectorItem
from app.models.memory import Memory
from app.models.source import Source
from app.models.user import User


pytestmark = pytest.mark.asyncio


def _item(source_ref: str, content: str = "hello world") -> ConnectorItem:
    return ConnectorItem(
        title="Doc title",
        content=content,
        summary="summary",
        source_ref=source_ref,
        source_url="https://example.com/doc",
        tags=["test"],
    )


@pytest.fixture
async def user(db):
    u = User(email=f"sync-test-{uuid4()}@example.com", hashed_password=None)
    db.add(u)
    await db.flush()
    return u


@pytest.fixture
async def source(db, user):
    s = Source(
        user_id=user.id,
        source_type="manual",
        display_name=f"test-source-{uuid4()}",
        config={},
    )
    db.add(s)
    await db.flush()
    return s


async def test_resync_of_unchanged_item_skips(db, source):
    svc = SourceSyncService(db)
    item = _item("ref-1")

    outcome1, memory_id1 = await svc._persist_item(source, item)
    await db.flush()

    # Second persist of the same (source, ref) exercises the
    # MemorySource.memory relationship load — previously MissingGreenlet.
    outcome2, memory_id2 = await svc._persist_item(source, item)
    await db.flush()

    assert outcome1 == "added"
    assert outcome2 == "skipped"
    assert memory_id1 == memory_id2


async def test_resync_of_changed_item_updates(db, source):
    svc = SourceSyncService(db)
    await svc._persist_item(source, _item("ref-2", content="v1"))
    await db.flush()

    outcome, memory_id = await svc._persist_item(source, _item("ref-2", content="v2"))
    await db.flush()

    assert outcome == "updated"

    memory = await db.get(Memory, __import__("uuid").UUID(memory_id))
    assert memory.content == "v2"
