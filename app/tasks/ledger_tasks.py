"""Ledger retention task — keeps memory_access_logs bounded.

The access ledger is append-only by design, so without pruning it grows
without bound under chatty agents. This beat task deletes rows older than
``LEDGER_RETENTION_DAYS`` (default 90, config-settable).
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog

from app.config import settings
from app.tasks.celery_app import celery_app

log = structlog.get_logger()


@celery_app.task(name="tasks.prune_access_ledger")
def prune_access_ledger() -> dict[str, object]:
    """Delete access-ledger rows older than LEDGER_RETENTION_DAYS.

    Returns a small summary for the beat log. The ledger records *access*,
    not content — pruning old rows does not affect the erasure-receipt
    audit story, whose authoritative artifacts are the receipts themselves.
    """
    from sqlalchemy import delete

    from app.database import AsyncSessionLocal
    from app.models.memory_access_log import MemoryAccessLog

    days = settings.LEDGER_RETENTION_DAYS
    cutoff = datetime.now(UTC) - timedelta(days=days)

    async def _run() -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                delete(MemoryAccessLog).where(
                    MemoryAccessLog.created_at < cutoff
                )
            )
            await session.commit()
            return result.rowcount or 0

    import asyncio

    removed = asyncio.run(_run())
    summary = {"removed": removed, "cutoff": cutoff.isoformat(), "retention_days": days}
    log.info("access ledger pruned", **summary)
    return summary
