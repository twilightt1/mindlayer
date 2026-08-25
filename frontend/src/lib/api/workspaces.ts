/**
 * API client for Workspaces
 */

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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// ─── Workspaces ────────────────────────────────────────────────────────────────

export async function listWorkspaces(workspaceType?: string): Promise<WorkspaceListResponse> {
  const params = workspaceType ? `?workspace_type=${workspaceType}` : "";
  return fetchWithAuth<WorkspaceListResponse>(`/workspaces${params}`);
}

export async function createWorkspace(data: WorkspaceCreate): Promise<Workspace> {
  return fetchWithAuth<Workspace>("/workspaces", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getWorkspace(workspaceId: string): Promise<Workspace> {
  return fetchWithAuth<Workspace>(`/workspaces/${workspaceId}`);
}

export async function updateWorkspace(
  workspaceId: string,
  data: WorkspaceUpdate
): Promise<Workspace> {
  return fetchWithAuth<Workspace>(`/workspaces/${workspaceId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteWorkspace(workspaceId: string): Promise<void> {
  return fetchWithAuth<void>(`/workspaces/${workspaceId}`, {
    method: "DELETE",
  });
}

// ─── Members ──────────────────────────────────────────────────────────────────

export async function listMembers(workspaceId: string): Promise<MemberListResponse> {
  return fetchWithAuth<MemberListResponse>(`/workspaces/${workspaceId}/members`);
}

export async function addMember(
  workspaceId: string,
  userId: string,
  role: MemberRole = "viewer"
): Promise<TeamMember> {
  return fetchWithAuth<TeamMember>(
    `/workspaces/${workspaceId}/members?user_id=${userId}&role=${role}`,
    { method: "POST" }
  );
}

export async function updateMemberRole(
  workspaceId: string,
  userId: string,
  role: MemberRole
): Promise<TeamMember> {
  return fetchWithAuth<TeamMember>(`/workspaces/${workspaceId}/members/${userId}`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

export async function removeMember(workspaceId: string, userId: string): Promise<void> {
  return fetchWithAuth<void>(`/workspaces/${workspaceId}/members/${userId}`, {
    method: "DELETE",
  });
}

// ─── Invites ──────────────────────────────────────────────────────────────────

export async function listInvites(workspaceId: string): Promise<InviteListResponse> {
  return fetchWithAuth<InviteListResponse>(`/workspaces/${workspaceId}/invites`);
}

export async function createInvite(
  workspaceId: string,
  data: InviteCreate
): Promise<WorkspaceInvite> {
  return fetchWithAuth<WorkspaceInvite>(`/workspaces/${workspaceId}/invites`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function cancelInvite(
  workspaceId: string,
  inviteId: string
): Promise<void> {
  return fetchWithAuth<void>(`/workspaces/${workspaceId}/invites/${inviteId}`, {
    method: "DELETE",
  });
}

export async function acceptInvite(inviteToken: string): Promise<TeamMember> {
  return fetchWithAuth<TeamMember>(`/workspaces/invites/${inviteToken}/accept`, {
    method: "POST",
  });
}
