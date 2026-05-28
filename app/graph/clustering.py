"""Simple graph cluster detection for MindLayer.

Phase 4 intentionally avoids external graph dependencies. Clusters are connected
components over relation edges above a configurable weight threshold.
"""
from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import Entity, Relation
from app.schemas.mindlayer import GraphCluster, GraphClustersResponse, GraphEdge, GraphNode


async def detect_clusters(
    db: AsyncSession,
    user_id: UUID,
    *,
    min_weight: float = 0.2,
    limit: int = 20,
) -> GraphClustersResponse:
    """Return connected components for a user's knowledge graph."""
    entities = (await db.execute(
        select(Entity).where(Entity.user_id == user_id)
    )).scalars().all()
    if not entities:
        return GraphClustersResponse(clusters=[], generated_at=datetime.utcnow())

    entity_by_id = {entity.id: entity for entity in entities}
    relations = (await db.execute(
        select(Relation).where(
            Relation.user_id == user_id,
            Relation.weight >= min_weight,
        )
    )).scalars().all()

    adjacency: dict[UUID, set[UUID]] = defaultdict(set)
    edges_by_pair: dict[frozenset[UUID], list[Relation]] = defaultdict(list)
    for relation in relations:
        if relation.source_entity_id not in entity_by_id or relation.target_entity_id not in entity_by_id:
            continue
        adjacency[relation.source_entity_id].add(relation.target_entity_id)
        adjacency[relation.target_entity_id].add(relation.source_entity_id)
        edges_by_pair[frozenset({relation.source_entity_id, relation.target_entity_id})].append(relation)

    visited: set[UUID] = set()
    clusters: list[GraphCluster] = []

    for entity_id in entity_by_id:
        if entity_id in visited:
            continue
        component = _walk_component(entity_id, adjacency, visited)
        if not component:
            component = {entity_id}

        nodes = [entity_by_id[eid] for eid in component]
        component_edges: list[Relation] = []
        component_score = 0.0
        for pair, pair_edges in edges_by_pair.items():
            if pair.issubset(component):
                component_edges.extend(pair_edges)
                component_score += sum(edge.weight for edge in pair_edges)

        component_score += sum(entity.mention_count or 0 for entity in nodes) / 10.0
        clusters.append(
            GraphCluster(
                id=_cluster_id(nodes),
                nodes=[
                    GraphNode(id=entity.name, type=entity.entity_type, mentions=entity.mention_count)
                    for entity in sorted(nodes, key=lambda e: (e.mention_count or 0, e.name), reverse=True)
                ],
                edges=[
                    GraphEdge(
                        source=entity_by_id.get(edge.source_entity_id).name,
                        target=entity_by_id.get(edge.target_entity_id).name,
                        relation=edge.relation,
                        weight=edge.weight,
                    )
                    for edge in sorted(component_edges, key=lambda e: e.weight, reverse=True)
                ],
                score=round(component_score, 4),
            )
        )

    clusters.sort(key=lambda cluster: (cluster.score, len(cluster.nodes)), reverse=True)
    return GraphClustersResponse(clusters=clusters[:limit], generated_at=datetime.utcnow())


def _walk_component(start: UUID, adjacency: dict[UUID, set[UUID]], visited: set[UUID]) -> set[UUID]:
    component: set[UUID] = set()
    queue: deque[UUID] = deque([start])
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        component.add(current)
        for neighbor in adjacency.get(current, set()):
            if neighbor not in visited:
                queue.append(neighbor)
    return component


def _cluster_id(entities: list[Entity]) -> str:
    if not entities:
        return "cluster-empty"
    top = sorted(entities, key=lambda entity: (entity.mention_count or 0, entity.name), reverse=True)[0]
    return f"cluster-{str(top.id)[:8]}"
