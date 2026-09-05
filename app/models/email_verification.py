import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CHAR, TIMESTAMP, ForeignKey, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import GUID

if TYPE_CHECKING:
    from app.models.user import User


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id:           Mapped[uuid.UUID]    = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id:      Mapped[uuid.UUID]    = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token:        Mapped[str]          = mapped_column(String(128), unique=True, nullable=False, index=True)
    token_type:   Mapped[str]          = mapped_column(String(20), server_default="verify")
    otp_code:     Mapped[str|None]     = mapped_column(CHAR(6), nullable=True)
    otp_attempts: Mapped[int]          = mapped_column(SmallInteger(), default=0)
    expires_at:   Mapped[datetime]     = mapped_column(TIMESTAMP(timezone=True))
    used_at:      Mapped[datetime|None]= mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at:   Mapped[datetime]     = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="email_verifications")
