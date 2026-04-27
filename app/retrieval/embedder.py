import logging

import httpx

from app.config import settings

log = logging.getLogger(__name__)


def _embedding_url() -> str:
    return f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/embeddings"


def _embedding_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.FRONTEND_URL,
        "X-Title": "SupportMind",
    }


def _embedding_payload(batch: list[str]) -> dict:
    return {
        "model": settings.EMBED_MODEL,
        "input": batch,
    }


def _parse_embeddings(payload: dict) -> list[list[float]]:
    data = payload.get("data") or []
    embeddings = [item.get("embedding") for item in data if item.get("embedding")]
    if not embeddings:
        raise ValueError("No embedding data received")
    return embeddings


def _batches(texts: list[str]) -> list[list[str]]:
    batch_size = max(1, settings.EMBED_BATCH_SIZE)
    return [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    embeddings: list[list[float]] = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for batch in _batches(texts):
                response = await client.post(
                    _embedding_url(),
                    headers=_embedding_headers(),
                    json=_embedding_payload(batch),
                )
                response.raise_for_status()
                embeddings.extend(_parse_embeddings(response.json()))
        return embeddings
    except Exception as e:
        log.error("Failed to get embeddings", exc_info=True)
        raise ValueError(f"Failed to get embeddings: {e}")


async def embed_query(query: str) -> list[float]:
    return (await embed_texts([query]))[0]


def embed_texts_sync(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    embeddings: list[list[float]] = []
    try:
        with httpx.Client(timeout=30.0) as client:
            for batch in _batches(texts):
                response = client.post(
                    _embedding_url(),
                    headers=_embedding_headers(),
                    json=_embedding_payload(batch),
                )
                response.raise_for_status()
                embeddings.extend(_parse_embeddings(response.json()))
        return embeddings
    except Exception as e:
        log.error("Failed to get embeddings (sync)", exc_info=True)
        raise ValueError(f"Failed to get embeddings: {e}")
