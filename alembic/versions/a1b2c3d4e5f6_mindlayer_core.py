"""MindLayer core schema — second-brain tables

Adds the new MindLayer tables for personal second brain:
  - memories                : the canonical "memory" storage unit
  - entities                : people, projects, topics, concepts
  - relations               : typed edges between entities
  - memory_entities         : many-to-many memory <-> entity with salience
  - sources                 : connected accounts (Drive, Notion, Gmail, etc.)
  - memory_sources          : many-to-many memory <-> source item

Revision ID: a1b2c3d4e5f6
Revises: 8c57eb4c9b80
Create Date: 2026-06-15 00:35:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "8c57eb4c9b80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── memories ──────────────────────────────────────────────────────────────
    op.create_table(
        "memories",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("memories.id", ondelete="CASCADE"), nullable=True),
        sa.Column("source_type", sa.String(32), nullable=False, server_default="manual_note"),
        sa.Column("source_ref", sa.String(500), nullable=True),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("tags", ARRAY(sa.String), nullable=False, server_default=sa.text("'{}'::varchar[]")),
        sa.Column("salience", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("captured_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("indexed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memories_user_id",       "memories", ["user_id"])
    op.create_index("ix_memories_parent_id",     "memories", ["parent_id"])
    op.create_index("ix_memories_user_captured", "memories", ["user_id", "captured_at"])
    op.create_index("ix_memories_user_salience", "memories", ["user_id", "salience"])
    op.create_index("ix_memories_source",        "memories", ["user_id", "source_type"])

    # ── entities ──────────────────────────────────────────────────────────────
    op.create_table(
        "entities",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False, server_default="other"),
        sa.Column("aliases", ARRAY(sa.String), nullable=False, server_default=sa.text("'{}'::varchar[]")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("first_seen_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("mention_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", "entity_type", name="uq_entities_user_name_type"),
    )
    op.create_index("ix_entities_user_id",          "entities", ["user_id"])
    op.create_index("ix_entities_user_type",        "entities", ["user_id", "entity_type"])
    op.create_index("ix_entities_user_last_seen",   "entities", ["user_id", "last_seen_at"])

    # ── relations ─────────────────────────────────────────────────────────────
    op.create_table(
        "relations",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_entity_id", UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_entity_id", UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation", sa.String(64), nullable=False, server_default="related_to"),
        sa.Column("weight", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_evidence_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "source_entity_id", "target_entity_id", "relation", name="uq_relations_user_pair_type"),
    )
    op.create_index("ix_relations_user_id",        "relations", ["user_id"])
    op.create_index("ix_relations_source_entity_id", "relations", ["source_entity_id"])
    op.create_index("ix_relations_target_entity_id", "relations", ["target_entity_id"])
    op.create_index("ix_relations_user_weight",    "relations", ["user_id", "weight"])

    # ── memory_entities (m2m) ─────────────────────────────────────────────────
    op.create_table(
        "memory_entities",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("memory_id", UUID(as_uuid=True), sa.ForeignKey("memories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("salience", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("memory_id", "entity_id", name="uq_memory_entity"),
    )
    op.create_index("ix_memory_entities_memory_id", "memory_entities", ["memory_id"])
    op.create_index("ix_memory_entities_entity_id", "memory_entities", ["entity_id"])

    # ── sources ───────────────────────────────────────────────────────────────
    op.create_table(
        "sources",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False, server_default="manual"),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("config", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False, server_default="connected"),
        sa.Column("last_sync_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("sync_cursor", sa.String(1000), nullable=True),
        sa.Column("sync_error", sa.Text(), nullable=True),
        sa.Column("memories_synced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "source_type", "display_name", name="uq_sources_user_type_name"),
    )
    op.create_index("ix_sources_user_id",        "sources", ["user_id"])
    op.create_index("ix_sources_user_status",    "sources", ["user_id", "status"])
    op.create_index("ix_sources_user_type",      "sources", ["user_id", "source_type"])

    # ── memory_sources (m2m) ──────────────────────────────────────────────────
    op.create_table(
        "memory_sources",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("memory_id", UUID(as_uuid=True), sa.ForeignKey("memories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_ref", sa.String(500), nullable=True),
        sa.Column("item_url", sa.String(1000), nullable=True),
        sa.Column("item_excerpt", sa.Text(), nullable=True),
        sa.Column("fetched_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("memory_id", "source_id", name="uq_memory_source"),
    )
    op.create_index("ix_memory_sources_memory_id", "memory_sources", ["memory_id"])
    op.create_index("ix_memory_sources_source_id", "memory_sources", ["source_id"])
    op.create_index("ix_memory_sources_source",    "memory_sources", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_memory_sources_source",        table_name="memory_sources")
    op.drop_index("ix_memory_sources_source_id",     table_name="memory_sources")
    op.drop_index("ix_memory_sources_memory_id",     table_name="memory_sources")
    op.drop_table("memory_sources")

    op.drop_index("ix_sources_user_type",            table_name="sources")
    op.drop_index("ix_sources_user_status",          table_name="sources")
    op.drop_index("ix_sources_user_id",              table_name="sources")
    op.drop_table("sources")

    op.drop_index("ix_memory_entities_entity_id",    table_name="memory_entities")
    op.drop_index("ix_memory_entities_memory_id",    table_name="memory_entities")
    op.drop_table("memory_entities")

    op.drop_index("ix_relations_user_weight",        table_name="relations")
    op.drop_index("ix_relations_target_entity_id",   table_name="relations")
    op.drop_index("ix_relations_source_entity_id",   table_name="relations")
    op.drop_index("ix_relations_user_id",            table_name="relations")
    op.drop_table("relations")

    op.drop_index("ix_entities_user_last_seen",      table_name="entities")
    op.drop_index("ix_entities_user_type",           table_name="entities")
    op.drop_index("ix_entities_user_id",             table_name="entities")
    op.drop_table("entities")

    op.drop_index("ix_memories_source",              table_name="memories")
    op.drop_index("ix_memories_user_salience",       table_name="memories")
    op.drop_index("ix_memories_user_captured",       table_name="memories")
    op.drop_index("ix_memories_parent_id",           table_name="memories")
    op.drop_index("ix_memories_user_id",             table_name="memories")
    op.drop_table("memories")
