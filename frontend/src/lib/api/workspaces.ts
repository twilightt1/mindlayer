/**
 * API client for Workspaces
 * Uses centralized apiClient for consistent API calls
 */

import { apiClient } from "@/lib/api-client";
import type {
  Workspace,
  TeamMember,
  WorkspaceInvite,
  WorkspaceCreate,
  WorkspaceUpdate,
  InviteCreate,
  WorkspaceListResponse,
  MemberListResponse,
  InviteListResponse,
  MemberRole,
} from "@/types/workspace";

// ─── Workspaces ────────────────────────────────────────────────────────────────

export async function listWorkspaces(workspaceType?: string): Promise<WorkspaceListResponse> {
  const params = workspaceType ? `?workspace_type=${workspaceType}` : "";
  return apiClient.get<WorkspaceListResponse>(`/api/v1/workspaces${params}`);
}

export async function createWorkspace(data: WorkspaceCreate): Promise<Workspace> {
  return apiClient.post<Workspace>("/api/v1/workspaces", data);
}

export async function getWorkspace(workspaceId: string): Promise<Workspace> {
  return apiClient.get<Workspace>(`/api/v1/workspaces/${workspaceId}`);
}

export async function updateWorkspace(
  workspaceId: string,
  data: WorkspaceUpdate
): Promise<Workspace> {
  return apiClient.patch<Workspace>(`/api/v1/workspaces/${workspaceId}`, data);
}

export async function deleteWorkspace(workspaceId: string): Promise<void> {
  return apiClient.delete(`/api/v1/workspaces/${workspaceId}`);
}

// ─── Members ──────────────────────────────────────────────────────────────────

export async function listMembers(workspaceId: string): Promise<MemberListResponse> {
  return apiClient.get<MemberListResponse>(`/api/v1/workspaces/${workspaceId}/members`);
}

export async function addMember(
  workspaceId: string,
  userId: string,
  role: MemberRole = "viewer"
): Promise<TeamMember> {
  return apiClient.post<TeamMember>(
    `/api/v1/workspaces/${workspaceId}/members?user_id=${userId}&role=${role}`,
    {}
  );
}

export async function updateMemberRole(
  workspaceId: string,
  userId: string,
  role: MemberRole
): Promise<TeamMember> {
  return apiClient.patch<TeamMember>(`/api/v1/workspaces/${workspaceId}/members/${userId}`, { role });
}

export async function removeMember(workspaceId: string, userId: string): Promise<void> {
  return apiClient.delete(`/api/v1/workspaces/${workspaceId}/members/${userId}`);
}

// ─── Invites ──────────────────────────────────────────────────────────────────

export async function listInvites(workspaceId: string): Promise<InviteListResponse> {
  return apiClient.get<InviteListResponse>(`/api/v1/workspaces/${workspaceId}/invites`);
}

export async function createInvite(
  workspaceId: string,
  data: InviteCreate
): Promise<WorkspaceInvite> {
  return apiClient.post<WorkspaceInvite>(`/api/v1/workspaces/${workspaceId}/invites`, data);
}

export async function cancelInvite(
  workspaceId: string,
  inviteId: string
): Promise<void> {
  return apiClient.delete(`/api/v1/workspaces/${workspaceId}/invites/${inviteId}`);
}

export async function acceptInvite(inviteToken: string): Promise<TeamMember> {
  return apiClient.post<TeamMember>(`/api/v1/workspaces/invites/${inviteToken}/accept`, {});
}
