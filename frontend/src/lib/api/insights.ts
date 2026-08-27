/**
 * API client for Insight Cards
 * Uses centralized apiClient for consistent API calls
 */

import { apiClient } from "@/lib/api-client";
import type {
  InsightListResponse,
  InsightGenerateRequest,
  InsightGenerateResponse,
  InsightFeedbackRequest,
  InsightRefreshResponse,
  InsightResponse,
} from "@/types/insights";

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
  return apiClient.get<InsightListResponse>(`/api/v1/insights${query ? `?${query}` : ""}`);
}

export async function generateInsights(
  request: InsightGenerateRequest
): Promise<InsightGenerateResponse> {
  return apiClient.post<InsightGenerateResponse>("/api/v1/insights/generate", request);
}

export async function getInsight(insightId: string): Promise<InsightResponse> {
  return apiClient.get<InsightResponse>(`/api/v1/insights/${insightId}`);
}

export async function dismissInsight(
  insightId: string
): Promise<InsightResponse> {
  return apiClient.post<InsightResponse>(`/api/v1/insights/${insightId}/dismiss`, {});
}

export async function saveInsight(
  insightId: string
): Promise<InsightResponse> {
  return apiClient.post<InsightResponse>(`/api/v1/insights/${insightId}/save`, {});
}

export async function feedbackInsight(
  insightId: string,
  feedback: InsightFeedbackRequest
): Promise<InsightResponse> {
  return apiClient.post<InsightResponse>(
    `/api/v1/insights/${insightId}/feedback`,
    feedback
  );
}

export async function refreshInsights(): Promise<InsightRefreshResponse> {
  return apiClient.post<InsightRefreshResponse>("/api/v1/insights/refresh", {});
}
