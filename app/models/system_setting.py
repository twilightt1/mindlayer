import uuid
from datetime import datetime

from sqlalchemy import JSON, TIMESTAMP, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._datetime_helpers import utc_now
from app.models.types import GUID


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id:           Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    key:          Mapped[str]       = mapped_column(String(255), unique=True, nullable=False, index=True)
    value:        Mapped[dict]      = mapped_column(JSON, nullable=False)
    description:  Mapped[str|None]  = mapped_column(String(500), nullable=True)
    created_at:   Mapped[datetime]  = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:   Mapped[datetime]  = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=utc_now)
