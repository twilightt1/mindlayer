"""Add missing tables + memories.is_shared; insight_cards timestamps -> timestamptz

The migration chain never created workspaces, team_memberships,
workspace_invites, insight_cards, or feedbacks — those tables only existed
via Base.metadata.create_all (tests/dev). Any DB provisioned solely through
alembic was missing them. This migration adds them (IF NOT EXISTS so DBs that
already have them via create_all converge cleanly).

Also adds memories.is_shared (model column that had no migration) and converts
insight_cards timestamps to timestamptz: the refresh endpoint compares
InsightCard.created_at against Memory.captured_at (timestamptz, read back as
tz-aware by asyncpg), which raises TypeError on every call with real data.
Naive values are interpreted as UTC.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS workspaces (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            description VARCHAR(1000),
            workspace_type VARCHAR(32) NOT NULL DEFAULT 'personal',
            owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            organization_id UUID,
            settings JSONB NOT NULL DEFAULT '{}',
            status VARCHAR(32) NOT NULL DEFAULT 'active',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            member_count INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspaces_owner_id ON workspaces (owner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspaces_organization_id ON workspaces (organization_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspaces_owner_status ON workspaces (owner_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspaces_org_status ON workspaces (organization_id, status)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS team_memberships (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role VARCHAR(32) NOT NULL DEFAULT 'viewer',
            status VARCHAR(32) NOT NULL DEFAULT 'active',
            permissions JSONB NOT NULL DEFAULT '{}',
            joined_at TIMESTAMP NOT NULL DEFAULT NOW(),
            last_accessed_at TIMESTAMP
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_team_memberships_workspace_id ON team_memberships (workspace_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_team_memberships_user_id ON team_memberships (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_team_memberships_user_status ON team_memberships (user_id, status)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_team_memberships_workspace_user "
        "ON team_memberships (workspace_id, user_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS workspace_invites (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            inviter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            email VARCHAR(255) NOT NULL,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            role VARCHAR(32) NOT NULL DEFAULT 'viewer',
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            invite_token VARCHAR(64) NOT NULL,
            message VARCHAR(500),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMP NOT NULL,
            accepted_at TIMESTAMP
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspace_invites_workspace_id ON workspace_invites (workspace_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspace_invites_email ON workspace_invites (email)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspace_invites_user_id ON workspace_invites (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspace_invites_workspace_status ON workspace_invites (workspace_id, status)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_workspace_invites_invite_token "
        "ON workspace_invites (invite_token)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS insight_cards (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(500) NOT NULL,
            insight_type VARCHAR(32) NOT NULL DEFAULT 'connection',
            summary VARCHAR(500) NOT NULL,
            detail TEXT NOT NULL,
            source_docs JSONB NOT NULL DEFAULT '[]',
            source_count INTEGER NOT NULL DEFAULT 1,
            surprise_level VARCHAR(16) NOT NULL DEFAULT 'medium',
            confidence FLOAT NOT NULL DEFAULT 0.5,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            shown_at TIMESTAMPTZ,
            dismissed_at TIMESTAMPTZ,
            status VARCHAR(32) NOT NULL DEFAULT 'new',
            helpful BOOLEAN,
            feedback_note VARCHAR(1000),
            shown_count INTEGER NOT NULL DEFAULT 0,
            relevance_score FLOAT NOT NULL DEFAULT 0.5,
            user_preferences_snapshot JSONB
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_insight_cards_user_id ON insight_cards (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_insight_cards_created_at ON insight_cards (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_insight_cards_status ON insight_cards (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_insight_cards_user_type ON insight_cards (user_id, insight_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_insight_cards_user_status ON insight_cards (user_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_insight_cards_user_created ON insight_cards (user_id, created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_insight_cards_user_relevance ON insight_cards (user_id, relevance_score)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS feedbacks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            message_id UUID NOT NULL,
            feedback_type VARCHAR(32) NOT NULL DEFAULT 'positive',
            query_hash VARCHAR(64) NOT NULL,
            doc_ids VARCHAR(128)[] NOT NULL DEFAULT '{}',
            content VARCHAR(5000),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_feedbacks_user_id ON feedbacks (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feedbacks_conversation_id ON feedbacks (conversation_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feedbacks_message_id ON feedbacks (message_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feedbacks_created_at ON feedbacks (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feedbacks_query_hash ON feedbacks (query_hash)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feedbacks_type_created ON feedbacks (feedback_type, created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feedbacks_user_created ON feedbacks (user_id, created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feedbacks_conversation_created ON feedbacks (conversation_id, created_at)")

    op.execute("ALTER TABLE memories ADD COLUMN IF NOT EXISTS is_shared BOOLEAN NOT NULL DEFAULT false")

    # Convert any pre-existing naive insight_cards timestamps (created by
    # create_all with the old model) to timestamptz. Idempotent.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'insight_cards'
                  AND column_name IN ('created_at', 'shown_at', 'dismissed_at')
                  AND data_type = 'timestamp without time zone'
            ) THEN
                ALTER TABLE insight_cards
                    ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC',
                    ALTER COLUMN shown_at TYPE TIMESTAMPTZ USING shown_at AT TIME ZONE 'UTC',
                    ALTER COLUMN dismissed_at TYPE TIMESTAMPTZ USING dismissed_at AT TIME ZONE 'UTC';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS feedbacks")
    op.execute("DROP TABLE IF EXISTS workspace_invites")
    op.execute("DROP TABLE IF EXISTS team_memberships")
    op.execute("DROP TABLE IF EXISTS insight_cards")
    op.execute("DROP TABLE IF EXISTS workspaces")
    op.execute("ALTER TABLE memories DROP COLUMN IF EXISTS is_shared")
