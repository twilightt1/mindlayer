/**
 * TypeScript types for Insight Cards API
 */

export type InsightType = 
  | "connection" 
  | "contradiction" 
  | "evolution" 
  | "pattern" 
  | "gap" 
  | "confirmation" 
  | "synthesis";

export type InsightStatus = 
  | "new" 
  | "shown" 
  | "dismissed" 
  | "saved" 
  | "expired";

export type SurpriseLevel = "low" | "medium" | "high";

export interface InsightSourceDoc {
  document_id: string;
  title: string;
  excerpt: string;
  relevance_score: number;
}

export interface InsightResponse {
  id: string;
  user_id: string;
  title: string;
  insight_type: InsightType;
  summary: string;
  detail: string;
  source_docs: InsightSourceDoc[];
  source_count: number;
  surprise_level: SurpriseLevel;
  confidence: number;
  created_at: string;
  shown_at: string | null;
  dismissed_at: string | null;
  status: InsightStatus;
  helpful: boolean | null;
  feedback_note: string | null;
  shown_count: number;
  relevance_score: number;
  type_emoji: string;
}

export interface InsightListResponse {
  items: InsightResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface InsightGenerateRequest {
  document_ids?: string[];
  focus_topics?: string[];
  max_insights?: number;
}

export interface InsightGenerateResponse {
  insights: InsightResponse[];
  generation_time_ms: number;
  documents_analyzed: number;
  error: string | null;
}

export interface InsightFeedbackRequest {
  helpful: boolean;
  note?: string;
}

export interface InsightRefreshResponse {
  updated_count: number;
  new_insights: InsightResponse[];
  expired_count: number;
}

// Utility type for display
export interface InsightCardDisplay extends InsightResponse {
  displayTitle: string;
  typeColor: string;
  surpriseLabel: string;
  confidencePercent: string;
  timeAgo: string;
}

export const INSIGHT_TYPE_CONFIG: Record<InsightType, { emoji: string; label: string; color: string }> = {
  connection: { emoji: "🔗", label: "Connection", color: "text-blue-400" },
  contradiction: { emoji: "⚡", label: "Contradiction", color: "text-amber-400" },
  evolution: { emoji: "📈", label: "Evolution", color: "text-emerald-400" },
  pattern: { emoji: "🔄", label: "Pattern", color: "text-purple-400" },
  gap: { emoji: "❓", label: "Gap", color: "text-slate-400" },
  confirmation: { emoji: "✅", label: "Confirmation", color: "text-green-400" },
  synthesis: { emoji: "💡", label: "Synthesis", color: "text-yellow-400" },
};

export const SURPRISE_LABELS: Record<SurpriseLevel, string> = {
  low: "Expected",
  medium: "Interesting",
  high: "Surprising",
};
