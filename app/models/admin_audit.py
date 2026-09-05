import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, TIMESTAMP, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import GUID

if TYPE_CHECKING:
    from app.models.user import User


class AdminActionLog(Base):
    __tablename__ = "admin_audit_logs"

    id:                 Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    admin_id:           Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    target_entity_type: Mapped[str]       = mapped_column(String(50), nullable=False)
    target_entity_id:   Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    action:             Mapped[str]       = mapped_column(String(50), nullable=False)
    changes:            Mapped[dict]      = mapped_column(JSON, nullable=True)
    created_at:         Mapped[datetime]  = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    admin: Mapped["User"] = relationship()
