"""
Agents API — registered Open Memory Hub clients.

Endpoints:
    POST   /api/v1/agents                register a client; returns the plaintext token
                                         (shown EXACTLY once — only the SHA-256 hash is stored)
    GET    /api/v1/agents                list the current user's clients (no token material)
    DELETE /api/v1/agents/{client_id}    revoke a client (immediate: token stops working at once)
    GET    /api/v1/agents/access-log     access ledger, newest first, always scoped to the caller

Security notes:
    - Plaintext tokens are never persisted and never appear in list/ledger responses.
    - Revocation is immediate: an already-revoked own client revokes idempotently (204);
      unknown or other users' clients return 404 without leaking existence.
    - Every query filters on ``current_user.id``; client-supplied user ids are never trusted.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent_client import AgentClient
from app.models.memory_access_log import MemoryAccessLog
from app.models.user import User
from app.schemas.Orivory import (
    AccessLogItem,
    AccessLogListResponse,
    AgentClientCreate,
    AgentClientCreated,
    AgentClientListResponse,
    AgentClientResponse,
)
from app.services.agent_token_service import (
    generate_token,
    hash_token,
    validate_scopes,
)
from app.utils.dependencies import get_current_verified_user

router = APIRouter(prefix="/agents", tags=["agents"])


def _client_response(client: AgentClient) -> AgentClientResponse:
    """Map an AgentClient row to its token-free API representation."""
    return AgentClientResponse(
        id=client.id,
        name=client.name,
        scopes=client.scopes or [],
        status=client.status,
        created_at=client.created_at,
        last_used_at=client.last_used_at,
        revoked_at=client.revoked_at,
    )


@router.post("", response_model=AgentClientCreated, status_code=status.HTTP_201_CREATED)
async def register_agent_client(
    body: AgentClientCreate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentClientCreated:
    """Register a new agent client. The plaintext token is returned once, here only."""
    try:
        scopes = validate_scopes(body.scopes)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token = generate_token()
    client = AgentClient(
        user_id=current_user.id,
        name=body.name,
        token_hash=hash_token(token),
        scopes=scopes,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)

    return AgentClientCreated(
        id=client.id,
        name=client.name,
        scopes=client.scopes or [],
        status=client.status,
        created_at=client.created_at,
        token=token,
    )


@router.get("", response_model=AgentClientListResponse)
async def list_agent_clients(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentClientListResponse:
    """List the current user's agent clients (never includes token material)."""
    rows = (await db.execute(
        select(AgentClient)
        .where(AgentClient.user_id == current_user.id)
        .order_by(AgentClient.created_at.desc())
    )).scalars().all()

    return AgentClientListResponse(
        items=[_client_response(c) for c in rows],
        total=len(rows),
    )


# Declared BEFORE /{client_id} so "access-log" isn't parsed as a client_id.
@router.get("/access-log", response_model=AccessLogListResponse)
async def list_access_log(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    agent_client_id: UUID | None = Query(default=None, description="Filter by agent client"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> AccessLogListResponse:
    """Access ledger for the current user, newest first."""
    base = select(MemoryAccessLog).where(MemoryAccessLog.user_id == current_user.id)
    count_base = select(func.count(MemoryAccessLog.id)).where(
        MemoryAccessLog.user_id == current_user.id
    )
    if agent_client_id is not None:
        base = base.where(MemoryAccessLog.agent_client_id == agent_client_id)
        count_base = count_base.where(MemoryAccessLog.agent_client_id == agent_client_id)

    total = (await db.execute(count_base)).scalar_one()
    rows = (await db.execute(
        base.order_by(MemoryAccessLog.created_at.desc()).offset(offset).limit(limit)
    )).scalars().all()

    return AccessLogListResponse(
        items=[AccessLogItem.model_validate(row) for row in rows],
        total=total,
    )


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_agent_client(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Revoke an agent client. Immediate and idempotent for the owner (204)."""
    client = await db.get(AgentClient, client_id)
    if not client or client.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Agent client not found.")

    # Idempotent for the owner: re-revoking an already-revoked client is still 204.
    client.status = "revoked"
    client.revoked_at = datetime.now(UTC)
    await db.commit()
