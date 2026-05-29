"""Phase 4 smoke tests — knowledge graph extraction.

Self-contained, dependency-light checks for:
- entity/relation extraction parsing + fallback
- graph builder pure helpers
- schema/route surfaces
- cluster helpers

Run:
    python scripts/_test_phase4_smoke.py
"""
from __future__ import annotations

import asyncio
import py_compile
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

sys.path.insert(0, r"d:\DL\rag-backend\rag-backend")

from app.graph import extraction
from app.graph.builder import (
    GRAPH_EXTRACTED_AT_KEY,
    GraphBuildResult,
    _already_processed,
    _entity_key,
    _entity_lookup,
    _mark_processed,
    _merge_aliases,
    _merge_relation_metadata,
    _touch_entity,
)
from app.graph.clustering import _cluster_id, _walk_component
from app.graph.extraction import (
    ExtractedEntity,
    ExtractedRelation,
    extract_entities,
    extract_relations,
    normalize_entity_name,
    normalize_entity_type,
    normalize_relation_type,
)
from app.schemas.mindlayer import (
    EntityCreate,
    EntityUpdate,
    GraphCluster,
    GraphClustersResponse,
    GraphEdge,
    GraphNode,
    RelationCreate,
    RelationUpdate,
)

PASS = 0
TOTAL = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, TOTAL
    TOTAL += 1
    if condition:
        PASS += 1
        suffix = f" -- {detail}" if detail else ""
        print(f"  [PASS] {name}{suffix}")
    else:
        suffix = f" -- {detail}" if detail else ""
        print(f"  [FAIL] {name}{suffix}")
        raise AssertionError(name)


class FakeCompletions:
    def __init__(self, content: str) -> None:
        self.content = content

    async def create(self, **kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


class FakeClient:
    def __init__(self, content: str) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions(content))


def memory(**overrides):
    data = {
        "id": uuid4(),
        "user_id": uuid4(),
        "title": "Project Atlas meeting",
        "summary": "Mom discussed Project Atlas on 2026-05-12.",
        "content": "Mom said Project Atlas depends on OpenAI and the Vietnam launch plan.",
        "tags": ["Project Atlas", "OpenAI"],
        "captured_at": datetime.now(UTC),
        "extra_metadata": {},
    }
    data.update(overrides)
    return SimpleNamespace(**data)


async def run_extraction_tests() -> None:
    print("\n=== 1. extraction ===")
    check("entity type normalization", normalize_entity_type("Project") == "project")
    check("unknown entity type -> other", normalize_entity_type("weird") == "other")
    check("relation type normalization", normalize_relation_type("References") == "references")
    check("unknown relation type -> related_to", normalize_relation_type("likes") == "related_to")
    check("entity name normalization", normalize_entity_name("  Project   Atlas  ") == "Project Atlas")

    original_get_client = extraction._get_client
    try:
        extraction._get_client = lambda: FakeClient(
            '{"entities":[{"name":"Project Atlas","type":"project","aliases":["Atlas"],"salience":1.7},'
            '{"name":"Mom","type":"person","salience":0.8}],"relations":[]}'
        )
        result = await extract_entities(memory())
        check("valid entity JSON -> two entities", len(result.entities) == 2)
        check("entity salience clamped", result.entities[0].salience <= 1.0)
        check("entity fallback false", result.fallback_used is False)

        extraction._get_client = lambda: FakeClient("not json")
        fallback = await extract_entities(memory())
        check("bad entity JSON -> fallback", fallback.fallback_used is True)
        check("fallback returns entities", len(fallback.entities) >= 2)
        check("fallback extracts tag", any(e.name == "Project Atlas" for e in fallback.entities))

        extraction._get_client = lambda: FakeClient(
            '{"relations":[{"source":"Project Atlas","target":"Mom","relation":"references","weight":1.5},'
            '{"source":"Unknown","target":"Mom","relation":"references","weight":0.8},'
            '{"source":"Mom","target":"Mom","relation":"knows","weight":0.8}]}'
        )
        rel_result = await extract_relations(
            memory(),
            [ExtractedEntity("Project Atlas", "project"), ExtractedEntity("Mom", "person")],
        )
        semantic = [r for r in rel_result.relations if r.relation == "references"]
        baseline = [r for r in rel_result.relations if r.relation == "mentioned_in"]
        check("valid relation JSON -> semantic relation", len(semantic) == 1)
        check("valid relation JSON -> co-occurrence baseline", len(baseline) == 1)
        check("relation weight clamped", semantic[0].weight == 1.0)
        check("unknown/self relations ignored", semantic[0].source == "Project Atlas")

        extraction._get_client = lambda: FakeClient("not json")
        rel_fallback = await extract_relations(
            memory(),
            [ExtractedEntity("Project Atlas", "project"), ExtractedEntity("Mom", "person")],
        )
        check("bad relation JSON -> fallback", rel_fallback.fallback_used is True)
        check("fallback relation generated", len(rel_fallback.relations) == 1)
    finally:
        extraction._get_client = original_get_client


