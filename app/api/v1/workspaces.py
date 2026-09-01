"""
Workspace API - Team Knowledge Base Sharing

Q2 Growth Track: Shared workspaces for research teams.

Endpoints:
    GET    /api/v1/workspaces               - List user's workspaces
    POST   /api/v1/workspaces               - Create workspace
    GET    /api/v1/workspaces/{id}          - Get workspace
    PATCH  /api/v1/workspaces/{id}          - Update workspace
    DELETE /api/v1/workspaces/{id}           - Delete workspace
    GET    /api/v1/workspaces/{id}/members  - List members
    POST   /api/v1/workspaces/{id}/members  - Add member
    PATCH  /api/v1/workspaces/{id}/members/{user_id}  - Update member role
    DELETE /api/v1/workspaces/{id}/members/{user_id}  - Remove member
    GET    /api/v1/workspaces/{id}/invites - List pending invites
    POST   /api/v1/workspaces/{id}/invites - Create invite
    DELETE /api/v1/workspaces/{id}/invites/{invite_id} - Cancel invite
    POST   /api/v1/workspaces/invites/{token}/accept - Accept invite
"""

from __future__ import annotations

import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.workspace import (
    InviteStatus,
    MemberRole,
    MemberStatus,
    TeamMembership,
    Workspace,
    WorkspaceInvite,
    WorkspaceStatus,
)
from app.utils.dependencies import get_current_verified_user

log = logging.getLogger(__name__)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class WorkspaceCreate(BaseModel):
    """Create workspace request."""
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    workspace_type: str = Field(default="team", pattern="^(personal|team)$")
    settings: dict = Field(default_factory=dict)


class WorkspaceUpdate(BaseModel):
    """Update workspace request."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    settings: dict | None = None
    status: str | None = Field(default=None, pattern="^(active|archived)$")


class WorkspaceResponse(BaseModel):
    """Workspace response."""
    model_config = {"from_attributes": True}

    id: UUID
    name: str
    description: str | None
    workspace_type: str
    owner_id: UUID
    organization_id: UUID | None
    settings: dict
    status: str
    created_at: datetime
    updated_at: datetime
    member_count: int


class MemberResponse(BaseModel):
    """Team member response."""
    model_config = {"from_attributes": True}

    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: str
    status: str
    permissions: dict
    joined_at: datetime
    last_accessed_at: datetime | None


class MemberUpdate(BaseModel):
    """Update member request."""
    role: str | None = Field(default=None, pattern="^(admin|editor|viewer)$")


class InviteCreate(BaseModel):
    """Create invite request."""
    email: EmailStr
    role: str = Field(default="viewer", pattern="^(admin|editor|viewer)$")
    message: str | None = Field(default=None, max_length=500)


class InviteResponse(BaseModel):
    """Invite response."""
    model_config = {"from_attributes": True}

    id: UUID
    workspace_id: UUID
    inviter_id: UUID
    email: str
    user_id: UUID | None
    role: str
    status: str
    message: str | None
    created_at: datetime
    expires_at: datetime
    accepted_at: datetime | None


class WorkspaceListResponse(BaseModel):
    """List workspaces response."""
    items: list[WorkspaceResponse]
    total: int


class MemberListResponse(BaseModel):
    """List members response."""
    items: list[MemberResponse]
    total: int


class InviteListResponse(BaseModel):
    """List invites response."""
    items: list[InviteResponse]
    total: int


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def get_workspace_membership(
    db: AsyncSession,
    workspace_id: UUID,
    user_id: UUID,
) -> TeamMembership | None:
    """Get user's membership in a workspace."""
    result = await db.execute(
        select(TeamMembership).where(
            TeamMembership.workspace_id == workspace_id,
            TeamMembership.user_id == user_id,
            TeamMembership.status == MemberStatus.ACTIVE.value,
        )
    )
    return result.scalar_one_or_none()


async def check_workspace_access(
    db: AsyncSession,
    workspace_id: UUID,
    user_id: UUID,
    require_edit: bool = False,
) -> TeamMembership:
    """Check if user has access to workspace, raise if not."""
    # Check ownership
    workspace = await db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found.")

    if workspace.owner_id == user_id:
        # Owner has full access
        return TeamMembership(
            workspace_id=workspace_id,
            user_id=user_id,
            role=MemberRole.OWNER.value,
            status=MemberStatus.ACTIVE.value,
        )

    # Check membership
    membership = await get_workspace_membership(db, workspace_id, user_id)
    if not membership:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied.")

    if require_edit and not membership.can_edit():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Edit permission required.")

    return membership


def generate_invite_token() -> str:
    """Generate a secure invite token."""
    return secrets.token_urlsafe(32)


# ─── Workspace Endpoints ──────────────────────────────────────────────────────

