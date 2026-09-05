"""
Feedback model for Orivory.

Stores user feedback on RAG answers for continuous improvement.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.types import GUID


class Feedback(Base):
    """User feedback on RAG answers."""

    __tablename__ = "feedbacks"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
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
        JSON,
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
        server_default=func.now(),
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
