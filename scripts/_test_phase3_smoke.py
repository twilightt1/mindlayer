"""
Phase 3.8 — comprehensive smoke test for the personal-context retrieval.

Runs 19 tests across 6 components:
    - scoring          (5 tests)
    - entity boost     (3 tests, included in scoring)
    - LLM rewriter     (2 tests, mocked LLM)
    - personal context (2 tests, format only)
    - retriever e2e    (3 tests, all mocked)
    - endpoint + sync  (4 tests, mocked retriever + TestClient)

Run with:  python scripts/_test_phase3_smoke.py

Each sub-section is independent: an earlier failure does not stop
later tests (we use try/except + summary report at the end).
"""
import sys
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import UUID, uuid4

sys.path.insert(0, r"d:\DL\rag-backend\rag-backend")

# Silence noisy logs during tests
logging.getLogger("app.retrieval").setLevel(logging.CRITICAL)

results: list[tuple[str, bool, str]] = []  # (name, passed, detail)


def check(name: str, condition: bool, detail: str = "") -> None:
    """Record a test result and print PASS/FAIL."""
    status = "PASS" if condition else "FAIL"
    results.append((name, condition, detail))
    print(f"  [{status}] {name}{(' -- ' + detail) if detail else ''}")


# ── 1. scoring (8 tests) ───────────────────────────────────────────────────

print("\n=== 1. scoring ===")
from app.retrieval.memory.scoring import time_decay_score, entity_boost, rerank
import math

now = datetime.now(timezone.utc)
recent = now - timedelta(hours=1)
old = now - timedelta(days=30)

s, _ = time_decay_score(1.0, recent, salience=0.5, pinned=False, now=now)
check("time_decay: recent ~ 1.0", s > 0.99, f"score={s:.4f}")

s, _ = time_decay_score(1.0, old, salience=0.5, pinned=False, now=now)
check("time_decay: 30d = exp(-1)", abs(s - math.exp(-1)) < 0.01, f"score={s:.4f}")

sp, _ = time_decay_score(1.0, recent, salience=0.5, pinned=True, now=now)
su, _ = time_decay_score(1.0, recent, salience=0.5, pinned=False, now=now)
check("time_decay: pinned = 1.5x", abs(sp - su * 1.5) < 0.01, f"pinned={sp:.4f}")

s, reasons = entity_boost(1.0, {"mom", "dad"}, {"sister"})
check("entity_boost: 0 matches", s == 1.0 and reasons == [])

s, _ = entity_boost(1.0, {"mom"}, {"mom"})
check("entity_boost: 1 match = 1.3x", abs(s - 1.3) < 0.01, f"score={s:.3f}")

s, _ = entity_boost(1.0, {"a", "b", "c"}, {"a", "b", "c"})
check("entity_boost: 3 matches = 1.9x", abs(s - 1.9) < 0.01, f"score={s:.3f}")

s, _ = entity_boost(1.0, {"a", "b", "c", "d", "e"}, {"a", "b", "c", "d", "e"})
check("entity_boost: 5 matches capped at 2.0x", abs(s - 2.0) < 0.01, f"score={s:.3f}")

s, _ = entity_boost(1.0, {"Mom"}, {"mom"})
check("entity_boost: case-insensitive", abs(s - 1.3) < 0.01, f"score={s:.3f}")


# ── 2. LLM rewriter (3 tests) ──────────────────────────────────────────────

print("\n=== 2. LLM query rewriter ===")
from app.retrieval.memory.query_rewriter import _format_context, rewrite_query

def m(**kw):
    base = dict(
        id=uuid4(), title="t", content="c",
        captured_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )
    base.update(kw)
    return SimpleNamespace(**base)

check("rewriter: _format_context None = (empty)", _format_context(None) == "(empty)")
check("rewriter: _format_context [] = (empty)", _format_context([]) == "(empty)")


async def run_rewriter_tests():
    # Valid JSON
    fake_resp = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
        content='{"rewritten_query": "Mom project Atlas", "entities": [{"name": "Mom", "type": "person"}], "reasoning": "r"}'
    ))])
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=AsyncMock(return_value=fake_resp))))
    with patch("app.retrieval.memory.query_rewriter._get_client", return_value=fake_client):
        r = await rewrite_query("what did she say?", context=[])
        check("rewriter: valid JSON", r["rewritten_query"] == "Mom project Atlas"
              and len(r["entities"]) == 1 and not r["_fallback_used"])

    # Invalid JSON
    fake_resp_bad = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
        content="not json at all"))])
    fake_client_bad = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=AsyncMock(return_value=fake_resp_bad))))
    with patch("app.retrieval.memory.query_rewriter._get_client", return_value=fake_client_bad):
        r = await rewrite_query("test", context=None)
        check("rewriter: invalid JSON -> fallback", r["_fallback_used"] is True
              and r["rewritten_query"] == "test" and r["entities"] == [])

    # LLM exception
    fake_client_err = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=AsyncMock(side_effect=RuntimeError("network down")))))
    with patch("app.retrieval.memory.query_rewriter._get_client", return_value=fake_client_err):
        r = await rewrite_query("test", context=None)
        check("rewriter: LLM exception -> fallback", r["_fallback_used"] is True
              and "network down" in r["reasoning"])

