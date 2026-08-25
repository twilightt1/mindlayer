/**
 * TypeScript types for Discovery API
 */

export interface DocumentNode {
  id: string;
  title: string;
  entity_ids: string[];
  salience: number;
  connection_count: number;
}

export interface RelationshipEdge {
  source_id: string;
  target_id: string;
  relationship_type: string;
  weight: number;
  evidence: string;
}

export interface GraphResponse {
  nodes: DocumentNode[];
  edges: RelationshipEdge[];
}

export type DiscoveryFlowType = 
  | "explore_related"
  | "trace_origin"
  | "find_contradictions"
  | "synthesize"
  | "temporal_journey";

export type DiscoveryStatus = "active" | "completed" | "abandoned";

export interface DiscoverySession {
  id: string;
  user_id: string;
  flow_type: DiscoveryFlowType;
  starting_doc_id: string;
  target_doc_id: string | null;
  path: string[];
  current_step: number;
  connections_found: Connection[];
  status: DiscoveryStatus;
  created_at: string;
  completed_at: string | null;
  steps_taken: number;
  documents_explored: number;
}

export interface Connection {
  from_doc?: string;
  to_doc?: string;
  insight?: string;
  step_goal?: string;
  type?: string;
  title?: string;
  description?: string;
  confidence?: number;
}

export interface DiscoveryStep {
  next_doc_id: string;
  next_doc_title: string;
  reasoning: string;
  insight_preview: string;
  step_goal: string;
  is_complete: boolean;
}

export interface CrossReference {
  source_doc_id: string;
  target_doc_id: string;
  source_excerpt: string;
  target_excerpt: string;
  reference_type: string;
  relevance_score: number;
}

export interface DiscoveryInsight {
  title: string;
  description: string;
  related_doc_ids: string[];
  insight_type: string;
  confidence: number;
  evidence: string[];
}

export interface GraphMetrics {
  total_nodes: number;
  total_edges: number;
  avg_connections_per_node: number;
  edge_type_distribution: Record<string, number>;
  avg_edge_weight: number;
  graph_density: number;
}

export interface SessionListResponse {
  items: DiscoverySession[];
  total: number;
  limit: number;
  offset: number;
}

export interface DiscoveryGenerateRequest {
  starting_doc_id: string;
  flow_type: DiscoveryFlowType;
  target_doc_id?: string;
}

// Flow type labels
export const FLOW_TYPE_CONFIG: Record<DiscoveryFlowType, { label: string; emoji: string; description: string }> = {
  explore_related: {
    label: "Explore Related",
    emoji: "🔍",
    description: "Discover documents connected to your starting point",
  },
  trace_origin: {
    label: "Trace Origin",
    emoji: "📜",
    description: "Follow the chain of where ideas came from",
  },
  find_contradictions: {
    label: "Find Contradictions",
    emoji: "⚡",
    description: "Find conflicting information across documents",
  },
  synthesize: {
    label: "Synthesize",
    emoji: "💡",
    description: "Build a comprehensive understanding",
  },
  temporal_journey: {
    label: "Temporal Journey",
    emoji: "⏰",
    description: "Trace how thinking evolved over time",
  },
};
