from types import SimpleNamespace

import pytest

from app.agents import answer_agent, evaluator_agent, hallucination_agent, router_agent
from app.agents.llm_parsing import parse_llm_json_object
from app.agents.state import AgentState
from app.retrieval import embedder, retrieval_cache
from app.retrieval.bm25_retriever import BM25Retriever

pytestmark = pytest.mark.rag


@pytest.mark.asyncio
async def test_bm25_lazy_ensure_rebuilds_missing_index(monkeypatch):
    retriever = BM25Retriever()

    async def fake_rebuild_async(db, conversation_id: str) -> None:
        retriever.build_from_parents(
            conversation_id,
            [
                {
                    "id": "parent-1",
                    "content": "API keys can be rotated from account settings.",
                    "metadata": {"filename": "api.md"},
                },
                {
                    "id": "parent-2",
                    "content": "Invoices are available from the billing dashboard.",
                    "metadata": {"filename": "billing.md"},
                },
                {
                    "id": "parent-3",
                    "content": "Webhook retries use exponential backoff.",
                    "metadata": {"filename": "webhooks.md"},
                }
            ],
        )

    monkeypatch.setattr(retriever, "rebuild_async", fake_rebuild_async)

    result = await retriever.ensure_async(db=object(), conversation_id="conv-1")

    assert result == {"had_index": False, "rebuilt": True, "has_index": True}
    hits = await retriever.search("rotated API keys", top_k=3, conversation_id="conv-1")
    assert hits
    assert hits[0]["parent_id"] == "parent-1"


@pytest.mark.asyncio
async def test_retrieval_cache_invalidation_removes_conversation_keys(monkeypatch):
    class FakeRedis:
        def __init__(self):
            self.keys = {
                "rag:query:conv:conv-1:a": "cached-a",
                "rag:query:conv:conv-1:b": "cached-b",
                "rag:query:conv:conv-2:c": "cached-c",
            }

        async def scan(self, cursor=0, match=None, count=100):
            prefix = match.removesuffix("*")
            keys = [key for key in self.keys if key.startswith(prefix)]
            return 0, keys

        async def delete(self, *keys):
            deleted = 0
            for key in keys:
                if key in self.keys:
                    deleted += 1
                    del self.keys[key]
            return deleted

    fake_redis = FakeRedis()

    async def fake_get_redis():
        return fake_redis

    monkeypatch.setattr(retrieval_cache, "get_redis", fake_get_redis)

    deleted = await retrieval_cache.invalidate_query_cache("conv-1")

    assert deleted == 2
    assert set(fake_redis.keys) == {"rag:query:conv:conv-2:c"}


@pytest.mark.asyncio
async def test_answer_agent_uses_safe_error_and_records_trace(monkeypatch):
    class FailingCompletions:
        async def create(self, **kwargs):
            raise RuntimeError("provider-secret-stacktrace")

    class FakeClient:
        chat = SimpleNamespace(completions=FailingCompletions())

    monkeypatch.setattr(answer_agent, "_get_client", lambda: FakeClient())

    state: AgentState = {
        "query": "How do I rotate an API key?",
        "query_type": "rag",
        "history": [],
        "reranked_chunks": [
            {"content": "Rotate keys in Settings.", "metadata": {"filename": "api.md"}}
        ],
        "agent_trace": {},
        "retry_count": 0,
    }

    result = await answer_agent.answer_agent(state)

    assert result["response"] == "Sorry, I couldn't generate an answer right now. Please try again."
    assert "provider-secret-stacktrace" not in result["response"]
    assert result["agent_trace"]["answer"]["error"] == "provider-secret-stacktrace"
    assert result["agent_trace"]["citation"] == {
        "has_citation": False,
        "source_count": 1,
        "required": True,
    }
    assert "latency_ms" in result["agent_trace"]["answer"]


def test_citation_trace_detects_source_marker():
    state: AgentState = {
        "query_type": "rag",
        "response": "Rotate keys in settings [Source 1].",
        "reranked_chunks": [{"content": "Rotate keys in settings."}],
        "agent_trace": {},
    }

    answer_agent._record_citation_trace(state)

    assert state["agent_trace"]["citation"]["has_citation"] is True
    assert state["agent_trace"]["citation"]["source_count"] == 1
    assert state["agent_trace"]["citation"]["required"] is True


@pytest.mark.asyncio
async def test_embed_texts_batches_and_preserves_order(monkeypatch):
    calls: list[list[str]] = []

    async def fake_create(model, input, encoding_format, timeout):
        assert encoding_format == "float"
        calls.append(list(input))
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=[float(text[-1])]) for text in input]
        )

    monkeypatch.setattr(embedder.settings, "EMBED_BATCH_SIZE", 2)
    monkeypatch.setattr(
        embedder.async_client,
        "embeddings",
        SimpleNamespace(create=fake_create),
    )

    embeddings = await embedder.embed_texts(["text-1", "text-2", "text-3"])

    assert calls == [["text-1", "text-2"], ["text-3"]]
    assert embeddings == [[1.0], [2.0], [3.0]]


@pytest.mark.asyncio
async def test_evaluator_warn_only_keeps_chunks_on_grader_error(monkeypatch):
    class FailingCompletions:
        async def create(self, **kwargs):
            raise RuntimeError("grader unavailable")

    class FakeClient:
        chat = SimpleNamespace(completions=FailingCompletions())

    monkeypatch.setattr(evaluator_agent.settings, "EVALUATOR_FAILURE_MODE", "warn_only")
    monkeypatch.setattr(evaluator_agent, "_get_client", lambda: FakeClient())

    state: AgentState = {
        "query": "How do I rotate an API key?",
        "query_type": "rag",
        "reranked_chunks": [{"content": "Rotate keys in Settings."}],
        "agent_trace": {},
    }

    result = await evaluator_agent.evaluator_agent(state)

    assert result["context_relevant"] is True
    assert result["reranked_chunks"] == [{"content": "Rotate keys in Settings."}]
    assert result["agent_trace"]["grade_docs"]["failure_mode"] == "warn_only"
    assert result["agent_trace"]["grade_docs"]["error_count"] == 1


