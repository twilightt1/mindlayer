import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, TIMESTAMP, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import GUID

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class Message(Base):
    __tablename__ = "messages"

    id:              Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role:            Mapped[str]       = mapped_column(String(20), nullable=False)
    content:         Mapped[str]       = mapped_column(Text, nullable=False)
    agent_trace:     Mapped[dict]      = mapped_column(JSON, server_default="{}")
    token_count:     Mapped[int|None]  = mapped_column(Integer(), nullable=True)
    created_at:      Mapped[datetime]  = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_messages_role_created", "role", "created_at"),
    )
