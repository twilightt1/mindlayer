import logging
from openai import AsyncOpenAI, OpenAI
from app.config import settings

log = logging.getLogger(__name__)

async_client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY
)

sync_client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)


def _batches(texts: list[str]) -> list[list[str]]:
    batch_size = max(1, settings.EMBED_BATCH_SIZE)
    return [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    embeddings: list[list[float]] = []
    try:
        for batch in _batches(texts):
            response = await async_client.embeddings.create(
                model=settings.EMBED_MODEL,
                input=batch,
                timeout=30.0,
            )
            embeddings.extend(item.embedding for item in response.data)
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
        for batch in _batches(texts):
            response = sync_client.embeddings.create(
                model=settings.EMBED_MODEL,
                input=batch,
                timeout=30.0,
            )
            embeddings.extend(item.embedding for item in response.data)
        return embeddings
    except Exception as e:
        log.error("Failed to get embeddings (sync)", exc_info=True)
        raise ValueError(f"Failed to get embeddings: {e}")
