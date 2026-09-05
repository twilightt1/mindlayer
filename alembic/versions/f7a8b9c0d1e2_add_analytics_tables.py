"""Add analytics_events + feature_usage tables

The analytics service defines AnalyticsEvent and FeatureUsage ORM models,
but no migration ever created these tables — any DB provisioned through
alembic gets a 500 on POST /analytics/events and on the usage stats
endpoints (the tables only existed via Base.metadata.create_all in
tests/dev). Adds them with IF NOT EXISTS so create_all-provisioned DBs
converge cleanly.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "f7a8b9c0d1e2"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS analytics_events (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            event_name VARCHAR(128) NOT NULL,
            properties JSON NOT NULL DEFAULT '{}',
            path VARCHAR(256),
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_events_user_timestamp "
        "ON analytics_events (user_id, timestamp)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_events_event_timestamp "
        "ON analytics_events (event_name, timestamp)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS feature_usage (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            feature VARCHAR(64) NOT NULL,
            action VARCHAR(64) NOT NULL,
            count INTEGER NOT NULL DEFAULT 1,
            last_used TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_feature_usage_user_feature "
        "ON feature_usage (user_id, feature)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS feature_usage")
    op.execute("DROP TABLE IF EXISTS analytics_events")
