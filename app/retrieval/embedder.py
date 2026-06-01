import logging

from openai import AsyncOpenAI, OpenAI

from app.config import settings

log = logging.getLogger(__name__)


# Lazily-resolved module-level aliases.
# Tests commonly ``monkeypatch.setattr(embedder, "async_client", fake)`` or
# patch ``embedder.async_client.embeddings`` to inject fakes. By exposing
# these names through a module __getattr__, callers can treat them as
# normal module attributes while we still defer client construction until
# the first real access. Patching the module attribute via setattr will
# shadow the lazy resolver for the patched value, just as with a regular
# module attribute.
def __getattr__(name):
    if name == "async_client":
        return _get_async_client()
    if name == "sync_client":
        return _get_sync_client()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


_async_client: AsyncOpenAI | None = None
_sync_client: OpenAI | None = None


def _get_async_client() -> AsyncOpenAI:
    """Lazily construct the async OpenAI client.

    Delayed initialization keeps the module importable in test/CLI contexts
    that do not have LLM credentials available.
    """
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": settings.FRONTEND_URL,
                "X-Title": "MindLayer",
            },
        )
    return _async_client


def _get_sync_client() -> OpenAI:
    """Lazily construct the sync OpenAI client."""
    global _sync_client
    if _sync_client is None:
        _sync_client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": settings.FRONTEND_URL,
                "X-Title": "MindLayer",
            },
        )
    return _sync_client


# Module-level aliases. Resolution is lazy via __getattr__ above; we do not
# eagerly bind names so that test code can also ``setattr(embedder,
# "async_client", fake)`` to fully override the client. The first real
# access constructs and caches the singleton via _get_async_client() /
# _get_sync_client().


def _batches(texts: list[str]) -> list[list[str]]:
    batch_size = max(1, settings.EMBED_BATCH_SIZE)
    return [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    embeddings: list[list[float]] = []
    try:
        client = _get_async_client()
        for batch in _batches(texts):
            response = await client.embeddings.create(
                model=settings.EMBED_MODEL,
                input=batch,
                encoding_format="float",
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
        client = _get_sync_client()
        for batch in _batches(texts):
            response = client.embeddings.create(
                model=settings.EMBED_MODEL,
                input=batch,
                encoding_format="float",
                timeout=30.0,
            )
            embeddings.extend(item.embedding for item in response.data)
        return embeddings
    except Exception as e:
        log.error("Failed to get embeddings (sync)", exc_info=True)
        raise ValueError(f"Failed to get embeddings: {e}")