def run_builder_helper_tests() -> None:
    print("\n=== 2. graph builder helpers ===")
    result = GraphBuildResult(memory_id="m1", user_id="u1", entities_extracted=2)
    check("GraphBuildResult serializable", result.to_dict()["entities_extracted"] == 2)

    m1 = memory(extra_metadata={GRAPH_EXTRACTED_AT_KEY: "2026-01-01T00:00:00"})
    m2 = memory(extra_metadata={})
    check("already processed true", _already_processed(m1) is True)
    check("already processed false", _already_processed(m2) is False)
    check("entity key lower/type", _entity_key("Project Atlas", "Project") == ("project atlas", "project"))
    check("merge aliases dedupes", _merge_aliases(["Atlas"], ["Atlas", "PA"]) == ["Atlas", "PA"])

    ent = SimpleNamespace(first_seen_at=datetime.now(UTC), last_seen_at=datetime.now(UTC) - timedelta(days=1))
    older = datetime.now(UTC) - timedelta(days=10)
    newer = datetime.now(UTC) + timedelta(days=1)
    _touch_entity(ent, older)
    _touch_entity(ent, newer)
    check("touch entity first_seen", ent.first_seen_at.date() == older.date())
    check("touch entity last_seen", ent.last_seen_at.date() == newer.date())

    atlas = SimpleNamespace(name="Project Atlas", entity_type="project", id=uuid4())
    mom = SimpleNamespace(name="Mom", entity_type="person", id=uuid4())
    found = _entity_lookup({("project atlas", "project"): atlas, ("mom", "person"): mom}, "project atlas")
    check("entity lookup case-insensitive", found is atlas)

    meta = _merge_relation_metadata({"reasons": ["old"]}, ExtractedRelation("A", "B", reason="new"))
    check("relation metadata reason merge", meta["reasons"] == ["old", "new"])

    m = memory(extra_metadata={})
    entity_result = SimpleNamespace(entities=[1, 2], fallback_used=True, error=None)
    relation_result = SimpleNamespace(relations=[1], fallback_used=False, error="oops")
    _mark_processed(m, entity_result, relation_result)
    check("mark processed timestamp", GRAPH_EXTRACTED_AT_KEY in m.extra_metadata)
    check("mark processed counts", m.extra_metadata["graph_entity_count"] == 2)
    check("mark processed fallback", m.extra_metadata["graph_extraction_fallback_used"] is True)
    check("mark processed relation error", m.extra_metadata["graph_relation_error"] == "oops")


def run_schema_route_tests() -> None:
    print("\n=== 3. schemas and routes ===")
    ec = EntityCreate(name="Project Atlas", entity_type="project", aliases=["Atlas"])
    eu = EntityUpdate(name="Project Atlas v2")
    rc = RelationCreate(source_entity_id=uuid4(), target_entity_id=uuid4(), relation="references", weight=0.7)
    ru = RelationUpdate(weight=0.8)
    check("EntityCreate schema", ec.name == "Project Atlas" and ec.aliases == ["Atlas"])
    check("EntityUpdate schema", eu.name == "Project Atlas v2")
    check("RelationCreate schema", rc.weight == 0.7)
    check("RelationUpdate schema", ru.weight == 0.8)

    from app.api.v1.entities import graph_router, relations_router, router
    from app.api.v1.memories import _safe_enqueue_graph_build

    entity_paths = {route.path for route in router.routes}
    relation_paths = {route.path for route in relations_router.routes}
    graph_paths = {route.path for route in graph_router.routes}
    check("POST /entities route exists", "/entities" in entity_paths)
    check("PATCH /entities/{entity_id} route exists", "/entities/{entity_id}" in entity_paths)
    check("POST /relations route exists", "/relations" in relation_paths)
    check("PATCH /relations/{relation_id} route exists", "/relations/{relation_id}" in relation_paths)
    check("GET /graph/clusters route exists", "/graph/clusters" in graph_paths)
    check("memory graph enqueue helper lazy", callable(_safe_enqueue_graph_build))

    py_compile.compile("app/tasks/graph_tasks.py", doraise=True)
    py_compile.compile("app/tasks/celery_app.py", doraise=True)
    celery_text = Path("app/tasks/celery_app.py").read_text(encoding="utf-8")
    check("celery includes graph tasks", "app.tasks.graph_tasks" in celery_text)
    check("celery routes graph task", "tasks.build_memory_graph" in celery_text)


def run_cluster_helper_tests() -> None:
    print("\n=== 4. clustering helpers ===")
    a, b, c = uuid4(), uuid4(), uuid4()
    visited: set = set()
    component = _walk_component(a, {a: {b}, b: {a}, c: set()}, visited)
    check("walk component connected", component == {a, b})
    check("walk component marks visited", visited == {a, b})

    e1 = SimpleNamespace(id=uuid4(), name="Low", mention_count=1)
    e2 = SimpleNamespace(id=uuid4(), name="High", mention_count=5)
    check("cluster id uses top mention", _cluster_id([e1, e2]).startswith(f"cluster-{str(e2.id)[:8]}"))

    node = GraphNode(id="Project Atlas", type="project", mentions=3)
    edge = GraphEdge(source="Mom", target="Project Atlas", relation="references", weight=0.8)
    cluster = GraphCluster(id="cluster-1", nodes=[node], edges=[edge], score=1.2)
    response = GraphClustersResponse(clusters=[cluster], generated_at=datetime.now(UTC))
    check("GraphCluster schema", response.clusters[0].edges[0].relation == "references")


def main() -> None:
    asyncio.run(run_extraction_tests())
    run_builder_helper_tests()
    run_schema_route_tests()
    run_cluster_helper_tests()
    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS}/{TOTAL} tests passed")
    if PASS != TOTAL:
        raise SystemExit(1)
    print("All Phase 4 tests passed.")


if __name__ == "__main__":
    main()
