/**
 * Analytics API Client
 * Handles workspace analytics and statistics
 */

import { apiClient } from "@/lib/api-client";

export interface FeatureUsageItem {
  feature: string;
  action: string;
  count: number;
}

export interface PageViewItem {
  path: string;
  views: number;
}

export interface DAUItem {
  date: string;
  active_users: number;
}

export interface FeatureUsageResponse {
  items: FeatureUsageItem[];
  total: number;
}

export interface PageViewsResponse {
  items: PageViewItem[];
  total: number;
}

export interface DAUResponse {
  items: DAUItem[];
}

/**
 * Get feature usage statistics
 */
export async function getFeatureUsage(days = 7): Promise<FeatureUsageResponse> {
  return apiClient.get<FeatureUsageResponse>(`/api/v1/analytics/usage?days=${days}`);
}

/**
 * Get page view statistics
 */
export async function getPageViews(days = 7): Promise<PageViewsResponse> {
  return apiClient.get<PageViewsResponse>(`/api/v1/analytics/pages?days=${days}`);
}

/**
 * Get daily active users
 */
export async function getDAUStats(days = 7): Promise<DAUResponse> {
  return apiClient.get<DAUResponse>(`/api/v1/analytics/dau?days=${days}`);
}

/**
 * Record analytics events
 */
export async function recordAnalyticsEvents(events: Array<{
  name: string;
  properties?: Record<string, string | number | boolean>;
  timestamp?: number;
}>): Promise<{ recorded: number }> {
  return apiClient.post<{ recorded: number }>("/api/v1/analytics/events", {
    events,
  });
}
