/**
 * SSE (Server-Sent Events) Client Utility
 * Handles streaming responses from the backend
 */

export interface SSEMessage {
  type: string;
  data: any;
}

export interface SSEOptions {
  /** Callback when a message is received */
  onMessage?: (message: SSEMessage) => void;
  /** Callback when stream completes */
  onComplete?: () => void;
  /** Callback when error occurs */
  onError?: (error: Error) => void;
  /** Custom headers to send with request */
  headers?: Record<string, string>;
  /** Request body (for POST requests) */
  body?: any;
  /** HTTP method */
  method?: "GET" | "POST";
  /** Abort signal for cancellation */
  signal?: AbortSignal;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001";

/**
 * Parse SSE data line
 */
function parseSSEData(line: string): string | null {
  if (line.startsWith("data: ")) {
    return line.slice(6);
  }
  return null;
}

/**
 * Create an SSE connection and return a cleanup function
 */
export function createSSEConnection(
  endpoint: string,
  options: SSEOptions = {}
): { abort: () => void } {
  const { 
    onMessage, 
    onComplete, 
    onError, 
    headers = {},
    body,
    method = "POST",
    signal: externalSignal
  } = options;

  let aborted = false;
  const controller = new AbortController();

  // Handle abort from both internal and external signals
  const handleAbort = () => {
    aborted = true;
    controller.abort();
  };

  if (externalSignal) {
    externalSignal.addEventListener("abort", handleAbort);
  }

  const makeRequest = async () => {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method,
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
          ...(typeof window !== "undefined" && { 
            Authorization: `Bearer ${localStorage.getItem("auth_token")}` 
          }),
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`SSE error: ${response.status} ${response.statusText}`);
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
          onComplete?.();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        
        // Process complete lines
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine) continue;

          // Handle event type
          if (trimmedLine.startsWith("event: ")) {
            const eventType = trimmedLine.slice(7).trim();
            continue; // Wait for data line
          }

          const data = parseSSEData(trimmedLine);
          if (data) {
            // Handle JSON or plain text
            try {
              const parsed = JSON.parse(data);
              onMessage?.({
                type: parsed.type || "message",
                data: parsed,
              });
            } catch {
              // Plain text message
              onMessage?.({
                type: "message",
                data: { content: data },
              });
            }
          }
        }
      }
    } catch (error) {
      if (aborted) {
        // Clean abort, not an error
        return;
      }
      onError?.(error instanceof Error ? error : new Error(String(error)));
    }
  };

  makeRequest();

  return {
    abort: handleAbort,
  };
}

/**
 * Stream text response with chunk callbacks
 */
export function streamText(
  endpoint: string,
  options: {
    onChunk?: (chunk: string) => void;
    onComplete?: (fullText: string) => void;
    onError?: (error: Error) => void;
    headers?: Record<string, string>;
    body?: any;
    method?: "GET" | "POST";
    signal?: AbortSignal;
  } = {}
): { abort: () => void } {
  let fullText = "";

  return createSSEConnection(endpoint, {
    ...options,
    onMessage: (message) => {
      if (message.type === "content" || message.type === "chunk") {
        const content = message.data.content || message.data.chunk || message.data;
        fullText += content;
        options.onChunk?.(content);
      } else if (message.type === "done" || message.type === "complete") {
        options.onComplete?.(fullText);
      }
    },
    onError: options.onError,
    onComplete: () => options.onComplete?.(fullText),
    body: options.body,
    method: options.method,
    signal: options.signal,
  });
}

/**
 * Chat streaming specialized function
 */
export function streamChat(
  params: {
    content: string;
    workspace_id?: string;
    session_id?: string;
    context_filters?: {
      documents?: string[];
      memories?: string[];
    };
  },
  callbacks: {
    onChunk?: (chunk: string) => void;
    onComplete?: (fullMessage: string) => void;
    onSources?: (sources: any[]) => void;
    onError?: (error: Error) => void;
  }
): { abort: () => void } {
  let fullMessage = "";
  let sources: any[] = [];

  return createSSEConnection("/api/v1/chat", {
    method: "POST",
    body: {
      content: params.content,
      workspace_id: params.workspace_id,
      session_id: params.session_id,
      context_filters: params.context_filters,
      stream: true,
    },
    onMessage: (message) => {
      const { type, data } = message;

      if (type === "content" || type === "chunk") {
        const content = data.content || data.chunk || "";
        fullMessage += content;
        callbacks.onChunk?.(content);
      } else if (type === "sources") {
        sources = [...sources, data];
        callbacks.onSources?.(sources);
      } else if (type === "done" || type === "complete") {
        callbacks.onComplete?.(fullMessage);
      }
    },
    onError: callbacks.onError,
    onComplete: () => callbacks.onComplete?.(fullMessage),
  });
}

/**
 * Document processing status stream
 */
export function streamDocumentProcessing(
  documentId: string,
  callbacks: {
    onProgress?: (progress: number, status: string) => void;
    onComplete?: () => void;
    onError?: (error: Error) => void;
  }
): { abort: () => void } {
  return createSSEConnection(`/api/v1/documents/${documentId}/stream`, {
    method: "GET",
    onMessage: (message) => {
      const { data } = message;
      
      if (data.type === "progress") {
        callbacks.onProgress?.(data.progress || 0, data.status || "processing");
      } else if (data.type === "complete") {
        callbacks.onComplete?.();
      } else if (data.type === "error") {
        callbacks.onError?.(new Error(data.message || "Processing failed"));
      }
    },
    onError: callbacks.onError,
    onComplete: callbacks.onComplete,
  });
}

/**
 * Discovery session stream
 */
export function streamDiscovery(
  workspaceId: string,
  callbacks: {
    onInsight?: (insight: any) => void;
    onProgress?: (progress: number, message: string) => void;
    onComplete?: (insights: any[]) => void;
    onError?: (error: Error) => void;
  }
): { abort: () => void } {
  const insights: any[] = [];

  return createSSEConnection("/api/v1/discovery/stream", {
    method: "POST",
    body: { workspace_id: workspaceId },
    onMessage: (message) => {
      const { type, data } = message;

      if (type === "insight") {
        insights.push(data);
        callbacks.onInsight?.(data);
      } else if (type === "progress") {
        callbacks.onProgress?.(data.progress || 0, data.message || "");
      } else if (type === "done" || type === "complete") {
        callbacks.onComplete?.(insights);
      }
    },
    onError: callbacks.onError,
    onComplete: () => callbacks.onComplete?.(insights),
  });
}

/**
 * Simple polling-based fallback for environments where SSE is not supported
 */
export async function pollUntilComplete<T>(
  fetchFn: () => Promise<{ status: "pending" | "complete" | "error"; data?: T; error?: string }>,
  options: {
    interval?: number;
    maxAttempts?: number;
    onProgress?: (attempt: number) => void;
  } = {}
): Promise<T> {
  const { interval = 2000, maxAttempts = 30, onProgress } = options;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    onProgress?.(attempt);

    const result = await fetchFn();

    if (result.status === "complete") {
      if (!result.data) {
        throw new Error(result.error || "Poll completed without data");
      }
      return result.data;
    }

    if (result.status === "error") {
      throw new Error(result.error || "Poll failed");
    }

    await new Promise((resolve) => setTimeout(resolve, interval));
  }

  throw new Error(`Poll timed out after ${maxAttempts} attempts`);
}
