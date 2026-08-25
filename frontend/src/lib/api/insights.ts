/**
 * API client for Insight Cards
 */

import type {
  InsightListResponse,
  InsightGenerateRequest,
  InsightGenerateResponse,
  InsightFeedbackRequest,
  InsightRefreshResponse,
  InsightResponse,
} from "@/types/insights";

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

export async function listInsights(params?: {
  status?: string;
  insight_type?: string;
  limit?: number;
  offset?: number;
}): Promise<InsightListResponse> {
  const searchParams = new URLSearchParams();
  
  if (params?.status) searchParams.set("status", params.status);
  if (params?.insight_type) searchParams.set("insight_type", params.insight_type);
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));

  const query = searchParams.toString();
  return fetchWithAuth<InsightListResponse>(`/insights${query ? `?${query}` : ""}`);
}

export async function generateInsights(
  request: InsightGenerateRequest
): Promise<InsightGenerateResponse> {
  return fetchWithAuth<InsightGenerateResponse>("/insights/generate", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getInsight(insightId: string): Promise<InsightResponse> {
  return fetchWithAuth<InsightResponse>(`/insights/${insightId}`);
}

export async function dismissInsight(
  insightId: string
): Promise<InsightResponse> {
  return fetchWithAuth<InsightResponse>(`/insights/${insightId}/dismiss`, {
    method: "POST",
  });
}

export async function saveInsight(
  insightId: string
): Promise<InsightResponse> {
  return fetchWithAuth<InsightResponse>(`/insights/${insightId}/save`, {
    method: "POST",
  });
}

export async function feedbackInsight(
  insightId: string,
  feedback: InsightFeedbackRequest
): Promise<InsightResponse> {
  return fetchWithAuth<InsightResponse>(`/insights/${insightId}/feedback`, {
    method: "POST",
    body: JSON.stringify(feedback),
  });
}

export async function refreshInsights(): Promise<InsightRefreshResponse> {
  return fetchWithAuth<InsightRefreshResponse>("/insights/refresh", {
    method: "POST",
  });
}
