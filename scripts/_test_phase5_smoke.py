"""
Phase 5 smoke tests for memory-aware chat assistant integration.

Run with: python scripts/_test_phase5_smoke.py
"""
from __future__ import annotations

import asyncio
import logging
import sys
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch  # noqa: F401
from uuid import uuid4

from pydantic import ValidationError

sys.path.insert(0, r"d:\DL\rag-backend\rag-backend")
logging.getLogger("app.agents.personal_context_agent").setLevel(logging.CRITICAL)

results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    results.append((name, condition, detail))
    print(f"  [{status}] {name}{(' -- ' + detail) if detail else ''}")


def memory(**overrides):
    data = {
        "id": uuid4(),
        "user_id": uuid4(),
        "parent_id": None,
        "source_type": "manual_note",
        "source_ref": None,
        "source_url": None,
        "title": "Project Atlas",
        "content": "Mom discussed the Atlas launch plan.",
        "summary": "Atlas launch update",
        "tags": ["atlas"],
        "salience": 0.8,
        "pinned": False,
        "captured_at": datetime.now(UTC),
        "indexed_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "metadata": {},
    }
    data.update(overrides)
    return SimpleNamespace(**data)


print("\n=== 1. request schema ===")
from app.schemas.conversation import ChatRequest  # noqa: E402

req = ChatRequest(query="What did Mom say?")
check("ChatRequest defaults personal context", req.include_personal_context is True)
check("ChatRequest defaults graph context", req.include_graph_context is True)
check("ChatRequest default top_k", req.personal_memory_top_k == 5)
try:
    ChatRequest(query="")
    check("ChatRequest rejects empty query", False)
except ValidationError:
    check("ChatRequest rejects empty query", True)
try:
    ChatRequest(query="   ")
    check("ChatRequest rejects whitespace query", False)
except ValidationError:
    check("ChatRequest rejects whitespace query", True)
try:
    ChatRequest(query="x", personal_memory_top_k=11)
    check("ChatRequest top_k upper bound", False)
except ValidationError:
    check("ChatRequest top_k upper bound", True)


print("\n=== 2. personal memory chunks ===")
from app.agents.personal_context_agent import memory_to_chunk, recall_to_chunks, personal_context_agent  # noqa: E402
from app.schemas.mindlayer import MemoryResponse, MemoryWithScore, RecallResponse, RecallTrace  # noqa: E402

base_memory = MemoryResponse(**memory().__dict__)
scored_memory = MemoryWithScore(**base_memory.model_dump(), score=0.91, match_reasons=["entity:mom"])
trace = RecallTrace(
    rewritten_query="Mom Atlas",
    entities=[{"name": "Mom", "type": "person"}],
    latency_ms=12.0,
    num_candidates=1,
    num_results=1,
    used_personal_context=True,
    llm_fallback=False,
    llm_reasoning="ok",
    half_life_days=30.0,
)
recall = RecallResponse(results=[scored_memory], personal_context=[base_memory], trace=trace)
chunk = memory_to_chunk(scored_memory, score=scored_memory.score, match_reasons=scored_memory.match_reasons)
check("memory chunk source_type", chunk["metadata"]["source_type"] == "personal_memory")
check("memory chunk id metadata", chunk["metadata"]["memory_id"] == str(scored_memory.id))
check("memory chunk includes title", "Project Atlas" in chunk["content"])
chunks = recall_to_chunks(recall, limit=5)
check("recall_to_chunks dedupes result/context", len(chunks) == 1)
check("recall_to_chunks preserves score", chunks[0]["rerank_score"] == 0.91)


async def run_personal_agent_tests():
    disabled_state = {"agent_trace": {}, "personal_memory_enabled": False, "user_id": str(uuid4()), "query": "q"}
    out = await personal_context_agent(disabled_state)
    check("personal agent disabled", out["personal_memory_chunks"] == [] and out["agent_trace"]["personal_memory"]["enabled"] is False)

    zero_state = {"agent_trace": {}, "personal_memory_enabled": True, "personal_memory_top_k": 0, "user_id": str(uuid4()), "query": "q"}
    out = await personal_context_agent(zero_state)
    check("personal agent top_k zero", out["agent_trace"]["personal_memory"]["reason"] == "top_k_zero")

    fallback_state = {"agent_trace": {}, "personal_memory_enabled": True, "personal_memory_top_k": 3, "user_id": str(uuid4()), "query": "q"}
    with patch("app.agents.personal_context_agent.AsyncSessionLocal", side_effect=RuntimeError("db down")):
        out = await personal_context_agent(fallback_state)
    check("personal agent fails open", out["personal_memory_chunks"] == [] and out["agent_trace"]["personal_memory"]["fallback_used"] is True)


asyncio.run(run_personal_agent_tests())


print("\n=== 3. graph context chunks ===")
from app.agents.graph_context_agent import (  # noqa: E402
    _entity_matches_text,
    _memory_ids_from_chunks,
    build_graph_context_chunk,
)

