"""Memory usage feedback — salience loop columns

Adds usage-tracking columns to the ``memories`` table so the salience
feedback loop (P2.1) can bump memories that get recalled and used, and
decay ones that go untouched:

  - recall_count : int  — how many answers a memory has contributed to
  - last_used_at : timestamp (nullable) — when it was last used in an answer

Plus an index on (user_id, last_used_at) for the periodic decay scan.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-17 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "memories",
        sa.Column("recall_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "memories",
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_memories_user_last_used", "memories", ["user_id", "last_used_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_memories_user_last_used", table_name="memories")
    op.drop_column("memories", "last_used_at")
    op.drop_column("memories", "recall_count")
