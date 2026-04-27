from types import SimpleNamespace

import pytest

from app.retrieval import embedder
from app.retrieval.embedder import embed_query, embed_texts, embed_texts_sync


class _FakeAsyncEmbeddings:
    def __init__(self):
        self.calls: list[dict] = []

    async def create(self, model, input, encoding_format, timeout):
        self.calls.append(
            {
                "model": model,
                "input": input,
                "encoding_format": encoding_format,
                "timeout": timeout,
            }
        )
        data = [
            SimpleNamespace(embedding=[0.1, 0.2, 0.3]),
            SimpleNamespace(embedding=[0.4, 0.5, 0.6]),
        ][: len(input)]
        return SimpleNamespace(data=data)


class _FakeSyncEmbeddings:
    def __init__(self):
        self.calls: list[dict] = []

    def create(self, model, input, encoding_format, timeout):
        self.calls.append(
            {
                "model": model,
                "input": input,
                "encoding_format": encoding_format,
                "timeout": timeout,
            }
        )
        return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2, 0.3])])


@pytest.mark.asyncio
async def test_embed_texts_async(monkeypatch):
    fake_embeddings = _FakeAsyncEmbeddings()
    monkeypatch.setattr(embedder.async_client, "embeddings", fake_embeddings)

    texts = ["hello", "world"]
    embeddings = await embed_texts(texts)

    assert len(embeddings) == 2
    assert embeddings[0] == [0.1, 0.2, 0.3]
    assert embeddings[1] == [0.4, 0.5, 0.6]
    assert fake_embeddings.calls[0]["input"] == texts
    assert fake_embeddings.calls[0]["encoding_format"] == "float"
    assert fake_embeddings.calls[0]["timeout"] == 30.0


@pytest.mark.asyncio
async def test_embed_query_async(monkeypatch):
    fake_embeddings = _FakeAsyncEmbeddings()
    monkeypatch.setattr(embedder.async_client, "embeddings", fake_embeddings)

    query = "search term"
    embedding = await embed_query(query)

    assert isinstance(embedding, list)
    assert embedding == [0.1, 0.2, 0.3]
    assert fake_embeddings.calls[0]["input"] == [query]


def test_embed_texts_sync(monkeypatch):
    fake_embeddings = _FakeSyncEmbeddings()
    monkeypatch.setattr(embedder.sync_client, "embeddings", fake_embeddings)

    texts = ["hello"]
    embeddings = embed_texts_sync(texts)

    assert len(embeddings) == 1
    assert embeddings[0] == [0.1, 0.2, 0.3]
    assert fake_embeddings.calls[0]["input"] == texts
    assert fake_embeddings.calls[0]["encoding_format"] == "float"
    assert fake_embeddings.calls[0]["timeout"] == 30.0


@pytest.mark.asyncio
async def test_embed_empty(monkeypatch):
    fake_async_embeddings = _FakeAsyncEmbeddings()
    fake_sync_embeddings = _FakeSyncEmbeddings()
    monkeypatch.setattr(embedder.async_client, "embeddings", fake_async_embeddings)
    monkeypatch.setattr(embedder.sync_client, "embeddings", fake_sync_embeddings)

    embeddings = await embed_texts([])
    assert embeddings == []
    assert fake_async_embeddings.calls == []

    sync_embeddings = embed_texts_sync([])
    assert sync_embeddings == []
    assert fake_sync_embeddings.calls == []
