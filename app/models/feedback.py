"""
Feedback model for MindLayer.

Stores user feedback on RAG answers for continuous improvement.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Integer,
    TIMESTAMP,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Feedback(Base):
    """User feedback on RAG answers."""
    
    __tablename__ = "feedbacks"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Feedback type: positive, negative, correction, citation, ignored
    feedback_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="positive",
    )
    
    # Anonymized query hash for pattern analysis
    query_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    
    # Document IDs that were used in the answer
    doc_ids: Mapped[list[str]] = mapped_column(
        ARRAY(String(128)),
        nullable=False,
        server_default="{}",
    )
    
    # Optional user-provided content (for corrections)
    content: Mapped[str | None] = mapped_column(
        String(5000),
        nullable=True,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("NOW()"),
        index=True,
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_feedbacks_user_created", "user_id", "created_at"),
        Index("ix_feedbacks_conversation_created", "conversation_id", "created_at"),
        Index("ix_feedbacks_type_created", "feedback_type", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Feedback {self.id} type={self.feedback_type}>"
