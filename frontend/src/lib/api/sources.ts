/**
 * Sources API Client
 * Handles source/document management with the backend
 */

import { apiClient } from "@/lib/api-client";

export interface Source {
  id: string;
  source_type: "manual" | "file_upload" | "google_drive" | "notion" | "gmail" | "web_clipper" | "rss" | "calendar" | "twitter" | "other";
  display_name: string;
  description?: string;
  status: "connected" | "syncing" | "error" | "paused" | "disconnected";
  config?: Record<string, any>;
  last_synced_at?: string;
  created_at: string;
  updated_at: string;
}

export interface SourceCreate {
  source_type: Source["source_type"];
  display_name: string;
  description?: string;
  config?: Record<string, any>;
}

export interface SourceSyncResult {
  source_id: string;
  memories_added: number;
  memories_updated: number;
  errors: number;
  finished_at: string;
}

// Re-export for convenience
export type Document = Source;
export type DocumentUploaderProps = SourceCreate;

/**
 * List sources (documents)
 */
export async function listSources(params?: {
  source_type?: Source["source_type"];
  status?: Source["status"];
  limit?: number;
  offset?: number;
}): Promise<{ items: Source[]; total: number; limit: number; offset: number }> {
  const searchParams = new URLSearchParams();
  
  if (params?.source_type) searchParams.set("source_type", params.source_type);
  if (params?.status) searchParams.set("status", params.status);
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  
  const query = searchParams.toString();
  return apiClient.get<{ items: Source[]; total: number; limit: number; offset: number }>(
    `/api/v1/sources${query ? `?${query}` : ""}`
  );
}

/**
 * Alias for listSources - documents
 */
export const listDocuments = listSources;

/**
 * Get a single source
 */
export async function getSource(id: string): Promise<Source> {
  return apiClient.get<Source>(`/api/v1/sources/${id}`);
}

/**
 * Create a new source
 */
export async function createSource(params: SourceCreate): Promise<Source> {
  return apiClient.post<Source>("/api/v1/sources", params);
}

/**
 * Update a source
 */
export async function updateSource(
  id: string,
  params: Partial<SourceCreate>
): Promise<Source> {
  return apiClient.patch<Source>(`/api/v1/sources/${id}`, params);
}

/**
 * Delete a source
 */
export async function deleteSource(id: string): Promise<void> {
  return apiClient.delete(`/api/v1/sources/${id}`);
}

/**
 * Trigger sync for a source
 */
export async function syncSource(id: string): Promise<SourceSyncResult> {
  return apiClient.post<SourceSyncResult>(`/api/v1/sources/${id}/sync`);
}

// Re-export aliases
export const getDocument = getSource;
export const createDocument = createSource;
export const updateDocument = updateSource;
export const deleteDocument = deleteSource;
export const syncDocument = syncSource;

/**
 * File upload helper
 * Note: File uploads use multipart/form-data, not JSON
 */
export async function uploadDocument(
  file: File,
  options?: {
    display_name?: string;
    description?: string;
    onProgress?: (progress: number) => void;
  }
): Promise<Source> {
  const formData = new FormData();
  formData.append("file", file);
  if (options?.display_name) formData.append("display_name", options.display_name);
  if (options?.description) formData.append("description", options.description);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable && options?.onProgress) {
        options.onProgress(Math.round((e.loaded / e.total) * 100));
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const data = JSON.parse(xhr.responseText);
        resolve(data);
      } else {
        reject(new Error(`Upload failed: ${xhr.status}`));
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Upload failed"));
    });

    xhr.open("POST", `${apiClient.getBaseUrl()}/api/v1/sources`);
    
    // Use apiClient's token management
    const token = typeof window !== "undefined" 
      ? localStorage.getItem("auth_token") 
      : null;
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    xhr.send(formData);
  });
}
