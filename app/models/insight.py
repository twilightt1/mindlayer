"""
InsightCard model for Orivory.

Stores discovered insights from "What I Didn't Know I Knew" feature.
Proactively surfaces hidden connections and patterns from user's documents.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InsightTypeEnum(StrEnum):
    """Insight type enumeration for database storage."""
    CONNECTION = "connection"
    CONTRADICTION = "contradiction"
    EVOLUTION = "evolution"
    PATTERN = "pattern"
    GAP = "gap"
    CONFIRMATION = "confirmation"
    SYNTHESIS = "synthesis"


class InsightSurpriseLevelEnum(StrEnum):
    """Surprise level for database storage."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InsightStatusEnum(StrEnum):
    """Insight status for database storage."""
    NEW = "new"
    SHOWN = "shown"
    DISMISSED = "dismissed"
    SAVED = "saved"
    EXPIRED = "expired"


class InsightCard(Base):
    """Insight card model for proactive discovery feature."""

    __tablename__ = "insight_cards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # Ownership
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Insight content
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    insight_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="connection",
    )
    summary: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )
    detail: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    # Source documents (JSON array of document references)
    source_docs: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
    )
    source_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
    )

    # Metadata
    surprise_level: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default="medium",
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        server_default="0.5",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("NOW()"),
        index=True,
    )
    shown_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
    )
    dismissed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="new",
        index=True,
    )

    # User feedback
    helpful: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    feedback_note: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    # Analytics
    shown_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    relevance_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        server_default="0.5",
    )

    # Learned preferences (JSONB for flexibility)
    user_preferences_snapshot: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_insight_cards_user_created", "user_id", "created_at"),
        Index("ix_insight_cards_user_status", "user_id", "status"),
        Index("ix_insight_cards_user_type", "user_id", "insight_type"),
        Index("ix_insight_cards_user_relevance", "user_id", "relevance_score"),
    )

    def __repr__(self) -> str:
        return f"<InsightCard {self.id} type={self.insight_type} status={self.status}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "insight_type": self.insight_type,
            "summary": self.summary,
            "detail": self.detail,
            "source_docs": self.source_docs,
            "source_count": self.source_count,
            "surprise_level": self.surprise_level,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "shown_at": self.shown_at.isoformat() if self.shown_at else None,
            "dismissed_at": self.dismissed_at.isoformat() if self.dismissed_at else None,
            "status": self.status,
            "helpful": self.helpful,
            "feedback_note": self.feedback_note,
            "shown_count": self.shown_count,
            "relevance_score": self.relevance_score,
        }

    @property
    def type_emoji(self) -> str:
        """Get emoji for insight type."""
        emoji_map = {
            "connection": "🔗",
            "contradiction": "⚡",
            "evolution": "📈",
            "pattern": "🔄",
            "gap": "❓",
            "confirmation": "✅",
            "synthesis": "💡",
        }
        return emoji_map.get(self.insight_type, "💡")

    @property
    def display_title(self) -> str:
        """Get title with emoji prefix."""
        return f"{self.type_emoji} {self.title}"
