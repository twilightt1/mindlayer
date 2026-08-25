/**
 * TypeScript types for Workspace API
 */

export type WorkspaceType = "personal" | "team";
export type WorkspaceStatus = "active" | "archived" | "deleted";
export type MemberRole = "owner" | "admin" | "editor" | "viewer";
export type MemberStatus = "active" | "pending" | "left" | "removed";
export type InviteStatus = "pending" | "accepted" | "declined" | "expired";

export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  workspace_type: WorkspaceType;
  owner_id: string;
  organization_id: string | null;
  settings: Record<string, unknown>;
  status: WorkspaceStatus;
  created_at: string;
  updated_at: string;
  member_count: number;
}

export interface TeamMember {
  id: string;
  workspace_id: string;
  user_id: string;
  role: MemberRole;
  status: MemberStatus;
  permissions: Record<string, boolean>;
  joined_at: string;
  last_accessed_at: string | null;
}

export interface WorkspaceInvite {
  id: string;
  workspace_id: string;
  inviter_id: string;
  email: string;
  user_id: string | null;
  role: MemberRole;
  status: InviteStatus;
  message: string | null;
  created_at: string;
  expires_at: string;
  accepted_at: string | null;
}

export interface WorkspaceCreate {
  name: string;
  description?: string;
  workspace_type?: WorkspaceType;
  settings?: Record<string, unknown>;
}

export interface WorkspaceUpdate {
  name?: string;
  description?: string | null;
  settings?: Record<string, unknown>;
  status?: WorkspaceStatus;
}

export interface InviteCreate {
  email: string;
  role?: MemberRole;
  message?: string;
}

export interface WorkspaceListResponse {
  items: Workspace[];
  total: number;
}

export interface MemberListResponse {
  items: TeamMember[];
  total: number;
}

export interface InviteListResponse {
  items: WorkspaceInvite[];
  total: number;
}

// Role configuration
export const ROLE_CONFIG: Record<MemberRole, { label: string; description: string; color: string }> = {
  owner: {
    label: "Owner",
    description: "Full control including deletion",
    color: "text-amber-400",
  },
  admin: {
    label: "Admin",
    description: "Manage members and settings",
    color: "text-purple-400",
  },
  editor: {
    label: "Editor",
    description: "Add and edit content",
    color: "text-blue-400",
  },
  viewer: {
    label: "Viewer",
    description: "View content only",
    color: "text-green-400",
  },
};

// Workspace type labels
export const WORKSPACE_TYPE_CONFIG: Record<WorkspaceType, { label: string; emoji: string }> = {
  personal: {
    label: "Personal",
    emoji: "👤",
  },
  team: {
    label: "Team",
    emoji: "👥",
  },
};
