"""Import dedup integrity + ledger retention support

Adds a partial unique index on ``(user_id, source_type, source_ref)`` for
imported memories (only where ``source_ref`` is NOT NULL) so concurrent
imports of the same file cannot both succeed — closing the race window the
import service documented in v0.

Also adds ``retention_days`` to ``system_settings``-style governance: the
``memory_access_logs`` ledger retention task reads its window from the
existing ``ledger_retention_days`` setting (default 90).

Revision ID: c7d8e9f0a1b2
Revises: e6f7a8b9c0d1
Create Date: 2026-09-05 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c7d8e9f0a1b2"
down_revision: str | None = "e6f7a8b9c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Deduplicate existing imported memories first — the unique index below
    # would fail otherwise. Keep ONE row per (user, type, ref): the
    # lexicographically smallest (captured_at, id) pair — deterministic even
    # when timestamps tie. Later duplicates were the result of the
    # documented concurrent-import race. Child rows follow via ON DELETE
    # CASCADE.
    op.execute(
        """
        DELETE FROM memories m
        WHERE m.source_ref IS NOT NULL
          AND EXISTS (
            SELECT 1
            FROM memories k
            WHERE k.user_id = m.user_id
              AND k.source_type = m.source_type
              AND k.source_ref = m.source_ref
              AND (k.captured_at, k.id) < (m.captured_at, m.id)
          )
        """
    )

    # Partial unique index: NULL source_refs (manual notes) are exempt —
    # they are deduplicated by content, not by ref.
    op.create_index(
        "uq_imported_memories_user_type_ref",
        "memories",
        ["user_id", "source_type", "source_ref"],
        unique=True,
        postgresql_where=sa.text("source_ref IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_imported_memories_user_type_ref", table_name="memories")
