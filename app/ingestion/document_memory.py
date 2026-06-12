"""Turn an ingested document into cross-conversation personal memories.

Part of the "unify the two worlds" work (roadmap P1.1). A document uploaded
into one conversation only lives in that conversation's per-conversation
vector index. To make it part of the user's second brain — recallable from
*any* conversation — we also project it into the ``memories`` table and the
shared ``mindlayer_memories`` vector collection.

Granularity = **hybrid** (1 document + N passages):

    Memory(kind="document")            title=filename, content=summary
      ├─ Memory(kind="passage")        parent_id=doc, content=parent chunk
      ├─ Memory(kind="passage")
      └─ ...                            one per parent chunk

The document-level row is a single handle the user sees in their memory list;
the passage rows give fine-grained, citable recall. ``document_chunks`` remains
the high-fidelity per-conversation citation layer — this is additive.

Linkage is by ``Memory.source_ref == document_id`` (there is no FK from Memory
to Document). All cleanup paths must therefore delete by that key; see
``delete_document_memories_sync`` and the async variant used by API deletes.

Runs in the **synchronous** Celery ingestion context.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.document import Document
from app.models.memory import Memory
from app.utils.chunker import ParentChunk

log = logging.getLogger(__name__)

DOC_MEMORY_SOURCE_TYPE = "file_upload"
_SUMMARY_MAX_CHARS = 1500


@dataclass
class DocMemoryResult:
    document_id: str
    doc_memory_id: str | None
    passage_memory_ids: list[str]
    # Ids of memories from a *prior* projection of this document that were
    # deleted (re-ingest). Callers purge their stale vectors from Chroma.
    removed_memory_ids: list[str] = field(default_factory=list)

    @property
    def all_ids(self) -> list[str]:
        ids = [self.doc_memory_id] if self.doc_memory_id else []
        ids.extend(self.passage_memory_ids)
        return ids

    @property
    def stale_vector_ids(self) -> list[str]:
        """Prior-projection ids that no longer have a Postgres row."""
        current = set(self.all_ids)
        return [i for i in self.removed_memory_ids if i not in current]


def _document_summary(parents: list[ParentChunk]) -> str:
    """Cheap summary = the first parent chunk, truncated. No extra LLM cost."""
    if not parents:
        return ""
    head = parents[0].content.strip()
    return head[:_SUMMARY_MAX_CHARS]


def delete_document_memories_sync(db: Session, document_id: str) -> list[str]:
    """Delete all memories derived from a document (sync). Returns deleted ids.

    Deletes by ``source_ref == document_id`` so both the document-level row and
    its passages are removed regardless of hierarchy. Caller commits.
    """
    rows = (
        db.execute(select(Memory).where(Memory.source_ref == document_id))
        .scalars()
        .all()
    )
    ids = [str(m.id) for m in rows]
    for mem in rows:
        db.delete(mem)
    return ids


async def delete_document_memories_async(db: AsyncSession, document_id: str) -> list[str]:
    """Async variant of :func:`delete_document_memories_sync`.

    Used by the API delete paths (document delete, conversation delete). Deletes
    the rows in Postgres and returns the ids so the caller can also purge the
    vector store. Caller commits.
    """
    rows = (
        await db.execute(select(Memory).where(Memory.source_ref == document_id))
    ).scalars().all()
    ids = [str(m.id) for m in rows]
    for mem in rows:
        await db.delete(mem)
    return ids


def build_document_memories_sync(
    db: Session,
    document_id: str,
    parents: list[ParentChunk],
) -> DocMemoryResult:
    """Create the document + passage memories for one ingested document.

    Idempotent: any memories previously derived from this document are deleted
    first, so re-ingestion replaces rather than duplicates. The caller is
    responsible for committing the session and for embedding the returned ids
    into the vector store.
    """
    doc = db.get(Document, document_id)
    if doc is None:
        log.warning("Doc→memory skipped: document not found", extra={"doc_id": document_id})
        return DocMemoryResult(document_id=document_id, doc_memory_id=None, passage_memory_ids=[])

    conversation = db.get(Conversation, doc.conversation_id)
    if conversation is None:
        log.warning("Doc→memory skipped: conversation not found", extra={"doc_id": document_id})
        return DocMemoryResult(document_id=document_id, doc_memory_id=None, passage_memory_ids=[])

    user_id = conversation.user_id

    # Idempotency: clear any prior projection of this document.
    removed_ids = delete_document_memories_sync(db, document_id)

    base_meta = {
        "document_id": document_id,
        "conversation_id": str(doc.conversation_id),
        "filename": doc.filename,
    }

    doc_memory = Memory(
        id=uuid.uuid4(),
        user_id=user_id,
        source_type=DOC_MEMORY_SOURCE_TYPE,
        source_ref=document_id,
        title=doc.filename,
        content=_document_summary(parents) or doc.filename,
        summary=None,
        tags=[],
        extra_metadata={**base_meta, "kind": "document"},
    )
    db.add(doc_memory)
    db.flush()  # need doc_memory.id for passage parent_id

    passage_ids: list[str] = []
    for parent in parents:
        passage = Memory(
            id=uuid.uuid4(),
            user_id=user_id,
            parent_id=doc_memory.id,
            source_type=DOC_MEMORY_SOURCE_TYPE,
            source_ref=document_id,
            title=doc.filename,
            content=parent.content,
            summary=None,
            tags=[],
            extra_metadata={
                **base_meta,
                "kind": "passage",
                "parent_chunk_id": parent.id,
                "parent_index": parent.index,
            },
        )
        db.add(passage)
        passage_ids.append(str(passage.id))

    db.flush()
    log.info(
        "Built document memories",
        extra={"doc_id": document_id, "passages": len(passage_ids)},
    )
    return DocMemoryResult(
        document_id=document_id,
        doc_memory_id=str(doc_memory.id),
        passage_memory_ids=passage_ids,
        removed_memory_ids=removed_ids,
    )


__all__ = [
    "DocMemoryResult",
    "build_document_memories_sync",
    "delete_document_memories_sync",
    "delete_document_memories_async",
    "DOC_MEMORY_SOURCE_TYPE",
]
