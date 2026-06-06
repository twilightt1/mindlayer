"""
Source API — manage connected accounts and feeds.

Endpoints:
    POST   /api/v1/sources                create a source (registers a connector)
    GET    /api/v1/sources                list sources (filter by type, status)
    GET    /api/v1/sources/{id}           fetch one source
    PATCH  /api/v1/sources/{id}           update source settings
    DELETE /api/v1/sources/{id}           disconnect a source
    POST   /api/v1/sources/{id}/sync      trigger a sync via SourceSyncService
                                          (real connector dispatch)

The actual OAuth flow lives in Phase 2.5+; the sync endpoint delegates to
``SourceSyncService`` which runs the registered connector for the
source's ``source_type`` and persists results as Memory rows.
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
from app.ingestion.connectors.registry import get_connector_for_source

router = APIRouter(prefix="/sources", tags=["sources"])

CONFIG_VALIDATED_SOURCE_TYPES = {"rss", "web_clipper"}
SENSITIVE_CONFIG_KEYS = {
    "api_key",
    "access_token",
    "refresh_token",
    "client_secret",
    "credentials",
    "password",
    "secret",
    "token",
}


def _safe_source_config(config: dict | None) -> dict:
    """Return source config safe for UI display, redacting secret-like keys."""
    safe: dict = {}
    for key, value in (config or {}).items():
        key_lc = str(key).lower()
        if key_lc in SENSITIVE_CONFIG_KEYS or key_lc.endswith("_token") or key_lc.endswith("_secret"):
            safe[key] = "••••••••" if value else None
        elif isinstance(value, dict):
            safe[key] = _safe_source_config(value)
        elif isinstance(value, list):
            safe[key] = [
                _safe_source_config(item) if isinstance(item, dict) else item
                for item in value[:25]
            ]
        else:
            safe[key] = value
    return safe


def _source_response(source: Source) -> SourceResponse:
    response = SourceResponse.model_validate(source)
    return response.model_copy(update={"config": _safe_source_config(source.config)})


def _validate_source_config_or_422(source_type: str, config: dict | None) -> None:
    """Validate configs for practical no-OAuth connectors at create/update time."""
    if source_type not in CONFIG_VALIDATED_SOURCE_TYPES:
        return
    try:
        connector = get_connector_for_source(source_type, config or {})
        connector.validate_config()
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    body: SourceCreate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceResponse:
    _validate_source_config_or_422(body.source_type, body.config)
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
    return _source_response(source)


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
        items=[_source_response(s) for s in rows],
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
    return _source_response(source)


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
    if "config" in data:
        data["config"] = data["config"] or {}
        _validate_source_config_or_422(source.source_type, data["config"])
    for field, value in data.items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)
    return _source_response(source)


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
    Trigger a real sync for the source via ``SourceSyncService``.

    The dispatcher looks up the connector registered for
    ``source.source_type`` and runs fetch + persist. We expose the
    counts back to the caller so the UI can render progress.
    """
    from app.ingestion.dispatcher import SourceSyncService

    source = await db.get(Source, source_id)
    if not source or source.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Source not found.")
    if source.status == "disconnected":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Source is disconnected.")

    source.status = "syncing"
    await db.commit()

    try:
        result = await SourceSyncService(db).sync(source)
    except Exception as exc:  # defensive: never bubble 500 to the UI on a sync
        source.status = "error"
        source.sync_error = str(exc)
        await db.commit()
        return SourceSyncResponse(
            source_id=source_id,
            memories_added=0,
            memories_updated=0,
            errors=1,
            finished_at=datetime.utcnow(),
        )

    return SourceSyncResponse(
        source_id=source_id,
        memories_added=result.memories_added,
        memories_updated=result.memories_updated,
        errors=len(result.errors),
        finished_at=result.finished_at,
    )
