"""
Workspace and Team models for Orivory.

Q2 Growth Track: Team Knowledge Base Sharing
- Workspace: Shared vs personal workspaces
- TeamMembership: User roles in workspaces
- Invite: Team invitations
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.types import GUID


class WorkspaceType(StrEnum):
    """Type of workspace."""
    PERSONAL = "personal"
    TEAM = "team"


class WorkspaceStatus(StrEnum):
    """Workspace status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MemberRole(StrEnum):
    """Team member role."""
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class MemberStatus(StrEnum):
    """Membership status."""
    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    LEFT = "left"


class InviteStatus(StrEnum):
    """Invite status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class Workspace(Base):
    """Workspace model - personal or team workspace."""

    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Workspace details
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    workspace_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="personal",
    )

    # Ownership
    owner_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Organization (for team workspaces)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        nullable=True,
        index=True,
    )

    # Settings (JSON for flexibility)
    settings: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="active",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
    )

    # Member count (denormalized for performance)
    member_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    # Indexes
    __table_args__ = (
        Index("ix_workspaces_owner_status", "owner_id", "status"),
        Index("ix_workspaces_org_status", "organization_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Workspace {self.id} name={self.name} type={self.workspace_type}>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "workspace_type": self.workspace_type,
            "owner_id": str(self.owner_id),
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "settings": self.settings,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "member_count": self.member_count,
        }


class TeamMembership(Base):
    """Team membership model - users in team workspaces."""

    __tablename__ = "team_memberships"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Workspace
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # User
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Role
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="viewer",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="active",
    )

    # Permissions (JSON for custom permissions)
    permissions: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
    )

    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
    )

    # Indexes
    __table_args__ = (
        Index("ix_team_memberships_workspace_user", "workspace_id", "user_id", unique=True),
        Index("ix_team_memberships_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<TeamMembership {self.id} workspace={self.workspace_id} user={self.user_id} role={self.role}>"

    def can_edit(self) -> bool:
        """Check if member can edit workspace."""
        return self.role in (MemberRole.OWNER.value, MemberRole.ADMIN.value, MemberRole.EDITOR.value)

    def can_manage_members(self) -> bool:
        """Check if member can manage other members."""
        return self.role in (MemberRole.OWNER.value, MemberRole.ADMIN.value)

    def can_delete(self) -> bool:
        """Check if member can delete workspace."""
        return self.role == MemberRole.OWNER.value


class WorkspaceInvite(Base):
    """Workspace invite model - pending invitations."""

    __tablename__ = "workspace_invites"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Workspace
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Inviter
    inviter_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Invitee
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Role to assign
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="viewer",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="pending",
    )

    # Token for invite link
    invite_token: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    # Message
    message: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
    )

    # Indexes
    __table_args__ = (
        Index("ix_workspace_invites_workspace_status", "workspace_id", "status"),
        Index("ix_workspace_invites_email", "email"),
    )

    def __repr__(self) -> str:
        return f"<WorkspaceInvite {self.id} email={self.email} role={self.role}>"

    def is_expired(self) -> bool:
        """Check if invite has expired."""
        return datetime.now(UTC) > self.expires_at.replace(tzinfo=UTC)

    def is_pending(self) -> bool:
        """Check if invite is still pending."""
        return self.status == InviteStatus.PENDING.value and not self.is_expired()
