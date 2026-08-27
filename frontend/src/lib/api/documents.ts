/**
 * Documents API Client
 * Handles document upload, processing, and management
 */

import { apiClient } from "@/lib/api-client";

export interface Document {
  id: string;
  filename: string;
  title?: string;
  file_type: string;
  file_size: number;
  status: "processing" | "ready" | "error" | "partial";
  processing_progress?: number;
  error_message?: string;
  workspace_id?: string;
  tags?: string[];
  metadata?: {
    page_count?: number;
    word_count?: number;
    author?: string;
    created_date?: string;
    [key: string]: any;
  };
  summary?: string;
  created_at: Date;
  updated_at: Date;
  last_accessed_at?: Date;
}

export interface UploadedFile {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: Document["status"];
}

export interface UploadProgress {
  documentId: string;
  progress: number;
  status: "uploading" | "processing" | "ready" | "error";
  message?: string;
}

export interface UploadParams {
  file: File;
  workspace_id?: string;
  title?: string;
  tags?: string[];
  metadata?: Record<string, any>;
  onProgress?: (progress: UploadProgress) => void;
}

/**
 * Upload a document with progress tracking
 */
export async function uploadDocument({
  file,
  workspace_id,
  title,
  tags,
  metadata,
  onProgress,
}: UploadParams): Promise<Document> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", file);
    if (workspace_id) formData.append("workspace_id", workspace_id);
    if (title) formData.append("title", title);
    if (tags?.length) formData.append("tags", JSON.stringify(tags));
    if (metadata) formData.append("metadata", JSON.stringify(metadata));

    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress({
          documentId: "",
          progress: Math.round((e.loaded / e.total) * 50), // First 50% is upload
          status: "uploading",
          message: `Uploading: ${Math.round((e.loaded / e.total) * 100)}%`,
        });
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const data = JSON.parse(xhr.responseText);
        resolve({
          ...data,
          created_at: new Date(data.created_at),
          updated_at: new Date(data.updated_at),
        });
      } else {
        reject(new Error(`Upload failed: ${xhr.status}`));
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Upload failed"));
    });

    // Use apiClient's baseUrl for consistency
    const baseUrl = apiClient.getBaseUrl();
    xhr.open("POST", `${baseUrl}/api/v1/documents`);
    
    // Add auth header
    const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    xhr.send(formData);
  });
}

/**
 * List documents with optional filters
 */
export async function listDocuments(params?: {
  workspace_id?: string;
  status?: Document["status"];
  tags?: string[];
  search?: string;
  limit?: number;
  offset?: number;
  sort_by?: "created_at" | "updated_at" | "filename";
  sort_order?: "asc" | "desc";
}): Promise<{ documents: Document[]; total: number }> {
  const searchParams = new URLSearchParams();

  if (params?.workspace_id) searchParams.set("workspace_id", params.workspace_id);
  if (params?.status) searchParams.set("status", params.status);
  if (params?.tags?.length) searchParams.set("tags", params.tags.join(","));
  if (params?.search) searchParams.set("search", params.search);
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  if (params?.sort_by) searchParams.set("sort_by", params.sort_by);
  if (params?.sort_order) searchParams.set("sort_order", params.sort_order);

  const query = searchParams.toString();
  return apiClient.get<{ documents: Document[]; total: number }>(
    `/api/v1/documents${query ? `?${query}` : ""}`
  );
}

/**
 * Get a single document by ID
 */
export async function getDocument(id: string): Promise<Document> {
  return apiClient.get<Document>(`/api/v1/documents/${id}`);
}

/**
 * Update document metadata
 */
export async function updateDocument(
  id: string,
  params: { title?: string; tags?: string[]; metadata?: Record<string, any> }
): Promise<Document> {
  return apiClient.patch<Document>(`/api/v1/documents/${id}`, params);
}

/**
 * Delete a document
 */
export async function deleteDocument(id: string): Promise<void> {
  return apiClient.delete(`/api/v1/documents/${id}`);
}

/**
 * Download a document
 */
export async function downloadDocument(id: string): Promise<Blob> {
  const response = await fetch(`${apiClient.getBaseUrl()}/api/v1/documents/${id}/download`, {
    headers: apiClient.getHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to download document: ${response.status}`);
  }

  return response.blob();
}

/**
 * Reprocess a document
 */
export async function reprocessDocument(id: string): Promise<Document> {
  return apiClient.post<Document>(`/api/v1/documents/${id}/reprocess`, {});
}

/**
 * Get document content/text
 */
export async function getDocumentContent(id: string): Promise<string> {
  const data = await apiClient.get<{ content: string }>(`/api/v1/documents/${id}/content`);
  return data.content;
}

/**
 * Bulk delete documents
 */
export async function bulkDeleteDocuments(ids: string[]): Promise<{ deleted: number }> {
  return apiClient.post<{ deleted: number }>("/api/v1/documents/bulk-delete", { ids });
}

/**
 * Get document processing status (for SSE/polling updates)
 */
export async function getDocumentStatus(id: string): Promise<{
  status: Document["status"];
  progress?: number;
  error_message?: string;
}> {
  return apiClient.get<{ status: Document["status"]; progress?: number; error_message?: string }>(
    `/api/v1/documents/${id}/status`
  );
}

/**
 * Get supported file types
 */
export const SUPPORTED_FILE_TYPES = {
  pdf: { extensions: [".pdf"], icon: "📄", label: "PDF" },
  doc: { extensions: [".doc", ".docx"], icon: "📝", label: "Word Document" },
  text: { extensions: [".txt", ".md", ".rtf"], icon: "📃", label: "Text File" },
  spreadsheet: { extensions: [".xls", ".xlsx", ".csv"], icon: "📊", label: "Spreadsheet" },
  image: { extensions: [".jpg", ".jpeg", ".png", ".gif", ".webp"], icon: "🖼️", label: "Image" },
  url: { extensions: [], icon: "🔗", label: "Web URL" },
};

export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
export const MAX_FILES_PER_BATCH = 10;
