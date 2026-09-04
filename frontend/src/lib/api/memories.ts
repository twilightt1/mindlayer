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

/**
 * Backend MemoryResponse uses a different shape (title/content/source_type/
 * recall_count...). Map it onto the client Memory interface the UI renders.
 * `type` is derived from source_type since the backend has no memory-type
 * column; entity/relationship/concept are graph artifacts.
 */
export function mapBackendMemory(m: any): Memory {
  const sourceType = String(m.source_type || "other");
  const type: Memory["type"] = sourceType.includes("conversation")
    ? "observation"
    : sourceType === "manual_note"
      ? "concept"
      : "entity";
  return {
    id: m.id,
    type,
    name: m.title || m.summary || sourceType,
    description: m.summary || undefined,
    content: m.content,
    metadata: m.metadata,
    importance_score: m.salience,
    source_document_ids: m.source_ref ? [m.source_ref] : undefined,
    created_at: new Date(m.captured_at ?? m.created_at),
    updated_at: new Date(m.updated_at),
    last_accessed_at: m.last_used_at ? new Date(m.last_used_at) : undefined,
    access_count: m.recall_count ?? 0,
    tags: m.tags ?? [],
  };
}

function mapListResponse(data: { items?: any[]; memories?: any[] }): Memory[] {
  const rows = data.items ?? data.memories ?? [];
  return rows.map(mapBackendMemory);
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

  // Backend filter params (source_type/tag/query), mapped from client params
  if (params?.search) searchParams.set("query", params.search);
  if (params?.tags?.length) searchParams.set("tag", params.tags[0]);
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));

  const query = searchParams.toString();
  const data = await apiClient.get<{ items: any[]; memories?: any[] }>(`/api/v1/memories${query ? `?${query}` : ""}`);

  return mapListResponse(data);
}

/**
 * Get a single memory by ID
 */
export async function getMemory(id: string): Promise<Memory> {
  const data = await apiClient.get<any>(`/api/v1/memories/${id}`);
  return mapBackendMemory(data);
}

/**
 * Create a new memory
 */
export async function createMemory(params: CreateMemoryParams): Promise<Memory> {
  // Backend expects MemoryCreate: title/content/summary/source_type/tags...
  const data = await apiClient.post<any>("/api/v1/memories", {
    title: params.name,
    content: params.content ?? params.description ?? params.name,
    summary: params.description,
    source_type: "manual_note",
    tags: params.tags,
    metadata: params.metadata,
  });
  return mapBackendMemory(data);
}

/**
 * Update a memory
 */
export async function updateMemory(id: string, params: UpdateMemoryParams): Promise<Memory> {
  const data = await apiClient.patch<any>(`/api/v1/memories/${id}`, {
    ...(params.name !== undefined ? { title: params.name } : {}),
    ...(params.description !== undefined ? { summary: params.description } : {}),
    ...(params.content !== undefined ? { content: params.content } : {}),
    ...(params.importance_score !== undefined ? { salience: params.importance_score } : {}),
    ...(params.tags !== undefined ? { tags: params.tags } : {}),
    ...(params.metadata !== undefined ? { metadata: params.metadata } : {}),
  });
  return mapBackendMemory(data);
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
  // Backend list endpoint supports a `query` substring filter (no separate
  // /search route). POST /recall is LLM-quota-gated — too heavy for typing.
  const searchParams = new URLSearchParams({ query, limit: String(limit) });
  const data = await apiClient.get<{ items: any[]; memories?: any[] }>(`/api/v1/memories?${searchParams.toString()}`);
  return mapListResponse(data);
}

/**
 * Bulk delete memories
 */
export async function bulkDeleteMemories(ids: string[]): Promise<{ deleted: number }> {
  return apiClient.post<{ deleted: number }>("/api/v1/memories/bulk-delete", { ids });
}
