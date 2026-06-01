"""
Memory model for MindLayer.

A "memory" is a single piece of knowledge captured into the user's
second brain. Memories can come from many sources (file upload, web
clip, Gmail, Google Drive, manual note) and live independently of any
single conversation.

Design notes:
    - `source_type` describes the origin family (file, drive, notion,
      gmail, web_clip, manual_note, conversation_excerpt).
    - `parent_id` allows a memory to be a sub-chunk of a larger memory
      (e.g. an extracted passage from a document).
    - `salience` is a float in [0, 1] that the system can update over
      time based on usage / recency. Used for ranking.
    - `captured_at` is the original event time (e.g. the email date,
      the file mtime). `indexed_at` is when MindLayer first stored it.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Text,
    Float,
    Boolean,
    TIMESTAMP,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.entity import MemoryEntity
    from app.models.source import MemorySource


class Memory(Base):
    __tablename__ = "memories"

    id:            Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id:       Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id:     Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=True, index=True)

    # Origin description
    source_type:   Mapped[str]       = mapped_column(String(32), nullable=False, server_default="manual_note")
    source_ref:    Mapped[str | None] = mapped_column(String(500), nullable=True)  # e.g. drive file id, url, message id
    source_url:    Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Content
    title:         Mapped[str | None] = mapped_column(String(500), nullable=True)
    content:       Mapped[str]        = mapped_column(Text, nullable=False)
    summary:       Mapped[str | None] = mapped_column(Text, nullable=True)
    tags:          Mapped[list[str]]  = mapped_column(ARRAY(String), server_default=text("'{}'::varchar[]"), nullable=False)

    # Scoring
    salience:      Mapped[float]      = mapped_column(Float, server_default="0.5", nullable=False)
    pinned:        Mapped[bool]        = mapped_column(Boolean(), server_default="false", nullable=False)

    # Time
    captured_at:   Mapped[datetime]   = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    indexed_at:    Mapped[datetime]   = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    updated_at:    Mapped[datetime]   = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow, nullable=False)

    # Free-form metadata
    extra_metadata: Mapped[dict]      = mapped_column("metadata", JSONB, server_default="{}", nullable=False)

    user:    Mapped["User"]              = relationship(back_populates="memories")
    parent:  Mapped["Memory | None"]     = relationship("Memory", remote_side="Memory.id", back_populates="children")
    children: Mapped[list["Memory"]]    = relationship("Memory", back_populates="parent", cascade="all, delete-orphan")
    entity_links: Mapped[list["MemoryEntity"]] = relationship(back_populates="memory", cascade="all, delete-orphan")
    source_links: Mapped[list["MemorySource"]] = relationship(back_populates="memory", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_memories_user_captured", "user_id", "captured_at"),
        Index("ix_memories_user_salience", "user_id", "salience"),
        Index("ix_memories_source", "user_id", "source_type"),
    )


__all__ = ["Memory"]
