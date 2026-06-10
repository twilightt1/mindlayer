"""P1.1 unify tests: documents project into cross-conversation memories.

CI-safe: uses a fake sync Session (no Postgres) to verify the *shape* and
*idempotency* of the doc→memory builder. The DB-backed integration is covered
by the live integration suite.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.ingestion.document_memory import (
    DOC_MEMORY_SOURCE_TYPE,
    build_document_memories_sync,
)
from app.models.memory import Memory
from app.utils.chunker import ParentChunk

pytestmark = pytest.mark.rag


class FakeSession:
    """Minimal stand-in for a sync SQLAlchemy Session."""

    def __init__(self, doc, conversation, existing_memories=None):
        self._doc = doc
        self._conversation = conversation
        self.added: list = []
        self.deleted: list = []
        self._existing = list(existing_memories or [])

    def get(self, model, pk):
        from app.models.conversation import Conversation
        from app.models.document import Document

        if model is Document:
            return self._doc if str(self._doc.id) == str(pk) else None
        if model is Conversation:
            return self._conversation if str(self._conversation.id) == str(pk) else None
        return None

    def add(self, obj):
        self.added.append(obj)

    def delete(self, obj):
        self.deleted.append(obj)

    def flush(self):
        # Assign ids the way the DB server_default would, so parent_id wiring
        # can be asserted. Real Memory() already gets a uuid in our builder.
        pass

    def execute(self, stmt):
        # Used only by delete_document_memories_sync for the "existing" lookup.
        rows = self._existing

        class _Result:
            def __init__(self, items):
                self._items = items

            def scalars(self):
                return self

            def all(self):
                return self._items

        # First call returns ids (select(Memory.id)), second returns Memory rows.
        # Our builder calls select(Memory.id) then select(Memory); return rows
        # for both — scalars().all() shape is compatible.
        return _Result(rows)


def _doc():
    return SimpleNamespace(
        id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        filename="report.pdf",
    )


def _parents(n):
    return [
        ParentChunk(id=str(uuid.uuid4()), content=f"Parent {i} content body.", index=i)
        for i in range(n)
    ]


def test_builds_one_doc_plus_n_passages():
    doc = _doc()
    conv = SimpleNamespace(id=doc.conversation_id, user_id=uuid.uuid4())
    session = FakeSession(doc, conv)

    parents = _parents(3)
    result = build_document_memories_sync(session, str(doc.id), parents)

    # 1 doc memory + 3 passages created
    assert result.doc_memory_id is not None
    assert len(result.passage_memory_ids) == 3
    assert len(result.all_ids) == 4

    created = [o for o in session.added if isinstance(o, Memory)]
    assert len(created) == 4

    doc_rows = [m for m in created if m.extra_metadata.get("kind") == "document"]
    passage_rows = [m for m in created if m.extra_metadata.get("kind") == "passage"]
    assert len(doc_rows) == 1
    assert len(passage_rows) == 3


def test_passages_link_to_doc_memory_via_parent_id():
    doc = _doc()
    conv = SimpleNamespace(id=doc.conversation_id, user_id=uuid.uuid4())
    session = FakeSession(doc, conv)

    result = build_document_memories_sync(session, str(doc.id), _parents(2))

    created = [o for o in session.added if isinstance(o, Memory)]
    doc_mem = next(m for m in created if m.extra_metadata.get("kind") == "document")
    passages = [m for m in created if m.extra_metadata.get("kind") == "passage"]

    assert str(doc_mem.id) == result.doc_memory_id
    for p in passages:
        assert p.parent_id == doc_mem.id  # passage hangs off the doc memory


def test_all_memories_carry_document_linkage():
    doc = _doc()
    conv = SimpleNamespace(id=doc.conversation_id, user_id=uuid.uuid4())
    session = FakeSession(doc, conv)

    build_document_memories_sync(session, str(doc.id), _parents(2))
    created = [o for o in session.added if isinstance(o, Memory)]

    for m in created:
        assert m.source_ref == str(doc.id)           # linkage key for cleanup
        assert m.source_type == DOC_MEMORY_SOURCE_TYPE
        assert m.user_id == conv.user_id             # user resolved via conversation
        assert m.extra_metadata["document_id"] == str(doc.id)


def test_idempotent_reingest_deletes_prior_memories():
    doc = _doc()
    conv = SimpleNamespace(id=doc.conversation_id, user_id=uuid.uuid4())
    # Two memories from a previous ingestion of the same document.
    prior = [
        Memory(id=uuid.uuid4(), user_id=conv.user_id, source_ref=str(doc.id),
               source_type=DOC_MEMORY_SOURCE_TYPE, content="old", extra_metadata={}),
        Memory(id=uuid.uuid4(), user_id=conv.user_id, source_ref=str(doc.id),
               source_type=DOC_MEMORY_SOURCE_TYPE, content="old2", extra_metadata={}),
    ]
    session = FakeSession(doc, conv, existing_memories=prior)

    result = build_document_memories_sync(session, str(doc.id), _parents(1))

    # Prior memories were deleted before new ones were added.
    assert len(session.deleted) == 2
    assert set(session.deleted) == set(prior)

    # Prior ids are reported as stale vectors to purge, and none overlap the
    # freshly created ids (new rows get new uuids).
    prior_ids = {str(p.id) for p in prior}
    assert set(result.removed_memory_ids) == prior_ids
    assert set(result.stale_vector_ids) == prior_ids
    assert not (set(result.all_ids) & prior_ids)


def test_skips_when_document_missing():
    doc = _doc()
    conv = SimpleNamespace(id=doc.conversation_id, user_id=uuid.uuid4())
    session = FakeSession(doc, conv)

    # Ask for a different document id → builder finds no Document → no-op.
    result = build_document_memories_sync(session, str(uuid.uuid4()), _parents(2))
    assert result.doc_memory_id is None
    assert result.passage_memory_ids == []
    assert not session.added
