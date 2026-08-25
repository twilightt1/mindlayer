"""
Tests for Workspace models - Team Knowledge Base Sharing

Q2 Growth Track: Team workspaces, permissions, invites
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.models.workspace import (
    Workspace,
    TeamMembership,
    WorkspaceInvite,
    WorkspaceType,
    WorkspaceStatus,
    MemberRole,
    MemberStatus,
    InviteStatus,
)


class TestWorkspaceType:
    """Test WorkspaceType enum."""

    def test_all_types_exist(self):
        """All workspace types should exist."""
        assert WorkspaceType.PERSONAL.value == "personal"
        assert WorkspaceType.TEAM.value == "team"


class TestWorkspaceStatus:
    """Test WorkspaceStatus enum."""

    def test_all_statuses_exist(self):
        """All statuses should exist."""
        assert WorkspaceStatus.ACTIVE.value == "active"
        assert WorkspaceStatus.ARCHIVED.value == "archived"
        assert WorkspaceStatus.DELETED.value == "deleted"


class TestMemberRole:
    """Test MemberRole enum."""

    def test_all_roles_exist(self):
        """All roles should exist."""
        assert MemberRole.OWNER.value == "owner"
        assert MemberRole.ADMIN.value == "admin"
        assert MemberRole.EDITOR.value == "editor"
        assert MemberRole.VIEWER.value == "viewer"


class TestMemberStatus:
    """Test MemberStatus enum."""

    def test_all_statuses_exist(self):
        """All statuses should exist."""
        assert MemberStatus.ACTIVE.value == "active"
        assert MemberStatus.PENDING.value == "pending"
        assert MemberStatus.SUSPENDED.value == "suspended"
        assert MemberStatus.LEFT.value == "left"


class TestInviteStatus:
    """Test InviteStatus enum."""

    def test_all_statuses_exist(self):
        """All statuses should exist."""
        assert InviteStatus.PENDING.value == "pending"
        assert InviteStatus.ACCEPTED.value == "accepted"
        assert InviteStatus.DECLINED.value == "declined"
        assert InviteStatus.EXPIRED.value == "expired"


class TestWorkspace:
    """Test Workspace model."""

    def test_workspace_creation(self):
        """Test creating a workspace."""
        workspace = Workspace(
            id=uuid4(),
            name="Test Workspace",
            description="A test workspace",
            workspace_type=WorkspaceType.TEAM.value,
            owner_id=uuid4(),
            settings={"visibility": "private"},
            status=WorkspaceStatus.ACTIVE.value,  # Explicitly set since no DB session
        )
        
        assert workspace.name == "Test Workspace"
        assert workspace.workspace_type == WorkspaceType.TEAM.value
        assert workspace.status == WorkspaceStatus.ACTIVE.value

    def test_workspace_to_dict(self):
        """Test workspace to_dict method."""
        workspace_id = uuid4()
        owner_id = uuid4()
        
        workspace = Workspace(
            id=workspace_id,
            name="Test Workspace",
            owner_id=owner_id,
        )
        
        data = workspace.to_dict()
        
        assert data["name"] == "Test Workspace"
        assert data["id"] == str(workspace_id)
        assert data["owner_id"] == str(owner_id)


class TestTeamMembership:
    """Test TeamMembership model."""

    def test_membership_creation(self):
        """Test creating a membership."""
        workspace_id = uuid4()
        user_id = uuid4()
        
        membership = TeamMembership(
            workspace_id=workspace_id,
            user_id=user_id,
            role=MemberRole.EDITOR.value,
            status=MemberStatus.ACTIVE.value,
        )
        
        assert membership.workspace_id == workspace_id
        assert membership.user_id == user_id
        assert membership.role == MemberRole.EDITOR.value

    def test_can_edit_owner(self):
        """Test that owner can edit."""
        membership = TeamMembership(
            workspace_id=uuid4(),
            user_id=uuid4(),
            role=MemberRole.OWNER.value,
        )
        
        assert membership.can_edit() is True
        assert membership.can_manage_members() is True
        assert membership.can_delete() is True

    def test_can_edit_admin(self):
        """Test that admin can edit and manage."""
        membership = TeamMembership(
            workspace_id=uuid4(),
            user_id=uuid4(),
            role=MemberRole.ADMIN.value,
        )
        
        assert membership.can_edit() is True
        assert membership.can_manage_members() is True
        assert membership.can_delete() is False

    def test_can_edit_editor(self):
        """Test that editor can edit."""
        membership = TeamMembership(
            workspace_id=uuid4(),
            user_id=uuid4(),
            role=MemberRole.EDITOR.value,
        )
        
        assert membership.can_edit() is True
        assert membership.can_manage_members() is False
        assert membership.can_delete() is False

    def test_cannot_edit_viewer(self):
        """Test that viewer cannot edit."""
        membership = TeamMembership(
            workspace_id=uuid4(),
            user_id=uuid4(),
            role=MemberRole.VIEWER.value,
        )
        
        assert membership.can_edit() is False
        assert membership.can_manage_members() is False
        assert membership.can_delete() is False


class TestWorkspaceInvite:
    """Test WorkspaceInvite model."""

    def test_invite_creation(self):
        """Test creating an invite."""
        invite = WorkspaceInvite(
            workspace_id=uuid4(),
            inviter_id=uuid4(),
            email="test@example.com",
            role=MemberRole.VIEWER.value,
            invite_token="test-token-123",
            status=InviteStatus.PENDING.value,  # Explicitly set since no DB session
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        
        assert invite.email == "test@example.com"
        assert invite.status == InviteStatus.PENDING.value

    def test_is_expired_false(self):
        """Test that non-expired invite is not expired."""
        invite = WorkspaceInvite(
            workspace_id=uuid4(),
            inviter_id=uuid4(),
            email="test@example.com",
            invite_token="test-token",
            status=InviteStatus.PENDING.value,  # Explicitly set since no DB session
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        
        assert invite.is_expired() is False
        assert invite.is_pending() is True

    def test_is_expired_true(self):
        """Test that expired invite is expired."""
        invite = WorkspaceInvite(
            workspace_id=uuid4(),
            inviter_id=uuid4(),
            email="test@example.com",
            invite_token="test-token",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        
        assert invite.is_expired() is True
        assert invite.is_pending() is False

    def test_is_pending_false_when_accepted(self):
        """Test that accepted invite is not pending."""
        invite = WorkspaceInvite(
            workspace_id=uuid4(),
            inviter_id=uuid4(),
            email="test@example.com",
            invite_token="test-token",
            status=InviteStatus.ACCEPTED.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        
        assert invite.is_pending() is False
