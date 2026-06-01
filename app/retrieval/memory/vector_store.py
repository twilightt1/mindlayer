"""
Phase 3 — ChromaDB vector store for the personal Memory collection.

A single shared collection ``mindlayer_memories`` is partitioned by
``user_id`` via ChromaDB ``where={...}`` filter. We keep one collection
(not one per user) to avoid expensive create/destroy churn; the
``user_id`` filter is the security boundary.

Mirrors the structure of :mod:`app.retrieval.vector_retriever` but
operates on the ``Memory`` table instead of document chunks.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any, Callable

import httpx

from app.config import settings
from app.models.memory import Memory
from app.retrieval.embedder import embed_texts, embed_texts_sync

# Lazily imported so this module is importable in test/CLI contexts
# that don't have ChromaDB running.
if TYPE_CHECKING:
    import chromadb  # noqa: F401  (only for type hints)

log = logging.getLogger(__name__)

COLLECTION_NAME = "mindlayer_memories"

_async_client: chromadb.AsyncHttpClient | None = None
_sync_client: chromadb.HttpClient | None = None


# ── retry decorator (mirrors app.retrieval.vector_retriever.with_retry) ─────


def _with_retry(retries: int = 3, base_delay: float = 1.0):
    """Decorator that retries ChromaDB calls on connection errors."""

    def decorator(func: Callable):
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                last_exc: Exception | None = None
                for i in range(retries):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:  # noqa: BLE001
                        last_exc = e
                        if any(
                            msg in str(e)
                            for msg in ["Could not connect", "connection", "Refused"]
                        ) or isinstance(e, (ValueError, httpx.ConnectError)):
                            delay = base_delay * (2 ** i)
                            log.warning(
                                "Chroma connection failed (attempt %d/%d). "
                                "Retrying in %.1fs...",
                                i + 1, retries, delay,
                                extra={"error": str(e)},
                            )
                            await asyncio.sleep(delay)
                        else:
                            raise
                log.error(
                    "Failed to connect to Chroma after all retries.",
                    extra={"error": str(last_exc)},
                )
                raise last_exc  # type: ignore[misc]

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                last_exc: Exception | None = None
                for i in range(retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:  # noqa: BLE001
                        last_exc = e
                        if any(
                            msg in str(e)
                            for msg in ["Could not connect", "connection", "Refused"]
                        ) or isinstance(e, (ValueError, httpx.ConnectError)):
                            delay = base_delay * (2 ** i)
                            log.warning(
                                "Chroma connection failed (attempt %d/%d). "
                                "Retrying in %.1fs...",
                                i + 1, retries, delay,
                                extra={"error": str(e)},
                            )
                            time.sleep(delay)
                        else:
                            raise
                log.error(
                    "Failed to connect to Chroma after all retries.",
                    extra={"error": str(last_exc)},
                )
                raise last_exc  # type: ignore[misc]

            return sync_wrapper

    return decorator


# ── client singletons ────────────────────────────────────────────────────────


@_with_retry()
async def _get_async_client():
    global _async_client
    if _async_client is None:
        import chromadb  # lazy: only needed at runtime
        _async_client = await chromadb.AsyncHttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
    return _async_client


@_with_retry()
def _get_sync_client():
    global _sync_client
    if _sync_client is None:
        import chromadb  # lazy: only needed at runtime
        _sync_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
    return _sync_client


@_with_retry()
async def _get_collection():
    cli = await _get_async_client()
    return await cli.get_or_create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ── memory <-> document helpers ─────────────────────────────────────────────


def _memory_to_document(memory: Memory) -> str:
    """Concatenate title + content for the ChromaDB document text.

    Title is prepended (when present) so embedding captures the topic;
    content carries the body.
    """
    parts: list[str] = []
    if memory.title:
        parts.append(f"Title: {memory.title}")
    parts.append(memory.content)
    return "\n".join(parts)


def _memory_to_metadata(memory: Memory) -> dict[str, Any]:
    """Build the metadata dict stored alongside the vector.

    All values must be scalar or list-of-str (ChromaDB constraint).
    """
    captured_iso = memory.captured_at.isoformat() if memory.captured_at else None
    return {
        "user_id":     str(memory.user_id),
        "memory_id":   str(memory.id),
        "source_type": memory.source_type,
        "captured_at": captured_iso,
        "salience":    float(memory.salience),
        "pinned":      bool(memory.pinned),
        "tags":        list(memory.tags or []),
    }


# ── public API ──────────────────────────────────────────────────────────────


async def upsert_memory(memory: Memory) -> None:
    """Embed a memory and write it to the ChromaDB collection.

    Best-effort: logs and re-raises. Callers should wrap in try/except
    so a ChromaDB outage doesn't fail a CRUD request — the Postgres
    ``Memory`` row is the source of truth.
    """
    collection = await _get_collection()
    document = _memory_to_document(memory)
    metadata = _memory_to_metadata(memory)
    embedding = (await embed_texts([document]))[0]
    await collection.upsert(
        ids=[str(memory.id)],
        documents=[document],
        embeddings=[embedding],
        metadatas=[metadata],
    )
    log.info(
        "Upserted memory into ChromaDB",
        extra={"memory_id": str(memory.id), "user_id": str(memory.user_id)},
    )


def upsert_memory_sync(memory: Memory) -> None:
    """Synchronous variant — used by Celery / CLI contexts."""
    cli = _get_sync_client()
    collection = cli.get_or_create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    document = _memory_to_document(memory)
    metadata = _memory_to_metadata(memory)
    embedding = embed_texts_sync([document])[0]
    collection.upsert(
        ids=[str(memory.id)],
        documents=[document],
        embeddings=[embedding],
        metadatas=[metadata],
    )
    log.info(
        "Upserted memory into ChromaDB (sync)",
        extra={"memory_id": str(memory.id), "user_id": str(memory.user_id)},
    )


async def delete_memory(memory_id: str) -> None:
    """Remove a memory's vector from the collection (best-effort)."""
    try:
        collection = await _get_collection()
        await collection.delete(ids=[memory_id])
        log.info("Deleted memory from ChromaDB", extra={"memory_id": memory_id})
    except Exception as e:  # noqa: BLE001
        log.warning(
            "Failed to delete memory from ChromaDB",
            extra={"memory_id": memory_id, "error": str(e)},
        )


async def search_memories(
    query_embedding: list[float],
    *,
    user_id: str,
    top_k: int = 10,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Vector search restricted to a single user.

    Returns a list of dicts:
        {memory_id, content, score, metadata, rank, source="vector"}
    """
    try:
        collection = await _get_collection()
    except Exception as e:  # noqa: BLE001
        log.warning("Chroma unavailable for search", extra={"error": str(e)})
        return []

    count = await collection.count()
    if count == 0:
        return []

    user_filter: dict[str, Any] = {"user_id": {"$eq": user_id}}
    if where:
        user_filter.update(where)

    results = await collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, count),
        where=user_filter,
    )

    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    ids = results.get("ids", [[]])[0]

    if not docs:
        return []

    out: list[dict[str, Any]] = []
    for i, (doc, dist, meta, mid) in enumerate(
        zip(docs, distances, metadatas, ids)
    ):
        out.append(
            {
                "memory_id": mid,
                "content":   doc,
                "score":     1.0 - dist,  # cosine distance -> similarity
                "metadata":  meta,
                "rank":      i,
                "source":    "vector",
            }
        )
    return out
