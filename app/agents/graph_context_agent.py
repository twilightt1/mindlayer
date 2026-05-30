"""Knowledge graph context node for the chat agent graph."""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState
from app.database import AsyncSessionLocal
from app.models.entity import Entity, MemoryEntity, Relation

log = logging.getLogger(__name__)

MAX_QUERY_ENTITIES = 12
MAX_GRAPH_RELATIONS = 24


async def graph_context_agent(state: AgentState) -> AgentState:
    """Fetch one-hop graph facts relevant to query and recalled memories."""
    state.setdefault("agent_trace", {})
    state["graph_context_chunks"] = []
    state["graph_context_trace"] = {}

    if not state.get("graph_context_enabled", True):
        state["agent_trace"]["graph_context"] = {"enabled": False, "chunks": 0}
        return state

    try:
        async with AsyncSessionLocal() as db:
            entities = await fetch_relevant_entities(db, UUID(state["user_id"]), state)
            relations = await fetch_one_hop_relations(db, UUID(state["user_id"]), entities)
            entities = await expand_entities_for_relations(db, UUID(state["user_id"]), entities, relations)

        chunk = build_graph_context_chunk(entities, relations)
        chunks = [chunk] if chunk else []
        state["graph_context_chunks"] = chunks
        state["graph_context_trace"] = {
            "entities": len(entities),
            "relations": len(relations),
            "chunks": len(chunks),
        }
        state["agent_trace"]["graph_context"] = {
            "enabled": True,
            **state["graph_context_trace"],
        }
    except Exception as exc:  # noqa: BLE001
        log.warning("Graph context failed", extra={"error": str(exc)})
        state["graph_context_chunks"] = []
        state["graph_context_trace"] = {"error": str(exc)}
        state["agent_trace"]["graph_context"] = {
            "enabled": True,
            "chunks": 0,
            "fallback_used": True,
            "error": str(exc),
        }
    return state


async def fetch_relevant_entities(db: AsyncSession, user_id: UUID, state: AgentState) -> list[Entity]:
    """Find entities from personal memories and query text."""
    by_id: dict[UUID, Entity] = {}

    memory_ids = _memory_ids_from_chunks(state.get("personal_memory_chunks", []))
    if memory_ids:
        linked = (await db.execute(
            select(Entity)
            .join(MemoryEntity, MemoryEntity.entity_id == Entity.id)
            .where(Entity.user_id == user_id, MemoryEntity.memory_id.in_(memory_ids))
            .order_by(Entity.mention_count.desc())
            .limit(MAX_QUERY_ENTITIES)
        )).scalars().all()
        for entity in linked:
            by_id[entity.id] = entity

    query_text = " ".join([
        state.get("query", ""),
        state.get("rewritten_query", ""),
        " ".join(state.get("search_variants", []) or []),
    ]).casefold()
    if query_text:
        candidates = (await db.execute(
            select(Entity)
            .where(Entity.user_id == user_id)
            .order_by(Entity.mention_count.desc())
            .limit(100)
        )).scalars().all()
        for entity in candidates:
            if _entity_matches_text(entity, query_text):
                by_id[entity.id] = entity
            if len(by_id) >= MAX_QUERY_ENTITIES:
                break

    return sorted(by_id.values(), key=lambda e: (e.mention_count or 0, e.name), reverse=True)[:MAX_QUERY_ENTITIES]


async def fetch_one_hop_relations(db: AsyncSession, user_id: UUID, entities: list[Entity]) -> list[Relation]:
    """Fetch relation edges adjacent to selected entities."""
    entity_ids = [entity.id for entity in entities]
    if not entity_ids:
        return []
    rows = (await db.execute(
        select(Relation)
        .where(
            Relation.user_id == user_id,
            or_(Relation.source_entity_id.in_(entity_ids), Relation.target_entity_id.in_(entity_ids)),
        )
        .order_by(Relation.weight.desc(), Relation.evidence_count.desc())
        .limit(MAX_GRAPH_RELATIONS)
    )).scalars().all()
    return list(rows)


async def expand_entities_for_relations(
    db: AsyncSession,
    user_id: UUID,
    entities: list[Entity],
    relations: list[Relation],
) -> list[Entity]:
    """Include relation endpoint entities so graph triples can be rendered."""
    by_id = {entity.id: entity for entity in entities}
    missing_ids = {
        entity_id
        for relation in relations
        for entity_id in (relation.source_entity_id, relation.target_entity_id)
        if entity_id not in by_id
    }
    if missing_ids:
        rows = (await db.execute(
            select(Entity).where(Entity.user_id == user_id, Entity.id.in_(missing_ids))
        )).scalars().all()
        for entity in rows:
            by_id[entity.id] = entity
    return list(by_id.values())


def build_graph_context_chunk(entities: list[Entity], relations: list[Relation]) -> dict[str, Any] | None:
    """Format entities and relations as one grounding context chunk."""
    if not entities and not relations:
        return None

    entity_by_id = {entity.id: entity for entity in entities}
    entity_names = [entity.name for entity in entities]
    lines: list[str] = ["Knowledge graph context"]

    if entities:
        lines.append("Entities:")
        for entity in entities:
            alias_text = f" aliases={', '.join(entity.aliases)}" if entity.aliases else ""
            lines.append(f"- {entity.name} ({entity.entity_type}, mentions={entity.mention_count or 0}){alias_text}")

    if relations:
        lines.append("Relations:")
        for relation in relations:
            source = entity_by_id.get(relation.source_entity_id)
            target = entity_by_id.get(relation.target_entity_id)
            if source is None or target is None:
                continue
            lines.append(
                "- "
                f"{source.name} --{relation.relation}--> {target.name} "
                f"(weight={relation.weight:.2f}, evidence={relation.evidence_count})"
            )

    content = "\n".join(lines).strip()
    if content == "Knowledge graph context":
        return None

    score = max([relation.weight for relation in relations], default=0.25)
    return {
        "id": "graph:context",
        "content": content,
        "rerank_score": score,
        "score": score,
        "rank": 999,
        "match_reasons": ["knowledge_graph"],
        "metadata": {
            "filename": "Knowledge graph",
            "source_type": "knowledge_graph",
            "entity_names": entity_names,
            "relation_count": len(relations),
        },
    }


def _memory_ids_from_chunks(chunks: list[dict[str, Any]]) -> list[UUID]:
    memory_ids: list[UUID] = []
    for chunk in chunks:
        raw = (chunk.get("metadata") or {}).get("memory_id")
        if not raw:
            continue
        try:
            memory_ids.append(UUID(str(raw)))
        except ValueError:
            continue
    return memory_ids


def _entity_matches_text(entity: Entity, query_text: str) -> bool:
    if entity.name and entity.name.casefold() in query_text:
        return True
    for alias in entity.aliases or []:
        if alias and alias.casefold() in query_text:
            return True
    return False
