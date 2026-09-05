import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models._datetime_helpers import utc_now
from app.models.types import GUID

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.message import Message
    from app.models.user import User


class Conversation(Base):
    __tablename__ = "conversations"

    id:             Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id:        Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title:          Mapped[str]       = mapped_column(String(500), server_default="New Conversation")
    document_count: Mapped[int]       = mapped_column(Integer(), default=0)
    created_at:     Mapped[datetime]  = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:     Mapped[datetime]  = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=utc_now)

    user:      Mapped["User"]           = relationship(back_populates="conversations")
    messages:  Mapped[list["Message"]]  = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    documents: Mapped[list["Document"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="Document.created_at")
