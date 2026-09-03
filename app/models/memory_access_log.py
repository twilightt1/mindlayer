"""Access ledger for the Open Memory Hub.

Every MCP tool call (and later, every sensitive read) appends a row here so
the user can answer "which AI saw what, and when". Rows are append-only;
deletion of a memory does NOT erase the ledger (the ledger records that the
memory was accessed before deletion).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import TIMESTAMP, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MemoryAccessLog(Base):
    __tablename__ = "memory_access_logs"

    id:              Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)  # no FK: append-only ledger survives user deletion
    agent_client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)  # FK added in migration
    action:          Mapped[str] = mapped_column(String(32), nullable=False)
    memory_id:       Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)  # FK added in migration
    detail:          Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    created_at:      Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)

    __table_args__ = (
        Index("ix_access_logs_user_time", "user_id", "created_at"),
        Index("ix_access_logs_client_time", "agent_client_id", "created_at"),
    )

    def __init__(self, **kwargs: Any) -> None:
        # SQLAlchemy applies column defaults at flush time only; populate the
        # defaults here as well so transient instances (and unit tests) see them.
        kwargs.setdefault("detail", {})
        super().__init__(**kwargs)


__all__ = ["MemoryAccessLog"]
