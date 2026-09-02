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
 * List all documents from all conversations
 */
export async function listDocuments(): Promise<Document[]> {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  if (!token) return [];

  try {
    // Get all conversations
    const sessionsRes = await fetch(`${apiClient.getBaseUrl()}/api/v1/chat/sessions`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const sessions = await sessionsRes.json();
    
    // Get documents for each conversation
    const allDocs: Document[] = [];
    for (const session of sessions) {
      try {
        const docsRes = await fetch(`${apiClient.getBaseUrl()}/api/v1/chat/conversations/${session.id}/documents`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (docsRes.ok) {
          const docs = await docsRes.json();
          allDocs.push(...docs);
        }
      } catch (e) {
        // Skip failed requests
      }
    }
    
    return allDocs.sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  } catch (e) {
    console.error("Failed to list documents:", e);
    return [];
  }
}

/**
 * Upload a document with progress tracking
 * Uploads to the current chat session
 */
export async function uploadDocument({
  file,
  workspace_id,
  title,
  tags,
  metadata,
  onProgress,
}: UploadParams): Promise<Document> {
  // Get the current conversation/session ID from localStorage or use default
  let sessionId = typeof window !== "undefined" ? localStorage.getItem("current_session_id") : null;
  
  // If no session, create one first
  if (!sessionId) {
    const token = localStorage.getItem("auth_token");
    const response = await fetch(`${apiClient.getBaseUrl()}/api/v1/chat/sessions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({}),
    });
    const sessions = await response.json();
    sessionId = sessions[0]?.id;
    if (sessionId) {
      localStorage.setItem("current_session_id", sessionId);
    }
  }

  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress({
          documentId: "",
          progress: Math.round((e.loaded / e.total) * 100),
          status: "uploading",
          message: `Uploading: ${Math.round((e.loaded / e.total) * 100)}%`,
        });
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const data = JSON.parse(xhr.responseText);
        // Map backend response to frontend Document format
        const doc: Document = {
          id: data.id,
          filename: data.filename,
          title: data.filename,
          file_type: data.mime_type || "application/octet-stream",
          file_size: data.file_size,
          status: data.status === "pending" ? "processing" : (data.status as Document["status"]),
          created_at: new Date(data.created_at),
          updated_at: new Date(data.updated_at),
        };
        resolve(doc);
      } else {
        reject(new Error(`Upload failed: ${xhr.status} - ${xhr.responseText}`));
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Upload failed: Network error"));
    });

    // Use apiClient's baseUrl for consistency
    const baseUrl = apiClient.getBaseUrl();
    const endpoint = sessionId 
      ? `${baseUrl}/api/v1/chat/conversations/${sessionId}/documents`
      : `${baseUrl}/api/v1/chat/documents`;
      
    xhr.open("POST", endpoint);
    
    // Add auth header
    const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    xhr.send(formData);
  });
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
 * Uses the chat endpoint to delete documents
 */
export async function deleteDocument(id: string, conversationId?: string): Promise<void> {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  if (!token) throw new Error("Not authenticated");

  // If we have the conversation ID, use the chat endpoint
  if (conversationId) {
    const response = await fetch(`${apiClient.getBaseUrl()}/api/v1/chat/conversations/${conversationId}/documents/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      throw new Error(`Failed to delete document: ${response.status}`);
    }
    return;
  }

  // Fallback: try to find the document's conversation
  // For now, we'll try to delete using the root endpoint
  try {
    const response = await fetch(`${apiClient.getBaseUrl()}/api/v1/chat/documents/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      throw new Error(`Failed to delete document: ${response.status}`);
    }
  } catch (e) {
    // If endpoint doesn't exist, just log
    console.warn("Delete endpoint may not be available:", e);
  }
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
