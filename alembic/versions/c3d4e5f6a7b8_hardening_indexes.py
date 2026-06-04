"""Hardening indexes (P4)

Adds indexes for common query patterns that previously did sequential scans:

  - documents(conversation_id, status)   — "ready docs in conversation X"
  - memories USING gin (tags)            — tag containment (@>, &&) filters
  - memory_sources(source_id, item_ref)  — connector dedup lookup
  - messages(role, created_at)           — the quality-trend aggregation (P3)

All additive and safe; no data change.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-17 00:30:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_documents_conversation_status", "documents", ["conversation_id", "status"]
    )
    op.create_index(
        "ix_memories_tags", "memories", ["tags"], postgresql_using="gin"
    )
    op.create_index(
        "ix_memory_sources_source_item", "memory_sources", ["source_id", "item_ref"]
    )
    op.create_index(
        "ix_messages_role_created", "messages", ["role", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_messages_role_created", table_name="messages")
    op.drop_index("ix_memory_sources_source_item", table_name="memory_sources")
    op.drop_index("ix_memories_tags", table_name="memories")
    op.drop_index("ix_documents_conversation_status", table_name="documents")
