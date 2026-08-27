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
 * Send a chat message and receive a streaming response
 */
export async function sendChatMessage(
  params: SendMessageParams,
  onChunk: (chunk: string) => void,
  onComplete?: (fullMessage: string) => void,
  onError?: (error: Error) => void
): Promise<string> {
  let fullMessage = "";
  
  const stream = createSSEStream(
    "/api/v1/chat",
    {
      onChunk: (data: any) => {
        if (data.type === "content" || data.content) {
          const content = data.content || data.chunk || "";
          fullMessage += content;
          onChunk(content);
        }
      },
      onComplete: () => {
        onComplete?.(fullMessage);
      },
      onError: (error: any) => {
        onError?.(error);
      },
    },
    {
      content: params.content,
      workspace_id: params.workspace_id,
      session_id: params.session_id,
      context_filters: params.context_filters,
    }
  );

  return stream as any;
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
