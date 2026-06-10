"""P1.3 tests: "save note" from chat.

CI-safe: the router LLM path is not exercised (regex fast-paths + pure
validation only); the save_note node's DB + embedding are mocked.
"""
from __future__ import annotations

import pytest

from app.agents.memory_agent import (
    _note_title,
    _strip_save_trigger,
    memory_save_note_agent,
)
from app.agents.routing import route_from_router
from app.agents.state import AgentState

pytestmark = pytest.mark.rag


# ── routing ──────────────────────────────────────────────────────────────────


def test_route_from_router_passes_save_note_through():
    assert route_from_router({"query_type": "save_note"}) == "save_note"


# ── trigger stripping / title ────────────────────────────────────────────────


class TestStripTrigger:
    @pytest.mark.parametrize(
        "query,expected",
        [
            ("remember that my wifi is hunter2", "my wifi is hunter2"),
            ("Remember to call mom", "call mom"),
            ("note: buy milk", "buy milk"),
            ("save this note: project deadline friday", "project deadline friday"),
            ("ghi nhớ mua sữa", "mua sữa"),
            ("lưu lại: họp lúc 3h", "họp lúc 3h"),
            ("just some plain text", "just some plain text"),  # no trigger → unchanged
        ],
    )
    def test_strip(self, query, expected):
        assert _strip_save_trigger(query) == expected

    def test_title_truncates(self):
        long = "x" * 200
        title = _note_title(long)
        assert len(title) <= 80
        assert title.endswith("...")

    def test_title_first_line(self):
        assert _note_title("first line\nsecond line") == "first line"


# ── save_note node ───────────────────────────────────────────────────────────


@pytest.fixture
def fake_memory_infra(monkeypatch):
    """Patch AsyncSessionLocal + index_new_memory so the node runs offline."""
    created = {}

    class FakeDB:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        def add(self, obj):
            created["memory"] = obj

        async def commit(self):
            pass

        async def refresh(self, obj):
            import uuid as _uuid

            if getattr(obj, "id", None) is None:
                obj.id = _uuid.uuid4()

    # app.database.AsyncSessionLocal is imported *inside* the node, so patch it
    # on the source module.
    import app.database as database

    monkeypatch.setattr(database, "AsyncSessionLocal", lambda: FakeDB())

    indexed = {}

    async def fake_index(memory):
        indexed["memory"] = memory

    # index_new_memory is imported inside the node from write_back; patch source.
    import app.retrieval.memory.write_back as wb

    monkeypatch.setattr(wb, "index_new_memory", fake_index)

    return created, indexed


def _state(query: str) -> AgentState:
    return AgentState(
        user_id="00000000-0000-0000-0000-000000000001",
        conversation_id="00000000-0000-0000-0000-000000000002",
        query=query,
        agent_trace={},
    )


@pytest.mark.asyncio
async def test_save_note_creates_memory_and_confirms(fake_memory_infra):
    created, indexed = fake_memory_infra
    state = _state("remember that the wifi password is hunter2")

    out = await memory_save_note_agent(state)

    # A memory was created with the stripped content + chat_note tag.
    mem = created["memory"]
    assert mem.content == "the wifi password is hunter2"
    assert mem.source_type == "conversation_excerpt"
    assert "chat_note" in mem.tags
    # It was handed to the indexing pipeline (embed + graph).
    assert indexed["memory"] is mem
    # A confirmation response was set, and the trace marks it saved.
    assert "Saved to your memory" in out["response"]
    assert out["agent_trace"]["save_note"]["saved"] is True


@pytest.mark.asyncio
async def test_save_note_empty_content_asks_for_note(fake_memory_infra):
    created, indexed = fake_memory_infra
    state = _state("remember that")  # nothing after the trigger

    out = await memory_save_note_agent(state)

    assert "memory" not in created  # no memory created
    assert "memory" not in indexed
    assert out["agent_trace"]["save_note"]["saved"] is False
    assert out["agent_trace"]["save_note"]["reason"] == "empty_content"
    assert "What would you like me to remember" in out["response"]


@pytest.mark.asyncio
async def test_save_note_vietnamese_confirmation(fake_memory_infra):
    state = _state("ghi nhớ mua sữa cho con")

    out = await memory_save_note_agent(state)

    # Confirmation should be in Vietnamese for a Vietnamese note.
    assert "Đã lưu" in out["response"]
    assert out["agent_trace"]["save_note"]["saved"] is True


@pytest.mark.asyncio
async def test_save_note_streams_confirmation(fake_memory_infra):
    state = _state("note: deploy on friday")
    streamed = []

    async def cb(delta):
        streamed.append(delta)

    state["_stream_callback"] = cb

    await memory_save_note_agent(state)

    assert streamed and "Saved to your memory" in "".join(streamed)
