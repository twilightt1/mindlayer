"""
Source API — manage connected accounts and feeds.

Endpoints:
    POST   /api/v1/sources                create a source (registers a connector)
    GET    /api/v1/sources                list sources (filter by type, status)
    GET    /api/v1/sources/{id}           fetch one source
    PATCH  /api/v1/sources/{id}           update source settings
    DELETE /api/v1/sources/{id}           disconnect a source
    POST   /api/v1/sources/{id}/sync      trigger a (mock) sync — Phase 2 will wire
                                          to real connectors (Drive, Notion, Gmail)

The actual OAuth flow and connector implementations arrive in Phase 2
(multi-source connectors). For now this endpoint is the user-facing
control surface; the sync endpoint returns a stubbed result so the
end-to-end flow can be exercised.
"""
from __future__ import annotations

from uuid import UUID
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.source import Source
from app.utils.dependencies import get_current_verified_user
from app.schemas.source import (
    SourceCreate,
    SourceUpdate,
    SourceResponse,
    SourceListResponse,
    SourceSyncResponse,
)

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    body: SourceCreate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceResponse:
    source = Source(
        user_id=current_user.id,
        source_type=body.source_type,
        display_name=body.display_name,
        description=body.description,
        config=body.config,
        status="connected",
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


@router.get("", response_model=SourceListResponse)
async def list_sources(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    source_type: Literal["manual", "file_upload", "google_drive", "notion",
                          "gmail", "web_clipper", "rss", "calendar", "twitter", "other"] | None = None,
    status_filter: Literal["connected", "syncing", "error", "paused", "disconnected"] | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> SourceListResponse:
    base = select(Source).where(Source.user_id == current_user.id)
    count_base = select(func.count(Source.id)).where(Source.user_id == current_user.id)

    if source_type:
        base = base.where(Source.source_type == source_type)
        count_base = count_base.where(Source.source_type == source_type)
    if status_filter:
        base = base.where(Source.status == status_filter)
        count_base = count_base.where(Source.status == status_filter)

    total = (await db.execute(count_base)).scalar_one()
    rows = (await db.execute(
        base.order_by(Source.created_at.desc()).offset(offset).limit(limit)
    )).scalars().all()

    return SourceListResponse(
        items=[SourceResponse.model_validate(s) for s in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceResponse:
    source = await db.get(Source, source_id)
    if not source or source.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Source not found.")
    return SourceResponse.model_validate(source)


@router.patch("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: UUID,
    body: SourceUpdate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceResponse:
    source = await db.get(Source, source_id)
    if not source or source.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Source not found.")

    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    source = await db.get(Source, source_id)
    if not source or source.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Source not found.")
    await db.delete(source)
    await db.commit()


@router.post("/{source_id}/sync", response_model=SourceSyncResponse)
async def sync_source(
    source_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceSyncResponse:
    """
    Trigger a (mock) sync for the source. Phase 2 will dispatch to the
    real connector (Drive, Notion, Gmail, ...). For now this just
    updates last_sync_at and returns zero counts so the UI flow works.
    """
    source = await db.get(Source, source_id)
    if not source or source.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Source not found.")
    if source.status == "disconnected":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Source is disconnected.")

    now = datetime.utcnow()
    source.status = "syncing"
    await db.commit()

    # Stub: in Phase 2 this becomes a Celery job that calls the connector.
    source.status = "connected"
    source.last_sync_at = now
    source.sync_error = None
    await db.commit()

    return SourceSyncResponse(
        source_id=source_id,
        memories_added=0,
        memories_updated=0,
        errors=0,
        finished_at=now,
    )
