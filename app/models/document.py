import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models._datetime_helpers import utc_now
from app.models.types import GUID

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.document_chunk import DocumentChunk


class Document(Base):
    __tablename__ = "documents"

    id:              Mapped[uuid.UUID]    = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID]    = mapped_column(GUID(), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    filename:        Mapped[str]          = mapped_column(String(500), nullable=False)
    file_path:       Mapped[str]          = mapped_column(String(1000), nullable=False)
    file_size:       Mapped[int|None]     = mapped_column(BigInteger, nullable=True)
    mime_type:       Mapped[str|None]     = mapped_column(String(100), nullable=True)
    status:          Mapped[str]          = mapped_column(String(20), server_default="pending")
    chunk_count:     Mapped[int]          = mapped_column(Integer(), default=0)
    error_msg:       Mapped[str|None]     = mapped_column(Text, nullable=True)
    created_at:      Mapped[datetime]     = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime]     = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=utc_now)

    conversation: Mapped["Conversation"]        = relationship(back_populates="documents")
    chunks:       Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_documents_conversation_status", "conversation_id", "status"),
    )