@router.get("", response_model=WorkspaceListResponse)
async def list_workspaces(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    workspace_type: str | None = Query(default=None, pattern="^(personal|team)$"),
) -> WorkspaceListResponse:
    """List user's workspaces (owned + member of)."""
    # Get owned workspaces
    owned_query = select(Workspace).where(
        Workspace.owner_id == current_user.id,
        Workspace.status != WorkspaceStatus.DELETED.value,
    )

    # Get workspaces where user is a member
    member_query = select(Workspace).join(
        TeamMembership,
        Workspace.id == TeamMembership.workspace_id,
    ).where(
        TeamMembership.user_id == current_user.id,
        TeamMembership.status == MemberStatus.ACTIVE.value,
        Workspace.status != WorkspaceStatus.DELETED.value,
    )

    if workspace_type:
        owned_query = owned_query.where(Workspace.workspace_type == workspace_type)
        member_query = member_query.where(Workspace.workspace_type == workspace_type)

    # Combine queries
    combined_query = owned_query.union(member_query)
    count_query = select(func.count()).select_from(combined_query.subquery())

    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(
        combined_query.order_by(Workspace.updated_at.desc()).limit(100)
    )
    workspaces = result.scalars().all()

    return WorkspaceListResponse(
        items=[WorkspaceResponse.model_validate(w) for w in workspaces],
        total=total,
    )


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    body: WorkspaceCreate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceResponse:
    """Create a new workspace."""
    # Create workspace
    workspace = Workspace(
        name=body.name,
        description=body.description,
        workspace_type=body.workspace_type,
        owner_id=current_user.id,
        settings=body.settings,
    )
    db.add(workspace)
    await db.flush()

    # Add owner as member with owner role
    membership = TeamMembership(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role=MemberRole.OWNER.value,
        status=MemberStatus.ACTIVE.value,
    )
    db.add(membership)

    await db.commit()
    await db.refresh(workspace)

    return WorkspaceResponse.model_validate(workspace)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceResponse:
    """Get a workspace."""
    await check_workspace_access(db, workspace_id, current_user.id)

    workspace = await db.get(Workspace, workspace_id)
    return WorkspaceResponse.model_validate(workspace)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    body: WorkspaceUpdate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceResponse:
    """Update a workspace."""
    membership = await check_workspace_access(db, workspace_id, current_user.id, require_edit=True)

    if not membership.can_edit():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Edit permission required.")

    workspace = await db.get(Workspace, workspace_id)

    if body.name is not None:
        workspace.name = body.name
    if body.description is not None:
        workspace.description = body.description
    if body.settings is not None:
        workspace.settings = body.settings
    if body.status is not None:
        workspace.status = body.status

    workspace.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(workspace)

    return WorkspaceResponse.model_validate(workspace)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a workspace (soft delete)."""
    membership = await check_workspace_access(db, workspace_id, current_user.id)

    if not membership.can_delete():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only owner can delete workspace.")

    workspace = await db.get(Workspace, workspace_id)
    workspace.status = WorkspaceStatus.DELETED.value
    workspace.updated_at = datetime.now(UTC)

    await db.commit()


# ─── Member Endpoints ────────────────────────────────────────────────────────

@router.get("/{workspace_id}/members", response_model=MemberListResponse)
async def list_members(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MemberListResponse:
    """List workspace members."""
    await check_workspace_access(db, workspace_id, current_user.id)

    result = await db.execute(
        select(TeamMembership).where(
            TeamMembership.workspace_id == workspace_id,
            TeamMembership.status == MemberStatus.ACTIVE.value,
        )
    )
    members = result.scalars().all()

    return MemberListResponse(
        items=[MemberResponse.model_validate(m) for m in members],
        total=len(members),
    )


@router.post("/{workspace_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    workspace_id: UUID,
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    role: str = Query(default="viewer", pattern="^(admin|editor|viewer)$"),
) -> MemberResponse:
    """Add a member directly by user ID (for existing users)."""
    membership = await check_workspace_access(db, workspace_id, current_user.id)

    if not membership.can_manage_members():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Manage members permission required.")

    # Check if user exists
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")

    # Check if already a member
    existing = await get_workspace_membership(db, workspace_id, user_id)
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User is already a member.")

    # Create membership
    new_membership = TeamMembership(
        workspace_id=workspace_id,
        user_id=user_id,
        role=role,
        status=MemberStatus.ACTIVE.value,
    )
    db.add(new_membership)

    # Update member count
    workspace = await db.get(Workspace, workspace_id)
    workspace.member_count += 1
    workspace.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(new_membership)

    return MemberResponse.model_validate(new_membership)


@router.patch("/{workspace_id}/members/{target_user_id}", response_model=MemberResponse)
async def update_member(
    workspace_id: UUID,
    target_user_id: UUID,
    body: MemberUpdate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MemberResponse:
    """Update a member's role."""
    membership = await check_workspace_access(db, workspace_id, current_user.id)

    if not membership.can_manage_members():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Manage members permission required.")

    # Can't change owner's role
    workspace = await db.get(Workspace, workspace_id)
    if workspace.owner_id == target_user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot change owner's role.")

    target_membership = await get_workspace_membership(db, workspace_id, target_user_id)
    if not target_membership:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found.")

    if body.role:
        target_membership.role = body.role

    await db.commit()
    await db.refresh(target_membership)

    return MemberResponse.model_validate(target_membership)


