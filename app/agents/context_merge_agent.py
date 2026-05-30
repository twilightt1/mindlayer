"""Merge document, personal memory, and graph context for answer generation."""
from __future__ import annotations

import hashlib
from typing import Any

from app.agents.state import AgentState

MAX_GROUNDING_CHUNKS = 10


async def context_merge_agent(state: AgentState) -> AgentState:
    """Merge all available grounding sources into `reranked_chunks`."""
    state.setdefault("agent_trace", {})
    merged = merge_context_chunks(state)
    state["grounding_context_chunks"] = merged
    state["reranked_chunks"] = merged
    state["agent_trace"]["context_merge"] = {
        "document_chunks": len(state.get("doc_context_chunks", []) or []),
        "personal_memory_chunks": len(state.get("personal_memory_chunks", []) or []),
        "graph_context_chunks": len(state.get("graph_context_chunks", []) or []),
        "merged_chunks": len(merged),
        "max_chunks": MAX_GROUNDING_CHUNKS,
    }
    return state


def merge_context_chunks(state: AgentState, *, max_chunks: int = MAX_GROUNDING_CHUNKS) -> list[dict[str, Any]]:
    """Merge context chunks by priority: documents, memories, graph facts."""
    doc_chunks = state.get("reranked_chunks", []) or []
    state["doc_context_chunks"] = doc_chunks

    ordered_groups = [
        ("document", doc_chunks),
        ("personal_memory", state.get("personal_memory_chunks", []) or []),
        ("knowledge_graph", state.get("graph_context_chunks", []) or []),
    ]

    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for default_source_type, chunks in ordered_groups:
        for chunk in chunks:
            normalized = normalize_chunk(chunk, default_source_type=default_source_type, rank=len(merged) + 1)
            key = chunk_identity(normalized)
            if key in seen:
                continue
            seen.add(key)
            merged.append(normalized)
            if len(merged) >= max_chunks:
                return merged
    return merged


def normalize_chunk(chunk: dict[str, Any], *, default_source_type: str, rank: int) -> dict[str, Any]:
    """Ensure all chunks have source metadata expected by answer/SSE code."""
    metadata = dict(chunk.get("metadata") or {})
    metadata.setdefault("source_type", default_source_type)
    metadata.setdefault("filename", _default_filename(default_source_type))
    normalized = dict(chunk)
    normalized["metadata"] = metadata
    normalized.setdefault("rank", rank)
    normalized.setdefault("rerank_score", normalized.get("score", 0.0))
    normalized.setdefault("score", normalized.get("rerank_score", 0.0))
    return normalized


def chunk_identity(chunk: dict[str, Any]) -> str:
    """Return a stable identity for deduping mixed-source chunks."""
    metadata = chunk.get("metadata") or {}
    for field in ("memory_id", "document_id", "parent_id", "chunk_id"):
        value = metadata.get(field) or chunk.get(field)
        if value:
            return f"{field}:{value}"
    if chunk.get("id"):
        return f"id:{chunk['id']}"
    content = (chunk.get("content") or "").strip().encode("utf-8")
    return "content:" + hashlib.sha1(content).hexdigest()


def _default_filename(source_type: str) -> str:
    if source_type == "personal_memory":
        return "Personal memory"
    if source_type == "knowledge_graph":
        return "Knowledge graph"
    return "Document context"
