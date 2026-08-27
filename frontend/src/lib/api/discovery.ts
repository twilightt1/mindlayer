/**
 * API client for Discovery
 * Uses centralized apiClient for consistent API calls
 */

import { apiClient } from "@/lib/api-client";
import type {
  GraphResponse,
  DiscoverySession,
  DiscoveryStep,
  CrossReference,
  DiscoveryInsight,
  GraphMetrics,
  SessionListResponse,
  DiscoveryGenerateRequest,
} from "@/types/discovery";

export async function getDocumentGraph(docIds?: string[]): Promise<GraphResponse> {
  const params = docIds ? `?doc_ids=${docIds.join(",")}` : "";
  return apiClient.get<GraphResponse>(`/api/v1/discovery/graph${params}`);
}

export async function createDiscoverySession(
  request: DiscoveryGenerateRequest
): Promise<DiscoverySession> {
  return apiClient.post<DiscoverySession>("/api/v1/discovery/sessions", request);
}

export async function listDiscoverySessions(params?: {
  limit?: number;
  offset?: number;
  status?: string;
}): Promise<SessionListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  if (params?.status) searchParams.set("status", params.status);

  const query = searchParams.toString();
  return apiClient.get<SessionListResponse>(
    `/api/v1/discovery/sessions${query ? `?${query}` : ""}`
  );
}

export async function getDiscoverySession(sessionId: string): Promise<DiscoverySession> {
  return apiClient.get<DiscoverySession>(`/api/v1/discovery/sessions/${sessionId}`);
}

export async function getNextDiscoveryStep(sessionId: string): Promise<DiscoveryStep> {
  return apiClient.get<DiscoveryStep>(`/api/v1/discovery/sessions/${sessionId}/step`);
}

export async function advanceDiscovery(sessionId: string): Promise<DiscoverySession> {
  return apiClient.post<DiscoverySession>(`/api/v1/discovery/sessions/${sessionId}/advance`, {});
}

export async function completeDiscovery(sessionId: string): Promise<DiscoverySession> {
  return apiClient.post<DiscoverySession>(`/api/v1/discovery/sessions/${sessionId}/complete`, {});
}

export async function getDiscoverySynthesis(sessionId: string): Promise<DiscoveryInsight> {
  return apiClient.post<DiscoveryInsight>(`/api/v1/discovery/sessions/${sessionId}/synthesis`, {});
}

export async function findCrossReferences(
  doc1Id: string,
  doc2Id: string
): Promise<CrossReference[]> {
  return apiClient.get<CrossReference[]>(
    `/api/v1/discovery/references?doc1_id=${doc1Id}&doc2_id=${doc2Id}`
  );
}

export async function getGraphMetrics(): Promise<GraphMetrics> {
  return apiClient.get<GraphMetrics>("/api/v1/discovery/metrics");
}
