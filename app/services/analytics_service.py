"""
Analytics Service

Stores and aggregates user analytics events.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    and_,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

log = logging.getLogger(__name__)


class AnalyticsEvent(Base):
    """Analytics event model."""
    __tablename__ = "analytics_events"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    user_id: str = Column(String(36), nullable=False, index=True)
    event_name: str = Column(String(128), nullable=False, index=True)
    properties: dict = Column(JSON, server_default="{}", nullable=False)
    path: str = Column(String(256), nullable=True)
    timestamp: datetime = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("ix_events_user_timestamp", "user_id", "timestamp"),
        Index("ix_events_event_timestamp", "event_name", "timestamp"),
    )


class FeatureUsage(Base):
    """Feature usage aggregation."""
    __tablename__ = "feature_usage"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    user_id: str = Column(String(36), nullable=False)
    feature: str = Column(String(64), nullable=False)
    action: str = Column(String(64), nullable=False)
    count: int = Column(Integer, server_default="1", nullable=False)
    last_used: datetime = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("ix_feature_usage_user_feature", "user_id", "feature"),
    )


async def record_events(
    db: AsyncSession,
    events: list[dict],
    user_id: str,
) -> int:
    """Record analytics events."""
    if not events:
        return 0

    records = []
    for event in events:
        records.append({
            "user_id": user_id,
            "event_name": event.get("name", "unknown"),
            "properties": event.get("properties", {}),
            "path": event.get("properties", {}).get("url", ""),
            "timestamp": datetime.fromtimestamp(
                event.get("timestamp", 0) / 1000,
                tz=UTC
            ) if event.get("timestamp") else datetime.now(UTC),
        })

    db.add_all([AnalyticsEvent(**r) for r in records])
    await db.commit()

    log.info(f"Recorded {len(records)} analytics events for user {user_id}")
    return len(records)


async def record_feature_usage(
    db: AsyncSession,
    user_id: str,
    feature: str,
    action: str,
) -> None:
    """Record feature usage."""
    # Check for existing record
    result = await db.execute(
        select(FeatureUsage).where(
            and_(
                FeatureUsage.user_id == user_id,
                FeatureUsage.feature == feature,
                FeatureUsage.action == action,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.count += 1
        existing.last_used = datetime.now(UTC)
    else:
        db.add(FeatureUsage(
            user_id=user_id,
            feature=feature,
            action=action,
        ))

    await db.commit()


async def get_feature_usage(
    db: AsyncSession,
    user_id: str,
    days: int = 7,
) -> list[dict]:
    """Get feature usage for user in last N days."""
    cutoff = datetime.now(UTC) - __import__("datetime").timedelta(days=days)

    result = await db.execute(
        select(
            FeatureUsage.feature,
            FeatureUsage.action,
            func.sum(FeatureUsage.count).label("total_count"),
        )
        .where(
            and_(
                FeatureUsage.user_id == user_id,
                FeatureUsage.last_used >= cutoff,
            )
        )
        .group_by(FeatureUsage.feature, FeatureUsage.action)
        .order_by(func.sum(FeatureUsage.count).desc())
    )

    return [
        {
            "feature": row.feature,
            "action": row.action,
            "count": row.total_count,
        }
        for row in result.all()
    ]


async def get_page_views(
    db: AsyncSession,
    user_id: str,
    days: int = 7,
) -> list[dict]:
    """Get page views for user in last N days."""
    cutoff = datetime.now(UTC) - __import__("datetime").timedelta(days=days)

    result = await db.execute(
        select(
            AnalyticsEvent.path,
            func.count().label("views"),
        )
        .where(
            and_(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.event_name == "page_view",
                AnalyticsEvent.timestamp >= cutoff,
            )
        )
        .group_by(AnalyticsEvent.path)
        .order_by(func.count().desc())
    )

    return [
        {"path": row.path, "views": row.views}
        for row in result.all()
    ]


async def get_daily_active_users(
    db: AsyncSession,
    days: int = 7,
) -> list[dict]:
    """Get daily active users count."""
    cutoff = datetime.now(UTC) - __import__("datetime").timedelta(days=days)

    result = await db.execute(
        select(
            func.date(AnalyticsEvent.timestamp).label("date"),
            func.count(func.distinct(AnalyticsEvent.user_id)).label("dau"),
        )
        .where(AnalyticsEvent.timestamp >= cutoff)
        .group_by(func.date(AnalyticsEvent.timestamp))
        .order_by(func.date(AnalyticsEvent.timestamp))
    )

    return [
        {"date": str(row.date), "active_users": row.dau}
        for row in result.all()
    ]