entity_id = uuid4()
other_id = uuid4()
entity = SimpleNamespace(id=entity_id, name="Project Atlas", entity_type="project", aliases=["Atlas"], mention_count=3)
other = SimpleNamespace(id=other_id, name="Mom", entity_type="person", aliases=[], mention_count=2)
relation = SimpleNamespace(
    source_entity_id=other_id,
    target_entity_id=entity_id,
    relation="references",
    weight=0.82,
    evidence_count=2,
)
check("graph empty chunk none", build_graph_context_chunk([], []) is None)
graph_chunk = build_graph_context_chunk([entity, other], [relation])
check("graph chunk created", graph_chunk is not None)
check("graph chunk source_type", graph_chunk["metadata"]["source_type"] == "knowledge_graph")
check("graph chunk entity names", "Project Atlas" in graph_chunk["metadata"]["entity_names"])
check("graph chunk relation text", "Mom --references--> Project Atlas" in graph_chunk["content"])
check("entity matches name", _entity_matches_text(entity, "tell me about project atlas"))
check("entity matches alias", _entity_matches_text(entity, "what about atlas?"))
mem_id = uuid4()
ids = _memory_ids_from_chunks([
    {"metadata": {"memory_id": str(mem_id)}},
    {"metadata": {"memory_id": "not-a-uuid"}},
])
check("memory ids from chunks filters invalid", ids == [mem_id])


print("\n=== 4. context merge ===")
from app.agents.context_merge_agent import chunk_identity, merge_context_chunks, normalize_chunk  # noqa: E402

doc = {"id": "doc-1", "content": "doc", "metadata": {"filename": "doc.txt"}, "rerank_score": 0.9}
mem = {"id": "mem-1", "content": "mem", "metadata": {"memory_id": "m1", "source_type": "personal_memory"}, "rerank_score": 0.7}
graph = {"id": "graph-1", "content": "graph", "metadata": {"source_type": "knowledge_graph"}, "rerank_score": 0.5}
normalized = normalize_chunk({}, default_source_type="document", rank=1)
check("normalize default source", normalized["metadata"]["source_type"] == "document")
check("chunk identity memory id", chunk_identity(mem) == "memory_id:m1")
state = {"reranked_chunks": [doc], "personal_memory_chunks": [mem], "graph_context_chunks": [graph], "agent_trace": {}}
merged = merge_context_chunks(state)
check("merge preserves order", [c["content"] for c in merged] == ["doc", "mem", "graph"])
state_dup = {"reranked_chunks": [], "personal_memory_chunks": [mem, dict(mem)], "graph_context_chunks": []}
check("merge dedupes", len(merge_context_chunks(state_dup)) == 1)
state_cap = {
    "reranked_chunks": [
        {"id": f"doc-{i}", "content": f"doc {i}", "metadata": {"filename": f"doc-{i}.txt"}}
        for i in range(20)
    ],
    "personal_memory_chunks": [],
    "graph_context_chunks": [],
}
check("merge cap", len(merge_context_chunks(state_cap, max_chunks=3)) == 3)


print("\n=== 5. graph routing helpers ===")
from app.agents.routing import has_grounding_context, route_after_grade_docs, route_after_grade_gen  # noqa: E402

check("has grounding via personal", has_grounding_context({"personal_memory_chunks": [mem]}))
check("route docs no context answer", route_after_grade_docs({"query_type": "rag"}) == "answer")
check("route docs relevant answer", route_after_grade_docs({"query_type": "rag", "grounding_context_chunks": [doc], "context_relevant": True}) == "answer")
check(
    "route docs irrelevant retries docs",
    route_after_grade_docs({"query_type": "rag", "grounding_context_chunks": [doc], "context_relevant": False, "has_documents": True, "retry_count": 0})
    == "retry_retrieval_for_irrelevant_context",
)
check(
    "route memory-only irrelevant answer",
    route_after_grade_docs({"query_type": "rag", "grounding_context_chunks": [mem], "context_relevant": False, "has_documents": False})
    == "answer",
)
check("route gen no context save", route_after_grade_gen({"query_type": "rag"}) == "save")
check(
    "route gen hallucination retries answer",
    route_after_grade_gen({"query_type": "rag", "grounding_context_chunks": [doc], "is_hallucination": True, "retry_count": 0})
    == "retry_answer_for_hallucination",
)


print("\n=== 6. router and source metadata ===")
from app.agents.answer_agent import _source_label  # noqa: E402
from app.agents.router_agent import _router_fallback  # noqa: E402

router_state = {"agent_trace": {}, "has_documents": False, "personal_memory_enabled": True}
_router_fallback(router_state, "who is Mom?", "llm down")
check("router fallback uses personal memory", router_state["query_type"] == "rag")
router_state = {"agent_trace": {}, "has_documents": False, "personal_memory_enabled": False}
_router_fallback(router_state, "hello", "llm down")
check("router fallback chitchat when no sources", router_state["query_type"] == "chitchat")
check("source label memory", _source_label(mem) == "personal memory")
check("source label graph", _source_label(graph) == "knowledge graph")

try:
    from app.api.v1.chat import _source_event_payload

    payload = _source_event_payload(mem)
    check("SSE source memory metadata", payload["source_type"] == "personal_memory" and payload["memory_id"] == "m1")
except Exception as exc:  # noqa: BLE001
    check("SSE source memory metadata", False, str(exc))


print("\n" + "=" * 60)
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"RESULTS: {passed}/{total} tests passed")
if passed != total:
    print("Failures:")
    for name, ok, detail in results:
        if not ok:
            print(f"  - {name}: {detail}")
    raise SystemExit(1)
print("All Phase 5 tests passed.")
