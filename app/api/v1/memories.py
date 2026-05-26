"""
Memory API — second-brain personal memory storage.

Endpoints:
    POST   /api/v1/memories           create a memory (manual note, or from any source)
    GET    /api/v1/memories           list memories (filter by source_type, tag, query)
    GET    /api/v1/memories/{id}      fetch one memory with entity links
    PATCH  /api/v1/memories/{id}      update fields (title, summary, tags, salience, pinned)
    DELETE /api/v1/memories/{id}      remove a memory (cascades to entity + source links)

Note: This endpoint is for direct user/agent memory writes. The bulk
ingestion path (file upload, sync from a Source) lives in the
ingestion service and is wired up in Phase 2.
"""
from __future__ import annotations

from uuid import UUID
from datetime import datetime
from typing import Annotated, Literal

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.memory import Memory
from app.retrieval.memory.retriever import MemoryRetriever
from app.utils.dependencies import get_current_verified_user
from app.schemas.mindlayer import (
    MemoryCreate,
    MemoryUpdate,
    MemoryResponse,
    MemoryListResponse,
    RecallRequest,
    RecallResponse,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/memories", tags=["memories"])


# ── write-through sync helpers (added in commit 31) ────────────────────────


@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    body: MemoryCreate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MemoryResponse:
    """Create a new memory. The owning user is taken from the auth context."""
    memory = Memory(
        user_id=current_user.id,
        title=body.title,
        content=body.content,
        summary=body.summary,
        source_type=body.source_type,
        source_ref=body.source_ref,
        source_url=body.source_url,
        tags=body.tags,
        captured_at=body.captured_at or datetime.utcnow(),
        parent_id=body.parent_id,
        pinned=body.pinned,
        extra_metadata=body.metadata,
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return MemoryResponse.model_validate(memory)


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    source_type: Literal["manual_note", "file_upload", "google_drive", "notion",
                          "gmail", "web_clipper", "conversation_excerpt", "other"] | None = None,
    tag: str | None = Query(default=None, description="Filter by tag (exact match)"),
    query: str | None = Query(default=None, description="Substring search in title/content"),
    pinned: bool | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> MemoryListResponse:
    """List memories for the current user with optional filters."""
    base = select(Memory).where(Memory.user_id == current_user.id)
    count_base = select(func.count(Memory.id)).where(Memory.user_id == current_user.id)

    if source_type:
        base = base.where(Memory.source_type == source_type)
        count_base = count_base.where(Memory.source_type == source_type)
    if pinned is not None:
        base = base.where(Memory.pinned == pinned)
        count_base = count_base.where(Memory.pinned == pinned)
    if tag:
        # tags is a Postgres ARRAY; use the "contains" operator
        base = base.where(Memory.tags.contains([tag]))
        count_base = count_base.where(Memory.tags.contains([tag]))
    if query:
        # Case-insensitive substring match in title OR content
        pattern = f"%{query.lower()}%"
        title_match  = func.lower(Memory.title).like(pattern)
        content_match = func.lower(Memory.content).like(pattern)
        base = base.where(or_(title_match, content_match))
        count_base = count_base.where(or_(title_match, content_match))

    total = (await db.execute(count_base)).scalar_one()
    rows  = (await db.execute(
        base.order_by(Memory.captured_at.desc()).offset(offset).limit(limit)
    )).scalars().all()

    return MemoryListResponse(
        items=[MemoryResponse.model_validate(m) for m in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MemoryResponse:
    memory = await db.get(Memory, memory_id)
    if not memory or memory.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Memory not found.")
    return MemoryResponse.model_validate(memory)


@router.patch("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: UUID,
    body: MemoryUpdate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MemoryResponse:
    memory = await db.get(Memory, memory_id)
    if not memory or memory.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Memory not found.")

    data = body.model_dump(exclude_unset=True)
    # Pydantic alias `metadata` maps to ORM attribute `extra_metadata` (the
    # underlying column is named "metadata", reserved by SQLAlchemy).
    if "metadata" in data:
        data["extra_metadata"] = data.pop("metadata")
    for field, value in data.items():
        setattr(memory, field, value)

    await db.commit()
    await db.refresh(memory)
    return MemoryResponse.model_validate(memory)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    memory = await db.get(Memory, memory_id)
    if not memory or memory.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Memory not found.")
    await db.delete(memory)
    await db.commit()


# ── Phase 3.7: recall endpoint ──────────────────────────────────────────────


@router.post("/recall", response_model=RecallResponse)
async def recall_memory(
    body: RecallRequest,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecallResponse:
    """Personal-context recall: find memories matching the query.

    Pipeline (see :class:`MemoryRetriever` for details):

        1. Fetch personal context (pinned + recent).
        2. LLM rewrite the query + extract entities.
        3. Vector search in ChromaDB.
        4. Hydrate + apply entity boost + time decay.
        5. Return top_k with trace (rewritten query, entities, latency).

    Every step degrades gracefully: an empty ``results`` list plus a
    ``trace`` describing what was attempted is returned even if LLM,
    ChromaDB, or the DB read is partially down.
    """
    retriever = MemoryRetriever(
        db=db,
        user_id=current_user.id,
    )
    return await retriever.recall(
        query=body.query,
        top_k=body.top_k,
        include_personal_context=body.include_personal_context,
    )
