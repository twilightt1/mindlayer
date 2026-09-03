"""Access ledger read model — shared by the agents API and future receipts.

Every ledger read (list + count) goes through here so user scoping, newest-first
ordering, and pagination clamping cannot drift between callers. All queries are
always scoped to ``user_id``: client-supplied user ids are never trusted.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory_access_log import MemoryAccessLog

_MAX_LIMIT = 200


def _filters(
    user_id: uuid.UUID,
    agent_client_id: uuid.UUID | None,
) -> list[Any]:
    filters: list[Any] = [MemoryAccessLog.user_id == user_id]
    if agent_client_id is not None:
        filters.append(MemoryAccessLog.agent_client_id == agent_client_id)
    return filters


async def list_entries(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    agent_client_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[MemoryAccessLog], int]:
    """List a user's ledger entries newest first, together with the total count.

    ``limit`` is clamped into [1, 200] and a negative ``offset`` to 0 (clamped,
    never raised). The count query carries the same filters as the row query,
    so ``total`` is the unpaginated match count.
    """
    filters = _filters(user_id, agent_client_id)

    total = (await db.execute(
        select(func.count(MemoryAccessLog.id)).where(*filters)
    )).scalar_one()

    rows = (await db.execute(
        select(MemoryAccessLog)
        .where(*filters)
        .order_by(MemoryAccessLog.created_at.desc())
        .offset(max(offset, 0))
        .limit(max(1, min(limit, _MAX_LIMIT)))
    )).scalars().all()

    return list(rows), total


async def count_for_client(
    db: AsyncSession,
    user_id: uuid.UUID,
    agent_client_id: uuid.UUID,
) -> int:
    """Count ledger entries for one agent client, always scoped to the user."""
    return (await db.execute(
        select(func.count(MemoryAccessLog.id)).where(
            MemoryAccessLog.user_id == user_id,
            MemoryAccessLog.agent_client_id == agent_client_id,
        )
    )).scalar_one()


__all__ = ["count_for_client", "list_entries"]
