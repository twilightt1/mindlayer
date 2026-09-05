"""Registered MCP/agent clients for the Open Memory Hub.

An AgentClient is one external agent (Claude Desktop, OpenClaw, Cursor, a
script) that the user has explicitly granted access to their memory store.
Tokens are stored as SHA-256 hashes only; the plaintext is shown once at
registration time by the agents API.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, TIMESTAMP, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.types import GUID

DEFAULT_SCOPES: list[str] = ["memory:read"]


class AgentClient(Base):
    __tablename__ = "agent_clients"

    id:         Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id:    Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)  # FK added in migration
    name:       Mapped[str]       = mapped_column(String(100), nullable=False)
    token_hash: Mapped[str]       = mapped_column(String(64), nullable=False, unique=True, index=True)
    scopes:     Mapped[list[str]] = mapped_column(JSON, default=lambda: list(DEFAULT_SCOPES), nullable=False)
    status:     Mapped[str]       = mapped_column(String(16), default="active", server_default="active", nullable=False)

    created_at:   Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    revoked_at:   Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    def __init__(self, **kwargs: Any) -> None:
        # SQLAlchemy applies column defaults at flush time only; populate the
        # defaults here as well so transient instances (and unit tests) see them.
        kwargs.setdefault("scopes", list(DEFAULT_SCOPES))
        kwargs.setdefault("status", "active")
        super().__init__(**kwargs)

    @property
    def is_active(self) -> bool:
        return self.status == "active" and self.revoked_at is None


__all__ = ["AgentClient"]