@router.delete("/{workspace_id}/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: UUID,
    target_user_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Remove a member from workspace."""
    membership = await check_workspace_access(db, workspace_id, current_user.id)

    # Can remove if manage members or removing self
    can_remove = membership.can_manage_members() or current_user.id == target_user_id
    if not can_remove:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied.")

    # Can't remove owner
    workspace = await db.get(Workspace, workspace_id)
    if workspace.owner_id == target_user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot remove owner.")

    target_membership = await get_workspace_membership(db, workspace_id, target_user_id)
    if not target_membership:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found.")

    target_membership.status = MemberStatus.LEFT.value

    # Update member count
    workspace.member_count = max(1, workspace.member_count - 1)
    workspace.updated_at = datetime.now(UTC)

    await db.commit()


# ─── Invite Endpoints ────────────────────────────────────────────────────────

@router.get("/{workspace_id}/invites", response_model=InviteListResponse)
async def list_invites(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InviteListResponse:
    """List pending invites for workspace."""
    membership = await check_workspace_access(db, workspace_id, current_user.id)

    if not membership.can_manage_members():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Manage members permission required.")

    result = await db.execute(
        select(WorkspaceInvite).where(
            WorkspaceInvite.workspace_id == workspace_id,
            WorkspaceInvite.status == InviteStatus.PENDING.value,
        )
    )
    invites = result.scalars().all()

    return InviteListResponse(
        items=[InviteResponse.model_validate(i) for i in invites],
        total=len(invites),
    )


@router.post("/{workspace_id}/invites", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    workspace_id: UUID,
    body: InviteCreate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InviteResponse:
    """Create an invite for a workspace."""
    membership = await check_workspace_access(db, workspace_id, current_user.id)

    if not membership.can_manage_members():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Manage members permission required.")

    # Check if user already has invite
    existing = await db.execute(
        select(WorkspaceInvite).where(
            WorkspaceInvite.workspace_id == workspace_id,
            WorkspaceInvite.email == body.email,
            WorkspaceInvite.status == InviteStatus.PENDING.value,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Pending invite already exists for this email.")

    # Check if user is already a member
    invitee = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    invitee_user = invitee.scalar_one_or_none()

    if invitee_user:
        existing_membership = await get_workspace_membership(db, workspace_id, invitee_user.id)
        if existing_membership:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "User is already a member.")

    # Create invite
    invite = WorkspaceInvite(
        workspace_id=workspace_id,
        inviter_id=current_user.id,
        email=body.email.lower(),
        user_id=invitee_user.id if invitee_user else None,
        role=body.role,
        invite_token=generate_invite_token(),
        message=body.message,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)

    return InviteResponse.model_validate(invite)


@router.delete("/{workspace_id}/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invite(
    workspace_id: UUID,
    invite_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Cancel a pending invite."""
    membership = await check_workspace_access(db, workspace_id, current_user.id)

    if not membership.can_manage_members():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Manage members permission required.")

    invite = await db.get(WorkspaceInvite, invite_id)
    if not invite or invite.workspace_id != workspace_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found.")

    invite.status = InviteStatus.DECLINED.value
    await db.commit()


@router.post("/invites/{invite_token}/accept", response_model=MemberResponse)
async def accept_invite(
    invite_token: str,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MemberResponse:
    """Accept a workspace invite."""
    # Find invite by token
    result = await db.execute(
        select(WorkspaceInvite).where(WorkspaceInvite.invite_token == invite_token)
    )
    invite = result.scalar_one_or_none()

    if not invite:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found.")

    if invite.status != InviteStatus.PENDING.value:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invite is {invite.status}.")

    if invite.is_expired():
        invite.status = InviteStatus.EXPIRED.value
        await db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invite has expired.")

    # Verify email matches
    if invite.email != current_user.email.lower():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This invite is for a different email.")

    # Create membership
    membership = TeamMembership(
        workspace_id=invite.workspace_id,
        user_id=current_user.id,
        role=invite.role,
        status=MemberStatus.ACTIVE.value,
    )
    db.add(membership)

    # Update invite status
    invite.status = InviteStatus.ACCEPTED.value
    invite.user_id = current_user.id
    invite.accepted_at = datetime.now(UTC)

    # Update member count
    workspace = await db.get(Workspace, invite.workspace_id)
    workspace.member_count += 1
    workspace.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(membership)

    return MemberResponse.model_validate(membership)
