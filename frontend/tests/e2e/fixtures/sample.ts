// Sample data fixtures for E2E tests

export const mockInsight = {
  id: 'insight-1',
  title: 'Revenue increased 25% YoY',
  description: 'Based on analysis of Q1-Q2 financial documents',
  type: 'trend' as const,
  confidence: 0.92,
  created_at: '2025-08-20T10:00:00Z',
  sources: [
    { document_id: 'doc-1', chunk_id: 'chunk-1' }
  ],
  user_feedback: null,
};

export const mockDiscoveryFlow = {
  id: 'flow-1',
  name: 'Product Roadmap Analysis',
  flow_type: 'related_docs' as const,
  steps: [
    { 
      id: 'step-1', 
      query: 'What is our product roadmap for Q3?',
      documents: ['doc-1', 'doc-2'],
      answer: 'Based on documents...'
    }
  ],
  created_at: '2025-08-21T14:00:00Z',
};

export const mockWorkspace = {
  id: 'ws-1',
  name: 'Marketing Team',
  description: 'Shared workspace for marketing documents',
  owner_id: 'user-1',
  permissions: {
    default_role: 'viewer' as const,
  },
  created_at: '2025-08-15T09:00:00Z',
};

export const mockMember = {
  id: 'member-1',
  user_id: 'user-2',
  workspace_id: 'ws-1',
  role: 'editor' as const,
  joined_at: '2025-08-16T10:00:00Z',
};

export const filterOptions = {
  types: ['trend', 'anomaly', 'comparison', 'correlation', 'summary', 'recommendation', 'risk'],
  sortOptions: ['newest', 'oldest', 'relevance', 'confidence'],
  dateRange: ['7d', '30d', '90d', 'all'],
};

export const flowTypes = [
  { id: 'related_docs', label: 'Related Documents' },
  { id: 'timeline', label: 'Timeline View' },
  { id: 'comparison', label: 'Compare Documents' },
  { id: 'impact', label: 'Impact Analysis' },
  { id: 'custom', label: 'Custom Query' },
];

export const workspaceRoles = [
  { id: 'owner', label: 'Owner', canManage: true, canEdit: true, canDelete: true },
  { id: 'admin', label: 'Admin', canManage: true, canEdit: true, canDelete: false },
  { id: 'editor', label: 'Editor', canManage: false, canEdit: true, canDelete: false },
  { id: 'viewer', label: 'Viewer', canManage: false, canEdit: false, canDelete: false },
];