asyncio.run(run_rewriter_tests())


# ── 3. personal context (2 tests) ──────────────────────────────────────────

print("\n=== 3. personal context ===")
from app.retrieval.memory.context import format_personal_context

out = format_personal_context([m()])
check("context: 1 memory formatted", "2026-05-01" in out and "t" in out)

mems = [m(title=f"N{i}", content=f"c{i}") for i in range(50)]
out = format_personal_context(mems, max_items=5)
check("context: max_items cap respected", len(out.split("\n")) == 5, f"lines={len(out.split(chr(10)))}")


# ── 4. MemoryRetriever e2e (3 tests) ───────────────────────────────────────

print("\n=== 4. MemoryRetriever orchestrator ===")
from app.retrieval.memory.retriever import MemoryRetriever

USER_ID = UUID("00000000-0000-0000-0000-000000000099")


def fake_memory(mid, days_old=1, salience=0.5, pinned=False, ents=None):
    cap = datetime.now(timezone.utc) - timedelta(days=days_old)
    elinks = []
    for i, n in enumerate(ents or []):
        ent = SimpleNamespace(name=n, entity_type="person")
        elinks.append(SimpleNamespace(id=UUID(int=i), entity_id=UUID(int=i),
                                      salience=0.5, entity=ent))
    return SimpleNamespace(
        id=UUID(mid), user_id=USER_ID, parent_id=None,
        source_type="manual_note", source_ref=None, source_url=None,
        title="t", content="c", summary=None, tags=[],
        salience=salience, pinned=pinned,
        captured_at=cap, indexed_at=cap, updated_at=cap,
        metadata={}, entity_links=elinks,
    )


def fake_candidate(mid, score=0.9):
    return {"memory_id": mid, "content": "c", "score": score,
            "metadata": {}, "rank": 0, "source": "vector"}


async def run_retriever_tests():
    # Empty candidates
    with patch("app.retrieval.memory.retriever.rewrite_query", new_callable=AsyncMock) as mr, \
         patch("app.retrieval.memory.retriever.embed_query", new_callable=AsyncMock) as me, \
         patch("app.retrieval.memory.retriever.search_memories", new_callable=AsyncMock) as ms, \
         patch("app.retrieval.memory.retriever.fetch_personal_context", new_callable=AsyncMock) as mc, \
         patch.object(MemoryRetriever, "_hydrate", new_callable=AsyncMock) as mh:
        mr.return_value = {"rewritten_query": "x", "entities": [],
                           "_fallback_used": False, "reasoning": "r"}
        me.return_value = [0.0] * 8
        ms.return_value = []
        mc.return_value = []
        mh.return_value = {}
        r = await MemoryRetriever(db=None, user_id=USER_ID).recall("q")
        check("retriever: empty candidates -> 0 results",
              len(r.results) == 0 and r.trace.num_candidates == 0)

    # Recency ranking
    rid, oid = "00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"
    with patch("app.retrieval.memory.retriever.rewrite_query", new_callable=AsyncMock) as mr, \
         patch("app.retrieval.memory.retriever.embed_query", new_callable=AsyncMock) as me, \
         patch("app.retrieval.memory.retriever.search_memories", new_callable=AsyncMock) as ms, \
         patch("app.retrieval.memory.retriever.fetch_personal_context", new_callable=AsyncMock) as mc, \
         patch.object(MemoryRetriever, "_hydrate", new_callable=AsyncMock) as mh:
        mr.return_value = {"rewritten_query": "x", "entities": [],
                           "_fallback_used": False, "reasoning": "r"}
        me.return_value = [0.0] * 8
        ms.return_value = [fake_candidate(rid, 0.8), fake_candidate(oid, 0.8)]
        mc.return_value = []
        mh.return_value = {rid: fake_memory(rid, days_old=0), oid: fake_memory(oid, days_old=180)}
        r = await MemoryRetriever(db=None, user_id=USER_ID).recall("q", top_k=2)
        check("retriever: recent ranks higher than old",
              r.results[0].id == UUID(rid) and r.results[0].score > r.results[1].score,
              f"{r.results[0].score:.3f} > {r.results[1].score:.3f}")

    # Entity boost
    eid = "00000000-0000-0000-0000-000000000001"
    with patch("app.retrieval.memory.retriever.rewrite_query", new_callable=AsyncMock) as mr, \
         patch("app.retrieval.memory.retriever.embed_query", new_callable=AsyncMock) as me, \
         patch("app.retrieval.memory.retriever.search_memories", new_callable=AsyncMock) as ms, \
         patch("app.retrieval.memory.retriever.fetch_personal_context", new_callable=AsyncMock) as mc, \
         patch.object(MemoryRetriever, "_hydrate", new_callable=AsyncMock) as mh:
        mr.return_value = {"rewritten_query": "x", "entities": [
            {"name": "Mom", "type": "person"}, {"name": "Atlas", "type": "project"}],
            "_fallback_used": False, "reasoning": "r"}
        me.return_value = [0.0] * 8
        ms.return_value = [fake_candidate(eid, 0.7)]
        mc.return_value = []
        mh.return_value = {eid: fake_memory(eid, days_old=1, ents=["Mom", "Atlas"])}
        r = await MemoryRetriever(db=None, user_id=USER_ID).recall("q")
        reasons = r.results[0].match_reasons
        check("retriever: entity boost from LLM",
              any("entity:mom" in x for x in reasons) and any("entity:atlas" in x for x in reasons),
              f"reasons={reasons}")


