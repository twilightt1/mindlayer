"""MCP memory tools — the hub's public surface to agents.

Design rules:
  - Every tool resolves its own AgentPrincipal (via the ``_current_principal``
    seam — in production the FastMCP wrappers in ``server.py`` publish the
    principal resolved from the MCP Context's HTTP request headers) and
    enforces scopes; failures return ``{"error": ...}`` dicts, never raise.
  - Every authorized call appends a ``MemoryAccessLog`` row — the ledger is the
    product. Identity/scope denials return *before* any DB write.
  - Reads bump nothing (salience bumping stays in the chat pipeline); writes
    reuse ``index_new_memory`` so embedding + graph stay best-effort.
"""
from __future__ import annotations

import logging
from contextvars import ContextVar
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.mcp_hub.identity import (
    ACTION_ADD,
    ACTION_DELETE,
    ACTION_FORGET,
    ACTION_GET,
    ACTION_LIST,
    ACTION_SEARCH,
    AgentPrincipal,
)
from app.models.memory import Memory
from app.models.memory_access_log import MemoryAccessLog
from app.retrieval.memory.write_back import index_new_memory, safe_delete_from_chroma
from app.services.erasure_service import erase_memories

log = logging.getLogger(__name__)

MAX_SEARCH_LIMIT = 20
MAX_LIST_LIMIT = 100

IDENTITY_ERROR = {"error": "agent identity required"}
READ_SCOPE_ERROR = {"error": "scope memory:read required"}
WRITE_SCOPE_ERROR = {"error": "scope memory:write required"}

# Set by the FastMCP wrappers in server.py for the duration of one tool call;
# ``_current_principal`` reads it so the tool bodies stay framework-free
# (and tests can monkeypatch the function outright).
_principal_var: ContextVar[AgentPrincipal | None] = ContextVar("mcp_hub_principal", default=None)


def _current_principal() -> AgentPrincipal | None:
    """Principal for the active MCP call; ``None`` outside an MCP request."""
    return _principal_var.get()


def _session():
    """DB session seam — production wraps ``AsyncSessionLocal`` (async CM)."""
    return AsyncSessionLocal()


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _memory_brief(memory: Memory) -> dict[str, Any]:
    return {
        "id": str(memory.id),
        "title": memory.title,
        "content": memory.content,
        "tags": list(memory.tags or []),
        "salience": memory.salience,
        "captured_at": _iso(memory.captured_at),
    }


def _ledger_entry(
    principal: AgentPrincipal,
    action: str,
    *,
    memory_id: UUID | None = None,
    detail: dict[str, Any] | None = None,
) -> MemoryAccessLog:
    """Build one append-only ledger row (never logged back to the caller)."""
    return MemoryAccessLog(
        user_id=principal.user_id,
        agent_client_id=principal.agent_client_id,
        action=action,
        memory_id=memory_id,
        detail=detail if detail is not None else {},
    )


async def _recall_memory_ids(query: str, limit: int) -> list[tuple[UUID, float]]:
    """Recall seam used by ``search_memory``.

    MVP ranking is a plain SQL select — the user's memories ordered by
    salience desc, then captured_at desc (``query`` is kept for seam
    compatibility; semantic recall replaces this body later without touching
    the tool bodies). Tests monkeypatch this and return
    ``[(memory_id, score), ...]`` pairs.
    """
    principal = _current_principal()
    if principal is None:
        return []
    async with _session() as db:
        rows = (
            await db.execute(
                select(Memory.id, Memory.salience)
                .where(Memory.user_id == principal.user_id)
                .order_by(Memory.salience.desc(), Memory.captured_at.desc())
                .limit(limit)
            )
        ).all()
    return [(row.id, float(row.salience)) for row in rows]


async def search_memory(query: str, limit: int = 8) -> dict[str, Any]:
    """Search the caller's memories (requires the ``memory:read`` scope)."""
    principal = _current_principal()
    if principal is None:
        return IDENTITY_ERROR
    if not principal.can_read():
        return READ_SCOPE_ERROR
    capped = max(1, min(limit, MAX_SEARCH_LIMIT))
    async with _session() as db:
        recalled = await _recall_memory_ids(query, capped)
        results: list[dict[str, Any]] = []
        if recalled:
            # Hydrate the ranked ids; re-check ownership in the same query so
            # the recall seam can never widen access beyond the principal.
            rows = (
                await db.execute(
                    select(Memory).where(
                        Memory.id.in_([mid for mid, _ in recalled]),
                        Memory.user_id == principal.user_id,
                    )
                )
            ).scalars().all()
            by_id = {row.id: row for row in rows}
            results = [_memory_brief(by_id[mid]) for mid, _ in recalled if mid in by_id]
        db.add(
            _ledger_entry(
                principal,
                ACTION_SEARCH,
                detail={
                    "query": query,
                    "returned": len(results),
                    "memory_ids": [entry["id"] for entry in results],
                },
            )
        )
        await db.commit()
    return {"query": query, "results": results}


