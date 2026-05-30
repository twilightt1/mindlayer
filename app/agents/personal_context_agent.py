"""Personal memory context node for the chat agent graph."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from app.agents.state import AgentState
from app.database import AsyncSessionLocal
from app.retrieval.memory.retriever import MemoryRetriever
from app.schemas.mindlayer import MemoryResponse, MemoryWithScore, RecallResponse

log = logging.getLogger(__name__)

DEFAULT_MEMORY_SCORE = 0.35


async def personal_context_agent(state: AgentState) -> AgentState:
    """Fetch personal memory recall and convert it into answer-agent chunks."""
    state.setdefault("agent_trace", {})
    state["personal_memory_chunks"] = []
    state["personal_recall_trace"] = {}

    if not state.get("personal_memory_enabled", True):
        state["agent_trace"]["personal_memory"] = {"enabled": False, "chunks": 0}
        return state

    top_k = int(state.get("personal_memory_top_k", 5) or 0)
    if top_k <= 0:
        state["agent_trace"]["personal_memory"] = {"enabled": True, "chunks": 0, "reason": "top_k_zero"}
        return state

    query = state.get("rewritten_query") or state.get("query") or ""
    if not query.strip():
        state["agent_trace"]["personal_memory"] = {"enabled": True, "chunks": 0, "reason": "empty_query"}
        return state

    try:
        async with AsyncSessionLocal() as db:
            retriever = MemoryRetriever(db, UUID(state["user_id"]))
            recall = await retriever.recall(query, top_k=top_k, include_personal_context=True)
        chunks = recall_to_chunks(recall, limit=top_k)
        state["personal_memory_chunks"] = chunks
        state["personal_recall_trace"] = recall.trace.model_dump()
        state["agent_trace"]["personal_memory"] = {
            "enabled": True,
            "chunks": len(chunks),
            "recall_results": len(recall.results),
            "personal_context": len(recall.personal_context or []),
            "trace": state["personal_recall_trace"],
        }
    except Exception as exc:  # noqa: BLE001
        log.warning("Personal memory context failed", extra={"error": str(exc)})
        state["personal_memory_chunks"] = []
        state["personal_recall_trace"] = {"error": str(exc)}
        state["agent_trace"]["personal_memory"] = {
            "enabled": True,
            "chunks": 0,
            "fallback_used": True,
            "error": str(exc),
        }
    return state


def recall_to_chunks(recall: RecallResponse, *, limit: int = 5) -> list[dict[str, Any]]:
    """Convert recall results and recent/pinned context into answer chunks."""
    seen: set[str] = set()
    chunks: list[dict[str, Any]] = []

    for memory in recall.results:
        chunk = memory_to_chunk(
            memory,
            score=float(getattr(memory, "score", DEFAULT_MEMORY_SCORE) or DEFAULT_MEMORY_SCORE),
            match_reasons=list(getattr(memory, "match_reasons", []) or []),
            rank=len(chunks) + 1,
        )
        memory_id = chunk["metadata"]["memory_id"]
        if memory_id not in seen:
            seen.add(memory_id)
            chunks.append(chunk)
        if len(chunks) >= limit:
            return chunks

    for memory in recall.personal_context or []:
        chunk = memory_to_chunk(memory, score=DEFAULT_MEMORY_SCORE, match_reasons=["personal_context"], rank=len(chunks) + 1)
        memory_id = chunk["metadata"]["memory_id"]
        if memory_id not in seen:
            seen.add(memory_id)
            chunks.append(chunk)
        if len(chunks) >= limit:
            break

    return chunks


def memory_to_chunk(
    memory: MemoryResponse | MemoryWithScore,
    *,
    score: float = DEFAULT_MEMORY_SCORE,
    match_reasons: list[str] | None = None,
    rank: int = 1,
) -> dict[str, Any]:
    """Format one personal memory as a retrieval-style chunk."""
    captured = _format_datetime(memory.captured_at)
    title = memory.title or "Untitled memory"
    summary = (memory.summary or "").strip()
    content = (memory.content or "").strip()
    body = summary if summary else content
    if summary and content and summary not in content:
        body = f"{summary}\n{content}"

    chunk_content = f"Personal memory ({captured})\nTitle: {title}\n{body}".strip()
    return {
        "id": f"memory:{memory.id}",
        "content": chunk_content,
        "rerank_score": score,
        "score": score,
        "rank": rank,
        "match_reasons": match_reasons or [],
        "metadata": {
            "filename": f"Memory: {title}",
            "source_type": "personal_memory",
            "memory_id": str(memory.id),
            "captured_at": captured,
            "tags": list(memory.tags or []),
        },
    }


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "unknown-date"
    return value.isoformat()
