import pytest

from app.retrieval.embedder import embed_query, embed_texts, embed_texts_sync


class _FakeAsyncResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeAsyncClient:
    calls: list[dict] = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url, headers, json):
        self.calls.append({"url": url, "headers": headers, "json": json})
        data = [
            {"object": "embedding", "embedding": [0.1, 0.2, 0.3]},
            {"object": "embedding", "embedding": [0.4, 0.5, 0.6]},
        ][: len(json["input"])]
        return _FakeAsyncResponse({"object": "list", "data": data})


class _FakeSyncResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeSyncClient:
    calls: list[dict] = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def post(self, url, headers, json):
        self.calls.append({"url": url, "headers": headers, "json": json})
        return _FakeSyncResponse(
            {"object": "list", "data": [{"object": "embedding", "embedding": [0.1, 0.2, 0.3]}]}
        )


@pytest.mark.asyncio
async def test_embed_texts_async(monkeypatch):
    _FakeAsyncClient.calls = []
    monkeypatch.setattr("app.retrieval.embedder.httpx.AsyncClient", _FakeAsyncClient)

    texts = ["hello", "world"]
    embeddings = await embed_texts(texts)

    assert len(embeddings) == 2
    assert embeddings[0] == [0.1, 0.2, 0.3]
    assert embeddings[1] == [0.4, 0.5, 0.6]
    assert _FakeAsyncClient.calls[0]["json"]["input"] == texts


@pytest.mark.asyncio
async def test_embed_query_async(monkeypatch):
    _FakeAsyncClient.calls = []
    monkeypatch.setattr("app.retrieval.embedder.httpx.AsyncClient", _FakeAsyncClient)

    query = "search term"
    embedding = await embed_query(query)

    assert isinstance(embedding, list)
    assert embedding == [0.1, 0.2, 0.3]
    assert _FakeAsyncClient.calls[0]["json"]["input"] == [query]


def test_embed_texts_sync(monkeypatch):
    _FakeSyncClient.calls = []
    monkeypatch.setattr("app.retrieval.embedder.httpx.Client", _FakeSyncClient)

    texts = ["hello"]
    embeddings = embed_texts_sync(texts)

    assert len(embeddings) == 1
    assert embeddings[0] == [0.1, 0.2, 0.3]
    assert _FakeSyncClient.calls[0]["json"]["input"] == texts


@pytest.mark.asyncio
async def test_embed_empty(monkeypatch):
    _FakeAsyncClient.calls = []
    _FakeSyncClient.calls = []
    monkeypatch.setattr("app.retrieval.embedder.httpx.AsyncClient", _FakeAsyncClient)
    monkeypatch.setattr("app.retrieval.embedder.httpx.Client", _FakeSyncClient)

    embeddings = await embed_texts([])
    assert embeddings == []
    assert _FakeAsyncClient.calls == []

    sync_embeddings = embed_texts_sync([])
    assert sync_embeddings == []
    assert _FakeSyncClient.calls == []