async def get_memory(memory_id: str) -> dict[str, Any]:
    """Fetch one memory owned by the caller (requires ``memory:read``)."""
    principal = _current_principal()
    if principal is None:
        return IDENTITY_ERROR
    if not principal.can_read():
        return READ_SCOPE_ERROR
    try:
        mid = UUID(memory_id)
    except ValueError:
        return {"error": "invalid memory id"}
    async with _session() as db:
        # Ownership is enforced in the query: a foreign id reads as "not found"
        # instead of leaking another user's memory.
        row = (
            await db.execute(
                select(Memory).where(Memory.id == mid, Memory.user_id == principal.user_id)
            )
        ).scalars().first()
        db.add(_ledger_entry(principal, ACTION_GET, memory_id=mid, detail={"found": row is not None}))
        await db.commit()
    if row is None:
        return {"error": "memory not found"}
    return _memory_brief(row)


async def list_recent(limit: int = 20) -> dict[str, Any]:
    """List the caller's most recent memories (requires ``memory:read``)."""
    principal = _current_principal()
    if principal is None:
        return IDENTITY_ERROR
    if not principal.can_read():
        return READ_SCOPE_ERROR
    capped = max(1, min(limit, MAX_LIST_LIMIT))
    async with _session() as db:
        rows = (
            await db.execute(
                select(Memory)
                .where(Memory.user_id == principal.user_id)
                .order_by(Memory.captured_at.desc(), Memory.id.desc())
                .limit(capped)
            )
        ).scalars().all()
        results = [_memory_brief(row) for row in rows]
        db.add(
            _ledger_entry(
                principal,
                ACTION_LIST,
                detail={"returned": len(results), "memory_ids": [entry["id"] for entry in results]},
            )
        )
        await db.commit()
    return {"results": results}


async def add_memory(title: str, content: str, tags: list[str] | None = None) -> dict[str, Any]:
    """Store a new memory owned by the caller (requires ``memory:write``)."""
    principal = _current_principal()
    if principal is None:
        return IDENTITY_ERROR
    if not principal.can_write():
        return WRITE_SCOPE_ERROR
    memory = Memory(
        id=uuid4(),  # client-side id so the ledger + indexing can reference it
        user_id=principal.user_id,
        title=title,
        content=content,
        tags=list(tags or []),
        source_type="mcp_agent",
        source_ref=f"agent:{principal.name}",
    )
    async with _session() as db:
        db.add(memory)
        await db.commit()
    try:
        await index_new_memory(memory)  # best-effort: embed + graph enqueue
    except Exception as exc:
        log.warning("MCP add_memory indexing failed for %s: %s", memory.id, exc)
    async with _session() as db:
        db.add(
            _ledger_entry(
                principal,
                ACTION_ADD,
                memory_id=memory.id,
                detail={"title": title, "memory_id": str(memory.id)},
            )
        )
        await db.commit()
    return _memory_brief(memory)


async def delete_memory(memory_id: str) -> dict[str, Any]:
    """Delete one memory owned by the caller (requires ``memory:write``)."""
    principal = _current_principal()
    if principal is None:
        return IDENTITY_ERROR
    if not principal.can_write():
        return WRITE_SCOPE_ERROR
    try:
        mid = UUID(memory_id)
    except ValueError:
        return {"error": "invalid memory id"}
    async with _session() as db:
        row = (
            await db.execute(
                select(Memory).where(Memory.id == mid, Memory.user_id == principal.user_id)
            )
        ).scalars().first()
        if row is None:
            db.add(_ledger_entry(principal, ACTION_DELETE, memory_id=mid, detail={"deleted": False}))
            await db.commit()
            return {"error": "memory not found"}
        await db.delete(row)
        await safe_delete_from_chroma(mid)  # best-effort vector cleanup
        db.add(_ledger_entry(principal, ACTION_DELETE, memory_id=mid, detail={"deleted": True}))
        await db.commit()
    return {"deleted": True, "id": str(mid)}


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


__all__ = [
    "add_memory",
    "delete_memory",
    "forget_memory",
    "get_memory",
    "list_recent",
    "search_memory",
]
