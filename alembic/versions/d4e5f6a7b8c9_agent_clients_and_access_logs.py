"""Agent clients + memory access logs — Open Memory Hub foundation

Adds the two hub tables:

  - agent_clients      : external AI agents (Claude Desktop, OpenClaw,
                         Cursor, scripts) that the user has explicitly
                         granted access to their memory store. Tokens are
                         stored as SHA-256 hashes only.
  - memory_access_logs : append-only ledger of every MCP tool call so the
                         user can answer "which AI saw what, and when".

Deleting an agent client keeps its ledger rows (agent_client_id SET NULL);
deleting a memory keeps the record that it was accessed (memory_id SET NULL),
so the ledger is never erased by cleanup.

Revision ID: d4e5f6a7b8c9
Revises: f7a8b9c0d1e2
Create Date: 2026-09-02 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── agent_clients ────────────────────────────────────────────────────────
    op.create_table(
        "agent_clients",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("scopes", ARRAY(sa.String()), nullable=False, server_default=sa.text('\'{"memory:read"}\'::varchar[]')),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_clients_user_id", "agent_clients", ["user_id"])
    op.create_index("ix_agent_clients_token_hash", "agent_clients", ["token_hash"], unique=True)

    # ── memory_access_logs (append-only) ─────────────────────────────────────
    op.create_table(
        "memory_access_logs",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("agent_client_id", UUID(as_uuid=True), sa.ForeignKey("agent_clients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("memory_id", UUID(as_uuid=True), sa.ForeignKey("memories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("detail", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_access_logs_user_time", "memory_access_logs", ["user_id", "created_at"])
    op.create_index("ix_access_logs_client_time", "memory_access_logs", ["agent_client_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_access_logs_client_time", table_name="memory_access_logs")
    op.drop_index("ix_access_logs_user_time", table_name="memory_access_logs")
    op.drop_table("memory_access_logs")
    op.drop_index("ix_agent_clients_token_hash", table_name="agent_clients")
    op.drop_index("ix_agent_clients_user_id", table_name="agent_clients")
    op.drop_table("agent_clients")