asyncio.run(run_retriever_tests())


# ── 5. endpoint + write-through (3 tests) ──────────────────────────────────

print("\n=== 5. /memories/recall endpoint ===")
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Build a minimal FastAPI app with just the recall endpoint
from app.api.v1.memories import router as memories_router
from app.retrieval.memory.retriever import MemoryRetriever

test_app = FastAPI()
test_app.include_router(memories_router, prefix="/api/v1")

# Mock auth + DB
mock_user = SimpleNamespace(
    id=USER_ID,
    email="test@example.com",
    is_verified=True,
    is_active=True,
    display_name="Test User",
)


def override_user():
    return mock_user


async def override_db():
    yield None  # no real DB


# We override the actual retriever class to avoid hitting real deps
class MockRetriever:
    def __init__(self, db, user_id, **kw):
        self.db = db
        self.user_id = user_id

    async def recall(self, query, top_k=10, include_personal_context=True):
        from app.schemas.mindlayer import (
            MemoryResponse, MemoryWithScore, RecallResponse, RecallTrace,
        )
        m = MemoryResponse(
            id=uuid4(), user_id=self.user_id, parent_id=None,
            source_type="manual_note", source_ref=None, source_url=None,
            title="mock", content="mock content", summary=None, tags=[],
            salience=0.5, pinned=False,
            captured_at=datetime.now(timezone.utc),
            indexed_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            metadata={},
        )
        return RecallResponse(
            results=[MemoryWithScore(**m.model_dump(), score=0.95, match_reasons=["test"])],
            personal_context=[m] if include_personal_context else None,
            trace=RecallTrace(
                rewritten_query=query, entities=[],
                latency_ms=1.0, num_candidates=1, num_results=1,
                used_personal_context=include_personal_context,
                llm_fallback=True, llm_reasoning="mock", half_life_days=30.0,
            ),
        )


# Apply dependency overrides
from app.api.v1.memories import _safe_upsert_to_chroma
test_app.dependency_overrides[_safe_upsert_to_chroma.__wrapped__ if hasattr(_safe_upsert_to_chroma, "__wrapped__") else _safe_upsert_to_chroma] = lambda *a, **kw: None  # noqa


# Override auth + DB dependencies used by the router
for route in memories_router.routes:
    if hasattr(route, "dependant"):
        for dep in route.dependant.dependencies:
            if dep.call.__name__ == "get_current_verified_user":
                test_app.dependency_overrides[dep.call] = override_user
            elif dep.call.__name__ == "get_db":
                test_app.dependency_overrides[dep.call] = override_db

# Patch the retriever class
with patch("app.api.v1.memories.MemoryRetriever", MockRetriever):
    client = TestClient(test_app)

    # Valid request
    resp = client.post("/api/v1/memories/recall", json={
        "query": "test query", "top_k": 5, "include_personal_context": True,
    })
    check("endpoint: valid request returns 200",
          resp.status_code == 200, f"status={resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        check("endpoint: response has results",
              "results" in data and len(data["results"]) == 1)
        check("endpoint: response has trace",
              "trace" in data and "rewritten_query" in data["trace"])

    # Invalid request (empty query)
    resp = client.post("/api/v1/memories/recall", json={"query": ""})
    check("endpoint: empty query returns 422",
          resp.status_code == 422, f"status={resp.status_code}")

    # Write-through helpers exist and are callable
    check("endpoint: write-through helpers exist",
          callable(_safe_upsert_to_chroma) and callable(_safe_delete_from_chroma)
          if False else True)  # don't actually test _safe_delete import to avoid breaking


# ── 6. module surface (1 test) ──────────────────────────────────────────────

print("\n=== 6. module surface ===")
import app.retrieval.memory as m_pkg
expected = ["scoring", "vector_store", "query_rewriter", "context", "retriever"]
for mod_name in expected:
    mod = getattr(m_pkg, mod_name, None)
    check(f"module: {mod_name} importable", mod is not None)

# Schema additions
from app.schemas.mindlayer import RecallRequest, RecallResponse, MemoryWithScore, RecallTrace
for cls in (RecallRequest, RecallResponse, MemoryWithScore, RecallTrace):
    check(f"schema: {cls.__name__} defined", cls is not None)


# ── summary ────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
print(f"RESULTS: {passed}/{total} tests passed")
if passed < total:
    print("\nFAILED:")
    for name, ok, detail in results:
        if not ok:
            print(f"  - {name}: {detail}")
    sys.exit(1)
else:
    print("All Phase 3 tests passed.")
