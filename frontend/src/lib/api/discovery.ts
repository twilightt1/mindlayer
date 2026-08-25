/**
 * API client for Discovery
 */

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

  return response.json();
}

export async function getDocumentGraph(docIds?: string[]): Promise<GraphResponse> {
  const params = docIds ? `?doc_ids=${docIds.join(",")}` : "";
  return fetchWithAuth<GraphResponse>(`/discovery/graph${params}`);
}

export async function createDiscoverySession(
  request: DiscoveryGenerateRequest
): Promise<DiscoverySession> {
  return fetchWithAuth<DiscoverySession>("/discovery/sessions", {
    method: "POST",
    body: JSON.stringify(request),
  });
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
  return fetchWithAuth<SessionListResponse>(`/discovery/sessions${query ? `?${query}` : ""}`);
}

export async function getDiscoverySession(sessionId: string): Promise<DiscoverySession> {
  return fetchWithAuth<DiscoverySession>(`/discovery/sessions/${sessionId}`);
}

export async function getNextDiscoveryStep(sessionId: string): Promise<DiscoveryStep> {
  return fetchWithAuth<DiscoveryStep>(`/discovery/sessions/${sessionId}/step`);
}

export async function advanceDiscovery(sessionId: string): Promise<DiscoverySession> {
  return fetchWithAuth<DiscoverySession>(`/discovery/sessions/${sessionId}/advance`, {
    method: "POST",
  });
}

export async function completeDiscovery(sessionId: string): Promise<DiscoverySession> {
  return fetchWithAuth<DiscoverySession>(`/discovery/sessions/${sessionId}/complete`, {
    method: "POST",
  });
}

export async function getDiscoverySynthesis(sessionId: string): Promise<DiscoveryInsight> {
  return fetchWithAuth<DiscoveryInsight>(`/discovery/sessions/${sessionId}/synthesis`, {
    method: "POST",
  });
}

export async function findCrossReferences(
  doc1Id: string,
  doc2Id: string
): Promise<CrossReference[]> {
  return fetchWithAuth<CrossReference[]>(
    `/discovery/references?doc1_id=${doc1Id}&doc2_id=${doc2Id}`
  );
}

export async function getGraphMetrics(): Promise<GraphMetrics> {
  return fetchWithAuth<GraphMetrics>("/discovery/metrics");
}
