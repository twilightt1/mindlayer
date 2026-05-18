"""
Source model for MindLayer.

A "source" is a connected account or feed that the user has authorized
MindLayer to pull memories from. Examples:
    - Google Drive folder or file
    - Notion workspace / database / page
    - Gmail mailbox or label
    - Web clipper bookmarked list
    - Manual (when the user just types a note in MindLayer)

`config` stores connection-specific settings (encrypted at rest in a
later phase). For Phase 1 we just keep it as JSONB.

`status` tracks the connector health: connected, syncing, error, paused.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Text,
    Integer,
    TIMESTAMP,
    ForeignKey,
    UniqueConstraint,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.memory import Memory


SOURCE_TYPES = (
    "manual",
    "file_upload",
    "google_drive",
    "notion",
    "gmail",
    "web_clipper",
    "rss",
    "calendar",
    "twitter",
    "other",
)

SOURCE_STATUS = (
    "connected",
    "syncing",
    "error",
    "paused",
    "disconnected",
)


class Source(Base):
    __tablename__ = "sources"

    id:            Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id:       Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    source_type:   Mapped[str]       = mapped_column(String(32), nullable=False, server_default="manual")
    display_name:  Mapped[str]       = mapped_column(String(255), nullable=False)
    description:   Mapped[str | None] = mapped_column(Text, nullable=True)

    # Connector configuration (auth tokens, folder ids, etc.)
    # Phase 1: stored as plain JSONB. Phase 7+: encrypted at rest.
    config:        Mapped[dict]      = mapped_column(JSONB, server_default="{}", nullable=False)

    # Sync state
    status:        Mapped[str]       = mapped_column(String(20), nullable=False, server_default="connected")
    last_sync_at:  Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    sync_cursor:   Mapped[str | None] = mapped_column(String(1000), nullable=True)  # opaque cursor for incremental sync
    sync_error:    Mapped[str | None] = mapped_column(Text, nullable=True)
    memories_synced: Mapped[int]     = mapped_column(Integer(), server_default="0", nullable=False)

    extra_metadata: Mapped[dict]      = mapped_column("metadata", JSONB, server_default="{}", nullable=False)
    created_at:    Mapped[datetime]   = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    updated_at:    Mapped[datetime]   = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow, nullable=False)

    user:        Mapped["User"]                       = relationship(back_populates="sources")
    memory_links: Mapped[list["MemorySource"]]        = relationship(back_populates="source", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "source_type", "display_name", name="uq_sources_user_type_name"),
        Index("ix_sources_user_status", "user_id", "status"),
        Index("ix_sources_user_type", "user_id", "source_type"),
    )


class MemorySource(Base):
    """
    Many-to-many link between a memory and the source that produced it.
    Captures the original item id (file id, message id, url) so we can
    navigate back to the source.
    """

    __tablename__ = "memory_sources"

    id:             Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    memory_id:      Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id:      Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)

    item_ref:     Mapped[str | None] = mapped_column(String(500), nullable=True)  # the remote id of the item
    item_url:     Mapped[str | None] = mapped_column(String(1000), nullable=True)
    item_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)        # short snippet from the source

    fetched_at:     Mapped[datetime]   = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    extra_metadata: Mapped[dict]       = mapped_column("metadata", JSONB, server_default="{}", nullable=False)

    memory: Mapped["Memory"] = relationship(back_populates="source_links")
    source: Mapped["Source"] = relationship(back_populates="memory_links")

    __table_args__ = (
        UniqueConstraint("memory_id", "source_id", name="uq_memory_source"),
        Index("ix_memory_sources_source", "source_id"),
    )


__all__ = ["Source", "MemorySource", "SOURCE_TYPES", "SOURCE_STATUS"]
