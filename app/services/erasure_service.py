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
