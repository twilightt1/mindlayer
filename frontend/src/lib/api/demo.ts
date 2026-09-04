/**
 * API client for Demo/Onboarding
 */

import { apiClient } from "@/lib/api-client";

export interface DemoSeedResponse {
  success: boolean;
  memory_count?: number;
  memory_titles?: string[];
  message: string;
}

export interface DemoStatusResponse {
  has_memories: boolean;
  has_demo_data: boolean;
}

export interface DemoPersona {
  id: string;
  name: string;
  description: string;
  emoji: string;
  memory_count: number;
}

export const DEMO_PERSONAS: DemoPersona[] = [
  {
    id: "professional",
    name: "Professional",
    description: "Marketing campaigns, product meetings, research",
    emoji: "💼",
    memory_count: 8,
  },
  {
    id: "creator",
    name: "Creator",
    description: "Book notes, creative projects, learning",
    emoji: "🎨",
    memory_count: 8,
  },
  {
    id: "researcher",
    name: "Researcher",
    description: "Technical docs, API notes, competitive analysis",
    emoji: "🔬",
    memory_count: 8,
  },
];

export async function seedDemoData(): Promise<DemoSeedResponse> {
  return apiClient.post<DemoSeedResponse>("/api/v1/demo/seed", {});
}

export async function getDemoStatus(): Promise<DemoStatusResponse> {
  return apiClient.get<DemoStatusResponse>("/api/v1/demo/status");
}
