from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1 import chat
from app.main import app

pytestmark = pytest.mark.api


class _FakeGraph:
    async def astream(self, state):
        yield {"router": {"query_type": "rag", "retry_count": 0}}
        yield {"retrieval": {"retry_count": 0, "reranked_chunks": []}}
        await state["_stream_callback"]("Hello")
        await state["_stream_callback"](" world")
        yield {
            "answer": {
                "response": "Hello world",
                "token_count": 2,
                "agent_trace": {"answer": {"model": "test-model"}},
            }
        }
        yield {
            "save": {
                "response": "Hello world",
                "token_count": 2,
                "agent_trace": {"answer": {"model": "test-model"}},
                "reranked_chunks": [
                    {
                        "content": "SupportMind streams responses token by token.",
                        "metadata": {"filename": "streaming.md"},
                        "rerank_score": 0.98765,
                    }
                ],
            }
        }


class _RetryGraph:
    async def astream(self, state):
        yield {"answer": {"response": "draft", "retry_count": 0}}
        state["retry_count"] = 1
        yield {"retry_answer_for_hallucination": {"retry_count": 1}}
        await state["_stream_callback"]("grounded")
        yield {"answer": {"response": "grounded", "retry_count": 1}}
        yield {"save": {"response": "grounded", "retry_count": 1, "reranked_chunks": []}}


class _ErrorGraph:
    async def astream(self, state):
        yield {"router": {"query_type": "rag"}}
        raise RuntimeError("boom")


def _parse_sse_frames(text: str) -> list[dict[str, str]]:
    frames = []
    for raw_frame in text.strip().split("\n\n"):
        frame: dict[str, str] = {}
        for line in raw_frame.splitlines():
            if line.startswith("event: "):
                frame["event"] = line.removeprefix("event: ")
            elif line.startswith("data: "):
                frame["data"] = line.removeprefix("data: ")
        if frame:
            frames.append(frame)
    return frames


@pytest.fixture
def chat_stream_overrides(monkeypatch):
    user = type("User", (), {"id": "11111111-1111-1111-1111-111111111111"})()
    conversation = type(
        "Conversation",
        (),
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "user_id": user.id,
            "document_count": 1,
        },
    )()

    async def current_user_override():
        return user

    async def conversation_override():
        return conversation

    async def db_override():
        yield object()

    async def noop_rate_limit(*args, **kwargs):
        return None

    async def noop_quota(*args, **kwargs):
        return None

    app.dependency_overrides[chat.get_current_active_user] = current_user_override
    app.dependency_overrides[chat._get_conversation] = conversation_override
    app.dependency_overrides[chat.get_db] = db_override
    monkeypatch.setattr(chat, "check_rate_limit", noop_rate_limit)
    monkeypatch.setattr(chat, "check_and_increment", noop_quota)

    yield conversation

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_stream_emits_status_tokens_sources_trace_and_done(
    monkeypatch,
    chat_stream_overrides,
):
    monkeypatch.setattr(chat, "rag_graph", _FakeGraph())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/chat/conversations/{chat_stream_overrides.id}/message",
            json={"query": "How does streaming work?"},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    frames = _parse_sse_frames(response.text)
    event_names = [frame["event"] for frame in frames]

    assert "status" in event_names
    assert event_names.count("token") == 1
    assert "sources" in event_names
    assert "trace" in event_names
    assert event_names[-1] == "done"
    assert '"content":"Hello world"' in response.text
    assert '"mode":"final_evaluated_response"' in response.text
    assert '"filename":"streaming.md"' in response.text


@pytest.mark.asyncio
async def test_chat_stream_retry_status_includes_retry_metadata(
    monkeypatch,
    chat_stream_overrides,
):
    monkeypatch.setattr(chat, "rag_graph", _RetryGraph())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/chat/conversations/{chat_stream_overrides.id}/message",
            json={"query": "Give me a grounded answer."},
        )

    assert response.status_code == 200
    assert '"stage":"retry_answer_for_hallucination"' in response.text
    assert '"category":"retry"' in response.text
    assert '"retry_count":1' in response.text
    assert '"attempt":2' in response.text
    assert '"content":"grounded"' in response.text
    assert '"content":"draft"' not in response.text


@pytest.mark.asyncio
async def test_chat_stream_emits_error_event_when_graph_fails(
    monkeypatch,
    chat_stream_overrides,
):
    monkeypatch.setattr(chat, "rag_graph", _ErrorGraph())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/chat/conversations/{chat_stream_overrides.id}/message",
            json={"query": "Trigger an error."},
        )

    assert response.status_code == 200
    frames = _parse_sse_frames(response.text)

    assert frames[-1]["event"] == "error"
    assert frames[-1]["data"] == '{"type":"error","message":"An error occurred."}'
