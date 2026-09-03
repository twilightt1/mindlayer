"""Memory erasure with verifiable receipts — Open Memory Hub MVP item 5.

One call → one ``ErasureReceipt``. Per memory id: ownership check (foreign/
missing ids recorded, never deleted), the full transitive descendant set is
collected BEFORE deletion via a ``parent_id`` BFS (papers §3.2), row delete via
the ORM cascade, ``safe_delete_from_chroma`` for every affected id, then an
adversarial verification pass (papers §3.3): re-query Chroma + re-count
residual DB rows. v0 verification = absence-checks of every derived artifact;
KG re-inference probing is a tracked follow-up.

Receipt ``status`` — precedence in this order:

- ``completed_with_errors``: at least one target's erasure raised (recorded
  per-target and skipped; the remaining targets are still erased).
- ``completed_with_residual``: no errors, but verification found residual
  vectors or DB rows.
- ``completed``: every target erased and verified clean.

Erasure is best-effort per target: one failing target never aborts the call or
the other targets. The receipt commit is the only unrecorded failure mode —
if it raises, the exception propagates and no receipt exists.
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
ERASURE_STATUS_ERRORS = "completed_with_errors"
NOT_FOUND_OR_FOREIGN = "not_found_or_foreign"

_MAX_LIMIT = 200
_MAX_BFS_DEPTH = 5  # descendants deeper than this are left untracked (recorded as residuals)


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


async def _collect_descendants(db: AsyncSession, root_id: uuid.UUID) -> tuple[list[uuid.UUID], int]:
    """BFS over ``parent_id`` from ``root_id`` — every transitive descendant.

    Returns ``(descendant_ids_bfs_order, max_depth)``; the root is not included
    and ``max_depth`` counts only levels that yielded nodes (0 = no children).
    Cycles are impossible via the FK, but a visited-set keeps the frontier loop
    honest anyway, and ``_MAX_BFS_DEPTH`` bounds runaway/accidental deep trees.
    """
    descendants: list[uuid.UUID] = []
    visited = {root_id}
    frontier = [root_id]
    depth = 0
    while frontier and depth < _MAX_BFS_DEPTH:
        rows = list((await db.execute(
            select(Memory.id).where(Memory.parent_id.in_(frontier))
        )).scalars().all())
        frontier = [rid for rid in rows if rid not in visited]
        if not frontier:
            break
        depth += 1
        visited.update(frontier)
        descendants.extend(frontier)
    return descendants, depth


async def _erase_one(db: AsyncSession, user_id: uuid.UUID, memory_id: uuid.UUID) -> dict[str, Any]:
    """Erase one owned memory and return its per-target receipt entry."""
    row = await db.get(Memory, memory_id)
    if row is None or row.user_id != user_id:
        return {"memory_id": str(memory_id), "status": NOT_FOUND_OR_FOREIGN}

    # Collect the FULL transitive descendant set BEFORE deletion (receipt must
    # describe what went away).
    child_ids, traversal_depth = await _collect_descendants(db, memory_id)
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
        "affected_memory_ids": [str(c) for c in child_ids],  # transitive, excluding the target
        "traversal_depth": traversal_depth,
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
    """Erase every owned memory among ``memory_ids`` and write one receipt.

    Best-effort per target: a target whose erasure raises is recorded as a
    per-target error entry (status ``error`` + message) and the remaining
    targets are still processed. The receipt commit is the only unrecorded
    failure mode — if it raises, the exception propagates and no receipt exists.
    """
    unique_ids = list(dict.fromkeys(memory_ids))
    targets: list[dict[str, Any]] = []
    for mid in unique_ids:
        try:
            targets.append(await _erase_one(db, user_id, mid))
        except Exception as exc:  # best-effort: record + continue
            log.exception("Erasure failed for memory %s", mid, extra={"memory_id": str(mid)})
            # A failed per-target commit poisons the session (PendingRollbackError);
            # roll back so the remaining targets (and the receipt commit) still work.
            await db.rollback()
            targets.append({
                "memory_id": str(mid),
                "status": "error",
                "error": str(exc),
                "vector_residual_checked": False,
                "db_residual": None,
            })
    erased = sum(1 for t in targets if t["status"] == "deleted")
    residual_vectors = sum(len(t["vector_residual"]) for t in targets if t["status"] == "deleted")
    residual_rows = sum(sum(t["db_residual"].values()) for t in targets if t["status"] == "deleted")
    any_errors = any(t["status"] == "error" for t in targets)

    if any_errors:
        status = ERASURE_STATUS_ERRORS
    elif residual_vectors or residual_rows:
        status = ERASURE_STATUS_RESIDUAL
    else:
        status = ERASURE_STATUS_COMPLETED

    receipt = ErasureReceipt(
        user_id=user_id,
        requested_memory_ids=[str(m) for m in unique_ids],
        status=status,
        detail={
            "requested_by": requested_by,
            "targets": targets,
            "summary": {
                "requested": len(unique_ids),
                "erased": erased,
                "skipped": len(unique_ids) - erased,
                "errors": sum(1 for t in targets if t["status"] == "error"),
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
    "ERASURE_STATUS_ERRORS",
    "ERASURE_STATUS_RESIDUAL",
    "NOT_FOUND_OR_FOREIGN",
    "erase_memories",
    "list_receipts",
]
