/**
 * Hub API Client — agent clients, access ledger, erasure receipts, imports.
 */

import { apiClient } from "@/lib/api-client";
import { getAccessToken } from "@/lib/api-client";

export interface AgentClientResponse {
  id: string;
  name: string;
  scopes: string[];
  status: "active" | "revoked";
  created_at: string;
  last_used_at: string | null;
  revoked_at: string | null;
}

export interface AgentClientCreated extends AgentClientResponse {
  /** Plaintext token — shown exactly once at registration time. */
  token: string;
}

export interface AccessLogItem {
  id: string;
  agent_client_id: string | null;
  action: string;
  memory_id: string | null;
  detail: Record<string, unknown>;
  created_at: string;
}

export interface AccessLogListResponse {
  items: AccessLogItem[];
  total: number;
}

export interface ErasureReceiptItem {
  id: string;
  status: string;
  requested_memory_ids: string[];
  detail: {
    requested_by?: string;
    targets?: Array<{
      memory_id: string;
      status: string;
      error?: string;
      affected_memory_ids?: string[];
      vectors_deleted?: string[];
      vector_residual?: string[];
      vector_residual_checked?: boolean;
      db_residual?: { children: number; entity_links: number; source_links: number };
      depth_capped?: boolean;
      vectors_unverified_depth_cap?: number;
    }>;
    summary?: {
      requested: number;
      erased: number;
      skipped: number;
      errors: number;
      residual_vectors: number;
      residual_rows: number;
    };
  };
  created_at: string;
}

export interface ErasureReceiptListResponse {
  items: ErasureReceiptItem[];
  total: number;
}

export interface ImportSummary {
  parsed: number;
  created: number;
  skipped_duplicates: number;
  failed: number;
  index_failures: number;
}

// ── Agent clients ────────────────────────────────────────────────────────────

export async function listAgentClients(): Promise<AgentClientListResponse> {
  return apiClient.get<AgentClientListResponse>("/api/v1/agents");
}

export async function registerAgentClient(
  name: string,
  scopes: string[]
): Promise<AgentClientCreated> {
  return apiClient.post<AgentClientCreated>("/api/v1/agents", { name, scopes });
}

export async function revokeAgentClient(clientId: string): Promise<void> {
  await apiClient.delete(`/api/v1/agents/${clientId}`);
}

export async function fetchAccessLog(
  agentClientId?: string,
  limit = 50,
  offset = 0
): Promise<AccessLogListResponse> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (agentClientId) params.set("agent_client_id", agentClientId);
  return apiClient.get<AccessLogListResponse>(`/api/v1/agents/access-log?${params}`);
}

// ── Erasure receipts ────────────────────────────────────────────────────────

export async function listErasureReceipts(
  limit = 50,
  offset = 0
): Promise<ErasureReceiptListResponse> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return apiClient.get<ErasureReceiptListResponse>(`/api/v1/erasure-receipts?${params}`);
}

export async function requestErasure(memoryIds: string[]): Promise<ErasureReceiptItem> {
  return apiClient.post<ErasureReceiptItem>("/api/v1/erasure-receipts", {
    memory_ids: memoryIds,
  });
}

// ── Imports ─────────────────────────────────────────────────────────────────

export async function importExportFile(
  file: File,
  sourceFormat: string
): Promise<ImportSummary> {
  const form = new FormData();
  form.append("file", file);
  if (sourceFormat && sourceFormat !== "auto") form.append("source_format", sourceFormat);
  const res = await fetch(`${apiClient.getBaseUrl()}/api/v1/imports`, {
    method: "POST",
    headers: { Authorization: `Bearer ${getAccessToken() || ""}` },
    body: form,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Import failed (${res.status})`);
  }
  return res.json();
}



interface AgentClientListResponse {
  items: AgentClientResponse[];
  total: number;
}
