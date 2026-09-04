# Onboarding Flow Documentation

## Overview

Orivory has a sophisticated onboarding system designed to guide users through key features with contextual tours and progressive discovery. This document describes the current flow, identifies friction points, and proposes improvements for a streamlined 3-step onboarding experience.

---

## Current Onboarding Architecture

### Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `OnboardingProvider` | `frontend/src/components/onboarding/OnboardingProvider.tsx` | State management for tour progress |
| `useOnboardingTour` | `frontend/src/components/onboarding/useOnboardingTour.ts` | Hook for tour lifecycle management |
| `presetTours` | `frontend/src/components/onboarding/presetTours.ts` | Tour step definitions |
| `AuthProvider` | `frontend/src/components/auth/AuthProvider.tsx` | Handles post-auth navigation |

### Available Tours

1. **Dashboard Tour** (`dashboard`) - 6 steps
   - Welcome, Quick Capture, Discovery, Insights, Search, Sources

2. **Discovery Tour** (`discovery`) - 4 steps
   - Graph View, Session Start, Flow Types, References

3. **Insights Tour** (`insights`) - 4 steps
   - Overview, Filters, Generate, Actions

4. **Workspaces Tour** (`workspaces`) - 3 steps
   - Header, Create, Invite Members

5. **Sources Tour** (`sources`) - 3 steps
   - Header, Add Source, Sync Status

### Data Flow

```
User Registration/Login
         │
         ▼
   AuthProvider checks tour state
         │
         ▼
   Auto-start Dashboard Tour (1.5s delay)
         │
         ▼
   User completes/skips tour
         │
         ▼
   Tour progress stored in localStorage
   Key: "Orivory_tours_completed"
```

---

## Current Flow Analysis

### Strengths ✅

1. **Comprehensive feature coverage** - All major features have dedicated tours
2. **Progressive disclosure** - Tours auto-start one at a time
3. **Persistent state** - Completed tours remembered in localStorage
4. **Target-based positioning** - Tours highlight specific UI elements
5. **Multiple entry points** - Users can restart tours from settings

### Friction Points ❌

| Issue | Location | Impact | Priority |
|-------|----------|--------|----------|
| Auto-start delay feels intrusive | `useOnboardingTour.ts:118` | Users may dismiss before understanding value | HIGH |
| Tour steps are too granular (20 total) | `presetTours.ts` | Overwhelming for new users | HIGH |
| No quick-win confirmation | Throughout | Users don't feel progress | MEDIUM |
| No value proposition first | Dashboard header | "What can this do for me?" | HIGH |
| Sources require external OAuth | Sources Tour | Blocking setup step | MEDIUM |
| No skip-all option | Throughout | Forces commitment | LOW |
| Mobile tour experience unclear | All tours | Mobile users may miss tours | LOW |

---

## Proposed Simplified 3-Step Onboarding

### Philosophy

> "Show value in 60 seconds, unlock power over time"

The new onboarding prioritizes:
1. **Value demonstration** before feature explanation
2. **Optional setup** - sources can be added later
3. **Immediate utility** - capture something in <10 seconds

### New Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    STEP 1: Value First                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Quick Capture Demo (5 seconds)                       │   │
│  │  "Watch how Orivory learns from this note..."        │   │
│  │  [Animated example of automatic categorization]      │   │
│  └─────────────────────────────────────────────────────┘   │
│  CTA: "Try it yourself" or "Skip, I'll explore"             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    STEP 2: First Capture                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  "Capture anything on your mind"                     │   │
│  │  [Large text area with placeholder hints]            │   │
│  │  • "Meeting notes", "Article to read", "Idea"        │   │
│  └─────────────────────────────────────────────────────┘   │
│  Validation: "Saved! Orivory is analyzing..."               │
│  Skip option: "I'll add memories later"                      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    STEP 3: Connect (Optional)                │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐                 │
│  │  Gmail    │  │  Notion   │  │  Drive    │   ...          │
│  │   ⭐      │  │   ⭐      │  │   ⭐      │                 │
│  └───────────┘  └───────────┘  └───────────┘                 │
│  "Connect one to start, or explore on your own"             │
│  [Skip to Dashboard]                                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Onboarding Complete!                      │
│  Dashboard with:                                            │
│  • First memory card visible                                 │
│  • "Guided Tour Available" banner (dismissible)              │
│  • Feature hints for underutilized areas                     │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Notes

#### Step 1: Value Demo (5 seconds)

```tsx
// New component: QuickDemoOnboarding
// Location: frontend/src/components/onboarding/QuickDemoOnboarding.tsx

interface QuickDemoProps {
  onComplete: () => void;
  onSkip: () => void;
}

// Shows animated GIF/video of:
// 1. User types a note
// 2. Orivory automatically extracts entities
// 3. Memory is categorized and linked
// Duration: Auto-advances after 5s or on click
```

