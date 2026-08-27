/**
 * Memories API Client
 * Handles memory/entity management with the backend
 */

import { apiClient } from "@/lib/api-client";

export interface Memory {
  id: string;
  type: "entity" | "relationship" | "observation" | "concept";
  name: string;
  description?: string;
  content?: string;
  metadata?: Record<string, any>;
  importance_score?: number;
  source_document_ids?: string[];
  created_at: Date;
  updated_at: Date;
  last_accessed_at?: Date;
  access_count: number;
  tags?: string[];
}

export interface MemoryConnection {
  id: string;
  source_id: string;
  target_id: string;
  relationship_type: string;
  strength: number;
  created_at: Date;
}

export interface MemoryStats {
  total_memories: number;
  entities: number;
  relationships: number;
  observations: number;
  concepts: number;
  recent_activity: {
    date: string;
    count: number;
  }[];
  top_tags: {
    tag: string;
    count: number;
  }[];
}

export interface CreateMemoryParams {
  name: string;
  type: Memory["type"];
  description?: string;
  content?: string;
  metadata?: Record<string, any>;
  importance_score?: number;
  source_document_ids?: string[];
  tags?: string[];
}

export interface UpdateMemoryParams {
  name?: string;
  description?: string;
  content?: string;
  metadata?: Record<string, any>;
  importance_score?: number;
  tags?: string[];
}

/**
 * List memories with optional filters
 */
export async function listMemories(params?: {
  type?: Memory["type"];
  tags?: string[];
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<Memory[]> {
  const searchParams = new URLSearchParams();
  
  if (params?.type) searchParams.set("type", params.type);
  if (params?.tags?.length) searchParams.set("tags", params.tags.join(","));
  if (params?.search) searchParams.set("search", params.search);
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  
  const query = searchParams.toString();
  const data = await apiClient.get<{ memories: any[] }>(`/api/v1/memories${query ? `?${query}` : ""}`);
  
  return data.memories.map((m: any) => ({
    ...m,
    created_at: new Date(m.created_at),
    updated_at: new Date(m.updated_at),
    last_accessed_at: m.last_accessed_at ? new Date(m.last_accessed_at) : undefined,
  }));
}

/**
 * Get a single memory by ID
 */
export async function getMemory(id: string): Promise<Memory> {
  const data = await apiClient.get<any>(`/api/v1/memories/${id}`);
  return {
    ...data,
    created_at: new Date(data.created_at),
    updated_at: new Date(data.updated_at),
    last_accessed_at: data.last_accessed_at ? new Date(data.last_accessed_at) : undefined,
  };
}

/**
 * Create a new memory
 */
export async function createMemory(params: CreateMemoryParams): Promise<Memory> {
  const data = await apiClient.post<any>("/api/v1/memories", params);
  return {
    ...data,
    created_at: new Date(data.created_at),
    updated_at: new Date(data.updated_at),
  };
}

/**
 * Update a memory
 */
export async function updateMemory(id: string, params: UpdateMemoryParams): Promise<Memory> {
  const data = await apiClient.patch<any>(`/api/v1/memories/${id}`, params);
  return {
    ...data,
    created_at: new Date(data.created_at),
    updated_at: new Date(data.updated_at),
  };
}

/**
 * Delete a memory
 */
export async function deleteMemory(id: string): Promise<void> {
  return apiClient.delete(`/api/v1/memories/${id}`);
}

/**
 * Get memory statistics
 */
export async function getMemoryStats(): Promise<MemoryStats> {
  return apiClient.get<MemoryStats>("/api/v1/memories/stats");
}

/**
 * Get related memories (connections)
 */
export async function getRelatedMemories(id: string): Promise<MemoryConnection[]> {
  const data = await apiClient.get<{ connections: any[] }>(`/api/v1/memories/${id}/connections`);
  return data.connections.map((c: any) => ({
    ...c,
    created_at: new Date(c.created_at),
  }));
}

/**
 * Search memories by semantic similarity
 */
export async function searchMemories(query: string, limit = 10): Promise<Memory[]> {
  const data = await apiClient.post<{ results: any[] }>("/api/v1/memories/search", { query, limit });
  return data.results.map((m: any) => ({
    ...m,
    created_at: new Date(m.created_at),
    updated_at: new Date(m.updated_at),
  }));
}

/**
 * Bulk delete memories
 */
export async function bulkDeleteMemories(ids: string[]): Promise<{ deleted: number }> {
  return apiClient.post<{ deleted: number }>("/api/v1/memories/bulk-delete", { ids });
}