@pytest.mark.asyncio
async def test_evaluator_fail_closed_filters_chunks_on_grader_error(monkeypatch):
    class FailingCompletions:
        async def create(self, **kwargs):
            raise RuntimeError("grader unavailable")

    class FakeClient:
        chat = SimpleNamespace(completions=FailingCompletions())

    monkeypatch.setattr(evaluator_agent.settings, "EVALUATOR_FAILURE_MODE", "fail_closed")
    monkeypatch.setattr(evaluator_agent, "_get_client", lambda: FakeClient())

    state: AgentState = {
        "query": "How do I rotate an API key?",
        "query_type": "rag",
        "reranked_chunks": [{"content": "Rotate keys in Settings."}],
        "agent_trace": {},
    }

    result = await evaluator_agent.evaluator_agent(state)

    assert result["context_relevant"] is False
    assert result["agent_trace"]["grade_docs"]["kept"] == 0
    assert result["agent_trace"]["grade_docs"]["failure_mode"] == "fail_closed"


def test_llm_json_parser_handles_fenced_json_and_none():
    parsed = parse_llm_json_object('```json\n{"score": "yes"}\n```')

    assert parsed.ok is True
    assert parsed.data == {"score": "yes"}

    empty = parse_llm_json_object(None)

    assert empty.ok is False
    assert empty.error == "empty_response"
    assert empty.raw_preview is None


@pytest.mark.asyncio
async def test_router_malformed_json_falls_back_with_trace(monkeypatch):
    class BadCompletions:
        async def create(self, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
            )

    class FakeClient:
        chat = SimpleNamespace(completions=BadCompletions())

    monkeypatch.setattr(router_agent, "_get_client", lambda: FakeClient())

    state: AgentState = {
        "query": "Which plan supports SSO?",
        "history": [],
        "has_documents": True,
        "agent_trace": {},
    }

    result = await router_agent.router_agent(state)

    assert result["query_type"] == "rag"
    assert result["search_variants"] == ["Which plan supports SSO?"]
    assert result["agent_trace"]["router"]["fallback_used"] is True
    assert result["agent_trace"]["router"]["error"] == "empty_response"


@pytest.mark.asyncio
async def test_evaluator_malformed_json_warn_only_keeps_chunks(monkeypatch):
    class BadCompletions:
        async def create(self, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="not json"))]
            )

    class FakeClient:
        chat = SimpleNamespace(completions=BadCompletions())

    monkeypatch.setattr(evaluator_agent.settings, "EVALUATOR_FAILURE_MODE", "warn_only")
    monkeypatch.setattr(evaluator_agent, "_get_client", lambda: FakeClient())

    state: AgentState = {
        "query": "Which plan supports SSO?",
        "query_type": "rag",
        "reranked_chunks": [{"content": "Enterprise supports SSO."}],
        "agent_trace": {},
    }

    result = await evaluator_agent.evaluator_agent(state)

    assert result["context_relevant"] is True
    assert result["reranked_chunks"] == [{"content": "Enterprise supports SSO."}]
    trace = result["agent_trace"]["grade_docs"]
    assert trace["fallback_used"] is True
    assert trace["error_count"] == 1


@pytest.mark.asyncio
async def test_hallucination_malformed_json_warn_only_fails_open(monkeypatch):
    class BadCompletions:
        async def create(self, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="not json"))]
            )

    class FakeClient:
        chat = SimpleNamespace(completions=BadCompletions())

    monkeypatch.setattr(hallucination_agent.settings, "EVALUATOR_FAILURE_MODE", "warn_only")
    monkeypatch.setattr(hallucination_agent, "_get_client", lambda: FakeClient())

    state: AgentState = {
        "query": "How do I rotate an API key?",
        "query_type": "rag",
        "response": "Rotate the key in Settings [Source 1].",
        "reranked_chunks": [{"content": "Rotate API keys in Settings."}],
        "agent_trace": {},
    }

    result = await hallucination_agent.hallucination_agent(state)

    assert result["is_hallucination"] is False
    assert result["answers_question"] is True
    assert result["agent_trace"]["hallucination"]["fallback_used"] is True


@pytest.mark.asyncio
async def test_hallucination_malformed_json_fail_closed_blocks_answer(monkeypatch):
    class BadCompletions:
        async def create(self, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="not json"))]
            )

    class FakeClient:
        chat = SimpleNamespace(completions=BadCompletions())

    monkeypatch.setattr(hallucination_agent.settings, "EVALUATOR_FAILURE_MODE", "fail_closed")
    monkeypatch.setattr(hallucination_agent, "_get_client", lambda: FakeClient())

    state: AgentState = {
        "query": "How do I rotate an API key?",
        "query_type": "rag",
        "response": "Rotate the key in Settings [Source 1].",
        "reranked_chunks": [{"content": "Rotate API keys in Settings."}],
        "agent_trace": {},
    }

    result = await hallucination_agent.hallucination_agent(state)

    assert result["is_hallucination"] is True
    assert result["answers_question"] is False
    assert result["agent_trace"]["hallucination"]["failure_mode"] == "fail_closed"
