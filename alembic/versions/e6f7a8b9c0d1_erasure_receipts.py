"""Erasure receipts — verifiable cascade-deletion proof (Open Memory Hub MVP 5)

One row per erasure call. ``requested_memory_ids`` is the deduplicated input;
``detail`` records per-target cascade results plus the post-deletion
verification pass. Receipts cascade away with the user (they quote personal
memory ids, so they must not outlive the user).

Revision ID: e6f7a8b9c0d1
Revises: d4e5f6a7b8c9
Create Date: 2026-09-02 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "e6f7a8b9c0d1"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "erasure_receipts",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_memory_ids", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(16), nullable=False, server_default="completed"),
        sa.Column("detail", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_erasure_receipts_user_id", "erasure_receipts", ["user_id"])
    op.create_index("ix_erasure_receipts_user_time", "erasure_receipts", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_erasure_receipts_user_time", table_name="erasure_receipts")
    op.drop_index("ix_erasure_receipts_user_id", table_name="erasure_receipts")
    op.drop_table("erasure_receipts")
