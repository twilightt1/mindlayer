/**
 * Chat API Client
 * Handles streaming chat interactions with the AI backend
 */

import { apiClient, createSSEStream } from "@/lib/api-client";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  sources?: ChatSource[];
}

export interface ChatSource {
  document_id: string;
  title: string;
  snippet: string;
  relevance_score: number;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: Date;
  updated_at: Date;
  message_count: number;
}

export interface SendMessageParams {
  content: string;
  workspace_id?: string;
  session_id?: string;
  context_filters?: {
    documents?: string[];
    memories?: string[];
  };
}

/**
 * Send a chat message and receive a streaming response.
 *
 * Returns `{ promise, abort }`: `promise` resolves when the stream finishes
 * (so callers can keep a loading state alive), `abort` cancels it. The
 * backend emits ONE `token` event carrying the FULL final content (plus
 * status/error events), so every chunk callback receives accumulated text.
 */
export async function sendChatMessage(
  params: SendMessageParams,
  onChunk: (fullSoFar: string) => void,
  onComplete?: (fullMessage: string) => void,
  onError?: (error: Error) => void
): Promise<{ promise: Promise<void>; abort: () => void }> {
  let fullMessage = "";
  let settled = false;
  let resolvePromise: (value: { promise: Promise<void>; abort: () => void }) => void = () => {};
  const outer = new Promise<{ promise: Promise<void>; abort: () => void }>((resolve) => {
    resolvePromise = resolve;
  });

  const stream = createSSEStream(
    "/api/v1/chat",
    {
      onChunk: (data: any) => {
        // Backend event protocol: {type:"token", content:<full text>},
        // {type:"error", message}, {type:"status"|...} (ignored).
        if (data?.type === "error") {
          settled = true;
          onError?.(new Error(data.message || "The server reported an error."));
          return;
        }
        if (data?.type === "token" || data?.type === "content" || data?.content) {
          const content = String(data.content ?? "");
          fullMessage = content; // full snapshot, not a delta
          onChunk(fullMessage);
        }
        if (data?.chunk) {
          // Forward-compat: true delta chunks accumulate.
          fullMessage += data.chunk;
          onChunk(fullMessage);
        }
      },
      onComplete: () => {
        if (!settled) {
          settled = true;
          onComplete?.(fullMessage);
        }
      },
      onError: (error: any) => {
        if (!settled) {
          settled = true;
          onError?.(error instanceof Error ? error : new Error(String(error)));
        }
      },
    },
    {
      content: params.content,
      workspace_id: params.workspace_id,
      session_id: params.session_id,
      context_filters: params.context_filters,
    }
  );

  resolvePromise({ promise: stream.promise, abort: stream.abort });
  return outer;
}

/**
 * Create a new chat session
 */
export async function createChatSession(workspaceId?: string): Promise<ChatSession> {
  return apiClient.post<ChatSession>("/api/v1/chat/sessions", {
    workspace_id: workspaceId,
  });
}

/**
 * List chat sessions
 */
export async function listChatSessions(workspaceId?: string): Promise<ChatSession[]> {
  const params = workspaceId ? `?workspace_id=${workspaceId}` : "";
  return apiClient.get<ChatSession[]>(`/api/v1/chat/sessions${params}`);
}

/**
 * Get chat history for a session
 */
export async function getChatHistory(sessionId: string): Promise<ChatMessage[]> {
  const data = await apiClient.get<{ messages: any[] }>(`/api/v1/chat/sessions/${sessionId}/messages`);
  return data.messages.map((msg: any) => ({
    ...msg,
    timestamp: new Date(msg.timestamp),
  }));
}

/**
 * Delete a chat session
 */
export async function deleteChatSession(sessionId: string): Promise<void> {
  return apiClient.delete(`/api/v1/chat/sessions/${sessionId}`);
}
