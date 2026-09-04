"""Wiring tests for the memories router create endpoint — CI-safe, no live DB.

`create_memory` is called directly: its parent-ownership validation raises
404 before any persistence or vector indexing, so no app/auth/db fixtures
are needed. Mirrors the routers' not-found style (agents router).
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.memories import create_memory
from app.schemas.Orivory import MemoryCreate


class _FakeDB:
    """Only `get` is reachable on the validation-404 path."""

    def __init__(self, parent):
        self._parent = parent

    async def get(self, model, pk):
        return self._parent


def _body(parent_id: uuid.UUID) -> MemoryCreate:
    return MemoryCreate(title="t", content="c", parent_id=parent_id)


async def test_create_memory_rejects_missing_parent():
    db = _FakeDB(parent=None)  # parent_id points at nothing

    with pytest.raises(HTTPException) as exc_info:
        await create_memory(_body(uuid.uuid4()), SimpleNamespace(id=uuid.uuid4()), db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Parent memory not found"


async def test_create_memory_rejects_foreign_parent():
    parent = SimpleNamespace(id=uuid.uuid4(), user_id=uuid.uuid4())
    db = _FakeDB(parent=parent)  # parent exists but belongs to another user

    with pytest.raises(HTTPException) as exc_info:
        await create_memory(_body(parent.id), SimpleNamespace(id=uuid.uuid4()), db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Parent memory not found"
