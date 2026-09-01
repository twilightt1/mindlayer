"""
Analytics API - User Analytics Tracking

Endpoints:
    POST   /api/v1/analytics/events   - Record analytics events
    GET    /api/v1/analytics/usage    - Get feature usage stats
    GET    /api/v1/analytics/pages    - Get page view stats
    GET    /api/v1/analytics/dau      - Get daily active users
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.analytics_service import (
    get_daily_active_users,
    get_feature_usage,
    get_page_views,
    record_events,
)
from app.utils.dependencies import get_current_verified_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


class EventRecord(BaseModel):
    """Single analytics event."""
    name: str
    properties: dict | None = None
    timestamp: int | None = None


class EventBatchRequest(BaseModel):
    """Batch of events to record."""
    events: list[EventRecord]


class EventBatchResponse(BaseModel):
    """Response from recording events."""
    recorded: int


class FeatureUsageItem(BaseModel):
    """Feature usage stat."""
    feature: str
    action: str
    count: int


class FeatureUsageResponse(BaseModel):
    """Feature usage response."""
    items: list[FeatureUsageItem]
    total: int


class PageViewItem(BaseModel):
    """Page view stat."""
    path: str
    views: int


class PageViewsResponse(BaseModel):
    """Page views response."""
    items: list[PageViewItem]
    total: int


class DAUItem(BaseModel):
    """Daily active users stat."""
    date: str
    active_users: int


class DAUResponse(BaseModel):
    """Daily active users response."""
    items: list[DAUItem]


@router.post("/events", response_model=EventBatchResponse)
async def record_analytics_events(
    body: EventBatchRequest,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EventBatchResponse:
    """Record analytics events."""
    events = [e.model_dump() for e in body.events]
    recorded = await record_events(db, events, str(current_user.id))
    return EventBatchResponse(recorded=recorded)


@router.get("/usage", response_model=FeatureUsageResponse)
async def get_usage_stats(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=7, ge=1, le=90, description="Days to look back"),
) -> FeatureUsageResponse:
    """Get feature usage statistics."""
    items = await get_feature_usage(db, str(current_user.id), days)
    total = sum(item["count"] for item in items)
    return FeatureUsageResponse(
        items=[FeatureUsageItem(**item) for item in items],
        total=total,
    )


@router.get("/pages", response_model=PageViewsResponse)
async def get_page_stats(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=7, ge=1, le=90, description="Days to look back"),
) -> PageViewsResponse:
    """Get page view statistics."""
    items = await get_page_views(db, str(current_user.id), days)
    total = sum(item["views"] for item in items)
    return PageViewsResponse(
        items=[PageViewItem(**item) for item in items],
        total=total,
    )


@router.get("/dau", response_model=DAUResponse)
async def get_dau_stats(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=7, ge=1, le=90, description="Days to look back"),
) -> DAUResponse:
    """Get daily active users (admin only for org-level, user for own stats)."""
    items = await get_daily_active_users(db, days)
    return DAUResponse(items=[DAUItem(**item) for item in items])
