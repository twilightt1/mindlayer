"use client";

import { OnboardingStep } from "./OnboardingProvider";

// Main dashboard tour
export const DASHBOARD_TOUR_ID = "dashboard";
export const DASHBOARD_TOUR_STEPS: OnboardingStep[] = [
  {
    id: "welcome",
    target: "[data-onboarding='dashboard-header']",
    title: "Welcome to MindLayer! 🎉",
    description: "Your AI-powered second brain. This quick tour will show you the key features.",
    placement: "bottom",
  },
  {
    id: "quick-capture",
    target: "[data-onboarding='quick-capture']",
    title: "Quick Capture",
    description: "Instantly capture thoughts, links, or files. They'll be automatically organized.",
    placement: "bottom",
  },
  {
    id: "discovery",
    target: "[data-onboarding='discovery-tab']",
    title: "Discover Connections",
    description: "Let AI find hidden relationships between your memories and surface insights.",
    placement: "bottom",
  },
  {
    id: "insights",
    target: "[data-onboarding='insights-tab']",
    title: "Proactive Insights",
    description: "AI proactively surfaces patterns and connections you might have missed.",
    placement: "bottom",
  },
  {
    id: "search",
    target: "[data-onboarding='search-bar']",
    title: "Semantic Search",
    description: "Ask questions in natural language. MindLayer understands context, not just keywords.",
    placement: "bottom",
  },
  {
    id: "sources",
    target: "[data-onboarding='sources-tab']",
    title: "Connected Sources",
    description: "Connect Gmail, Notion, Google Drive and more for automatic import.",
    placement: "top",
  },
];

// Discovery feature tour
export const DISCOVERY_TOUR_ID = "discovery";
export const DISCOVERY_TOUR_STEPS: OnboardingStep[] = [
  {
    id: "graph-view",
    target: "[data-onboarding='graph-visualization']",
    title: "Knowledge Graph",
    description: "Visualize how your memories connect. The closer nodes are, the more related they are.",
    placement: "right",
  },
  {
    id: "session-start",
    target: "[data-onboarding='start-discovery']",
    title: "Start a Journey",
    description: "Choose a starting document and let AI guide you through related content.",
    placement: "left",
  },
  {
    id: "session-types",
    target: "[data-onboarding='flow-type-selector']",
    title: "Exploration Modes",
    description: "Different ways to explore: trace origins, find contradictions, or synthesize ideas.",
    placement: "top",
  },
  {
    id: "references",
    target: "[data-onboarding='cross-references']",
    title: "Cross-Document References",
    description: "See exactly how one document relates to another with highlighted excerpts.",
    placement: "left",
  },
];

// Insights feature tour
export const INSIGHTS_TOUR_ID = "insights";
export const INSIGHTS_TOUR_STEPS: OnboardingStep[] = [
  {
    id: "insights-overview",
    target: "[data-onboarding='insights-header']",
    title: "Your AI Insights",
    description: "Patterns and connections discovered across your knowledge base.",
    placement: "bottom",
  },
  {
    id: "insight-types",
    target: "[data-onboarding='insight-type-filter']",
    title: "Filter by Type",
    description: "See connections, contradictions, evolutions, patterns, and more.",
    placement: "bottom",
  },
  {
    id: "generate-insights",
    target: "[data-onboarding='generate-insights']",
    title: "Generate New Insights",
    description: "Click to trigger AI analysis of your recent memories for new discoveries.",
    placement: "bottom",
  },
  {
    id: "save-dismiss",
    target: "[data-onboarding='insight-actions']",
    title: "Save or Dismiss",
    description: "Save valuable insights or dismiss ones that aren't relevant.",
    placement: "top",
  },
];

// Workspaces tour
export const WORKSPACES_TOUR_ID = "workspaces";
export const WORKSPACES_TOUR_STEPS: OnboardingStep[] = [
  {
    id: "workspaces-header",
    target: "[data-onboarding='workspaces-header']",
    title: "Team Workspaces",
    description: "Share knowledge with your team in collaborative workspaces.",
    placement: "bottom",
  },
  {
    id: "create-workspace",
    target: "[data-onboarding='create-workspace']",
    title: "Create a Workspace",
    description: "Start a personal or team workspace to organize shared knowledge.",
    placement: "bottom",
  },
  {
    id: "invite-members",
    target: "[data-onboarding='invite-members']",
    title: "Invite Team Members",
    description: "Add colleagues with different permission levels: admin, editor, or viewer.",
    placement: "left",
  },
];

// Sources/connectors tour
export const SOURCES_TOUR_ID = "sources";
export const SOURCES_TOUR_STEPS: OnboardingStep[] = [
  {
    id: "sources-header",
    target: "[data-onboarding='sources-header']",
    title: "Connected Sources",
    description: "Connect your apps and services for automatic memory capture.",
    placement: "bottom",
  },
  {
    id: "add-source",
    target: "[data-onboarding='add-source']",
    title: "Add a Source",
    description: "Connect Gmail, Notion, Google Drive, web clips, and more.",
    placement: "bottom",
  },
  {
    id: "source-sync",
    target: "[data-onboarding='sync-status']",
    title: "Sync Status",
    description: "Monitor when each source was last synced and the items imported.",
    placement: "top",
  },
];

// All available tours
export const ALL_TOURS = {
  [DASHBOARD_TOUR_ID]: DASHBOARD_TOUR_STEPS,
  [DISCOVERY_TOUR_ID]: DISCOVERY_TOUR_STEPS,
  [INSIGHTS_TOUR_ID]: INSIGHTS_TOUR_STEPS,
  [WORKSPACES_TOUR_ID]: WORKSPACES_TOUR_STEPS,
  [SOURCES_TOUR_ID]: SOURCES_TOUR_STEPS,
};

export const TOUR_LABELS: Record<string, string> = {
  [DASHBOARD_TOUR_ID]: "Dashboard Tour",
  [DISCOVERY_TOUR_ID]: "Discovery Tour",
  [INSIGHTS_TOUR_ID]: "Insights Tour",
  [WORKSPACES_TOUR_ID]: "Workspaces Tour",
  [SOURCES_TOUR_ID]: "Sources Tour",
};