#### Step 2: First Capture

```tsx
// Enhanced QuickCapture with onboarding context
// Location: frontend/src/components/onboarding/FirstCaptureOnboarding.tsx

interface FirstCaptureProps {
  onComplete: (content: string) => void;
  onSkip: () => void;
}

// Validation rules:
// - Min 10 characters (real content, not test)
// - Shows success animation on save
// - Captures first memory timestamp for analytics
```

#### Step 3: Connect Sources (Optional)

```tsx
// Simplified source cards with OAuth status
// Location: frontend/src/components/onboarding/ConnectSourcesOnboarding.tsx

interface ConnectSourcesProps {
  onSourceConnected: (sourceType: string) => void;
  onSkip: () => void;
}

// Only show 3-4 most popular sources
// Full source list available in Settings
// Each card shows: icon, name, connection count
```

---

## Feature Discovery Hints (Post-Onboarding)

After initial onboarding, use contextual hints to guide users:

### Hint Schema

```typescript
interface FeatureHint {
  id: string;
  feature: string;          // 'discovery' | 'insights' | 'sources' | etc.
  trigger: HintTrigger;    // When to show
  content: string;          // Hint text
  action?: HintAction;      // Optional CTA
  dismissible: boolean;
  priority: 'high' | 'medium' | 'low';
}

type HintTrigger = 
  | { type: 'time_on_page'; seconds: number }
  | { type: 'action_count'; action: string; count: number }
  | { type: 'feature_untouched'; days: number }
  | { type: 'recurring'; interval: string; maxTimes: number };
```

### Hint Examples

| Hint | Trigger | Content |
|------|---------|---------|
| Discovery | 3+ memories, not used | "Your memories are connecting. Discover hidden patterns →" |
| Sources | New user, 7 days | "Connect Gmail to auto-import important emails" |
| Search | Typed 5+ queries | "Try natural language: 'Show me notes from last week's meetings'" |
| Insights | 20+ memories | "New insights available! AI found 3 connections →" |

---

## Migration Plan

### Phase 1: Preserve Existing (No Breaking Changes)

1. Add new `QuickDemoOnboarding` component
2. Add new onboarding state: `'quick-demo' | 'first-capture' | 'connect-sources' | 'complete'`
3. Conditionally show new flow based on `users.show_new_onboarding` feature flag

### Phase 2: Gradual Rollout

1. Enable new flow for 10% of new users
2. Collect analytics on completion rates
3. Iterate based on data

### Phase 3: Full Rollout

1. Enable for all new users
2. Keep old tours available in Help menu
3. Deprecate auto-start behavior

---

## Analytics to Track

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Onboarding completion rate | N/A | >70% | Users who complete all 3 steps |
| Time to first memory | N/A | <30s | From registration to first capture |
| Sources connected in onboarding | N/A | >30% | At least 1 source during onboarding |
| 7-day retention (onboarded) | N/A | >60% | Return within 7 days |
| Feature adoption (discovery) | N/A | >40% | Used within 14 days |

---

## Files to Create/Modify

### New Files

| File | Purpose |
|------|---------|
| `frontend/src/components/onboarding/QuickDemoOnboarding.tsx` | Step 1: Value demo |
| `frontend/src/components/onboarding/FirstCaptureOnboarding.tsx` | Step 2: First capture |
| `frontend/src/components/onboarding/ConnectSourcesOnboarding.tsx` | Step 3: Connect sources |
| `frontend/src/components/onboarding/EnhancedOnboardingFlow.tsx` | Orchestrates 3-step flow |
| `app/schemas/hint.py` | Feature hint schema |
| `app/api/v1/hints.py` | Hint interaction API |

### Modified Files

| File | Change |
|------|--------|
| `frontend/src/components/onboarding/OnboardingProvider.tsx` | Add new states |
| `frontend/src/components/auth/AuthProvider.tsx` | Route to new flow |
| `app/models/user.py` | Add `onboarding_completed` flag |
| `app/api/v1/onboarding.py` | Track onboarding events |

---

## Appendix: Current Tour Data Structure

```typescript
interface OnboardingStep {
  id: string;
  target: string;           // CSS selector for highlight
  title: string;
  description: string;
  placement: 'top' | 'bottom' | 'left' | 'right';
}

interface Tour {
  id: string;
  steps: OnboardingStep[];
  autoStart?: boolean;
  triggerConditions?: TriggerCondition[];
}
```

---

## Appendix: LocalStorage Schema

```json
{
  "Orivory_tours_completed": {
    "completedTours": ["dashboard", "discovery"],
    "stepProgress": {
      "dashboard": {
        "welcome": true,
        "quick-capture": true,
        // ...
      }
    }
  }
}
```

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-15 | Claude | Initial documentation |
