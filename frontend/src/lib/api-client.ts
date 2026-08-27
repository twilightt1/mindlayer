/**
 * API Client Configuration
 * Central configuration for all API calls
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const API_CONFIG = {
  baseUrl: API_BASE,
  endpoints: {
    // Auth
    login: `${API_BASE}/api/v1/auth/login`,
    register: `${API_BASE}/api/v1/auth/register`,
    logout: `${API_BASE}/api/v1/auth/logout`,
    refresh: `${API_BASE}/api/v1/auth/refresh`,
    me: `${API_BASE}/api/v1/users/me`,
    
    // Chat
    chat: `${API_BASE}/api/v1/chat`,
    chatSessions: `${API_BASE}/api/v1/chat/sessions`,
    
    // Memories
    memories: `${API_BASE}/api/v1/memories`,
    memoryStats: `${API_BASE}/api/v1/memories/stats`,
    memorySearch: `${API_BASE}/api/v1/memories/search`,
    
    // Documents
    documents: `${API_BASE}/api/v1/sources`,
    documentUpload: `${API_BASE}/api/v1/sources/upload`,
    
    // Insights
    insights: `${API_BASE}/api/v1/insights`,
    
    // Discovery
    discovery: `${API_BASE}/api/v1/discovery`,
    
    // Workspaces
    workspaces: `${API_BASE}/api/v1/workspaces`,
    
    // Analytics
    analytics: `${API_BASE}/api/v1/analytics`,
  },
};

// ============================================================================
// TOKEN MANAGEMENT
// ============================================================================

const TOKEN_KEY = "auth_token";
const REFRESH_KEY = "refresh_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(accessToken: string, refreshToken?: string | null) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_KEY, refreshToken);
  }
}

export function clearTokens() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

// ============================================================================
// API CLIENT
// ============================================================================

export interface ApiError {
  detail?: string;
  message?: string;
  [key: string]: any;
}

export class ApiClient {
  private baseUrl: string;
  private token: string | null;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
    this.token = getAccessToken();
  }

  setToken(token: string | null) {
    this.token = token;
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "GET",
      headers: this.getHeaders(),
    });
    return this.handleResponse<T>(response);
  }

  async post<T>(endpoint: string, body?: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "POST",
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });
    return this.handleResponse<T>(response);
  }

  async patch<T>(endpoint: string, body?: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "PATCH",
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });
    return this.handleResponse<T>(response);
  }

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "DELETE",
      headers: this.getHeaders(),
    });
    return this.handleResponse<T>(response);
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || error.message || `HTTP ${response.status}`);
    }
    return response.json();
  }
}

// Default client instance
export const apiClient = new ApiClient();

// ============================================================================
// SSE STREAMING
// ============================================================================

export function createSSEStream(
  endpoint: string,
  callbacks: {
    onChunk?: (data: any) => void;
    onComplete?: () => void;
    onError?: (error: Error) => void;
  },
  body?: any
): { abort: () => void } {
  let aborted = false;
  const controller = new AbortController();

  const makeRequest = async () => {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
          Authorization: `Bearer ${getAccessToken()}`,
        },
        body: body ? JSON.stringify({ ...body, stream: true }) : JSON.stringify({ stream: true }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`SSE error: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("Response body is null");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        if (aborted) break;

        const { done, value } = await reader.read();
        
        if (done) {
          callbacks.onComplete?.();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          if (trimmed.startsWith("data: ")) {
            const data = trimmed.slice(6);
            try {
              const parsed = JSON.parse(data);
              callbacks.onChunk?.(parsed);
            } catch {
              callbacks.onChunk?.({ content: data });
            }
          }
        }
      }
    } catch (error) {
      if (!aborted) {
        callbacks.onError?.(error instanceof Error ? error : new Error(String(error)));
      }
    }
  };

  makeRequest();

  return {
    abort: () => {
      aborted = true;
      controller.abort();
    },
  };
}
