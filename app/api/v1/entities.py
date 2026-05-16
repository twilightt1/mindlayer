"""
Entity / Graph API — second-brain knowledge graph.

Endpoints:
    GET    /api/v1/entities                              list entities (filter by type, name)
    GET    /api/v1/entities/{id}                         fetch one entity with its relations
    GET    /api/v1/entities/{id}/memories                all memories tagged with this entity
    GET    /api/v1/graph/snapshot                        full graph for the current user
    GET    /api/v1/graph/timeline                        recent activity on the graph
    GET    /api/v1/graph/related/{entity_name}           related entities (1-hop neighbors)

In Phase 4, writes (POST/PATCH on entities, relations) will be added
when the extraction pipeline is live. For now the graph is read-only
to keep the surface area small.
"""
from __future__ import annotations

from uuid import UUID
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.memory import Memory
from app.models.entity import Entity, Relation, MemoryEntity
from app.utils.dependencies import get_current_verified_user
from app.schemas.mindlayer import (
    EntityResponse,
    EntityListResponse,
    RelationResponse,
    GraphSnapshot,
    GraphNode,
    GraphEdge,
    MemoryResponse,
)

router = APIRouter(prefix="/entities", tags=["entities"])


# ─── /entities ──────────────────────────────────────────────────────────────

@router.get("", response_model=EntityListResponse)
async def list_entities(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    entity_type: str | None = None,
    name: str | None = Query(default=None, description="Substring match on name (case-insensitive)"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> EntityListResponse:
    base = select(Entity).where(Entity.user_id == current_user.id)
    count_base = select(func.count(Entity.id)).where(Entity.user_id == current_user.id)

    if entity_type:
        base = base.where(Entity.entity_type == entity_type)
        count_base = count_base.where(Entity.entity_type == entity_type)
    if name:
        pattern = f"%{name.lower()}%"
        base = base.where(func.lower(Entity.name).like(pattern))
        count_base = count_base.where(func.lower(Entity.name).like(pattern))

    total = (await db.execute(count_base)).scalar_one()
    rows = (await db.execute(
        base.order_by(Entity.mention_count.desc(), Entity.last_seen_at.desc())
            .offset(offset).limit(limit)
    )).scalars().all()

    return EntityListResponse(
        items=[EntityResponse.model_validate(e) for e in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EntityResponse:
    entity = await db.get(Entity, entity_id)
    if not entity or entity.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Entity not found.")
    return EntityResponse.model_validate(entity)


@router.get("/{entity_id}/memories", response_model=list[MemoryResponse])
async def list_memories_for_entity(
    entity_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[MemoryResponse]:
    """Return all memories that link to this entity, newest first."""
    entity = await db.get(Entity, entity_id)
    if not entity or entity.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Entity not found.")

    rows = (await db.execute(
        select(Memory)
        .join(MemoryEntity, MemoryEntity.memory_id == Memory.id)
        .where(MemoryEntity.entity_id == entity_id, Memory.user_id == current_user.id)
        .order_by(Memory.captured_at.desc())
        .limit(limit)
    )).scalars().all()
    return [MemoryResponse.model_validate(m) for m in rows]


# ─── /graph ─────────────────────────────────────────────────────────────────

graph_router = APIRouter(prefix="/graph", tags=["graph"])


@graph_router.get("/snapshot", response_model=GraphSnapshot)
async def graph_snapshot(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    min_weight: float = Query(default=0.0, ge=0.0, le=1.0),
    limit: int = Query(default=200, ge=1, le=1000),
) -> GraphSnapshot:
    """Return a snapshot of the knowledge graph (nodes + edges) for visualization."""
    entity_rows = (await db.execute(
        select(Entity)
        .where(Entity.user_id == current_user.id)
        .order_by(Entity.mention_count.desc())
        .limit(limit)
    )).scalars().all()
    entity_ids = {e.id for e in entity_rows}

    relation_rows = (await db.execute(
        select(Relation)
        .where(
            Relation.user_id == current_user.id,
            Relation.weight >= min_weight,
            Relation.source_entity_id.in_(entity_ids),
            Relation.target_entity_id.in_(entity_ids),
        )
        .order_by(Relation.weight.desc())
        .limit(limit * 2)
    )).scalars().all()

    # Build id -> name map for edge endpoints
    name_of = {e.id: e.name for e in entity_rows}

    return GraphSnapshot(
        nodes=[
            GraphNode(id=e.name, type=e.entity_type, mentions=e.mention_count)
            for e in entity_rows
        ],
        edges=[
            GraphEdge(
                source=name_of.get(r.source_entity_id, str(r.source_entity_id)),
                target=name_of.get(r.target_entity_id, str(r.target_entity_id)),
                relation=r.relation,
                weight=r.weight,
            )
            for r in relation_rows
        ],
        generated_at=datetime.utcnow(),
    )


@graph_router.get("/related/{entity_name}", response_model=list[EntityResponse])
async def related_entities(
    entity_name: str,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[EntityResponse]:
    """Return entities directly related to the given entity name (1-hop neighbors)."""
    # Find source entity
    src = (await db.execute(
        select(Entity)
        .where(Entity.user_id == current_user.id, func.lower(Entity.name) == entity_name.lower())
    )).scalar_one_or_none()
    if not src:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Entity '{entity_name}' not found.")

    # Find both outgoing and incoming
    related_ids = (await db.execute(
        select(distinct(Relation.target_entity_id))
        .where(Relation.user_id == current_user.id, Relation.source_entity_id == src.id)
    )).scalars().all()
    incoming_ids = (await db.execute(
        select(distinct(Relation.source_entity_id))
        .where(Relation.user_id == current_user.id, Relation.target_entity_id == src.id)
    )).scalars().all()
    all_ids = set(related_ids) | set(incoming_ids)
    if not all_ids:
        return []

    rows = (await db.execute(
        select(Entity)
        .where(Entity.user_id == current_user.id, Entity.id.in_(all_ids))
        .order_by(Entity.mention_count.desc())
        .limit(limit)
    )).scalars().all()
    return [EntityResponse.model_validate(e) for e in rows]
