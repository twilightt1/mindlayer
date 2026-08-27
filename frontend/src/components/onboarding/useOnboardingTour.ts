"use client";

import { useCallback, useEffect } from "react";
import { useOnboarding, OnboardingStep } from "./OnboardingProvider";
import {
  ALL_TOURS,
  DASHBOARD_TOUR_ID,
  TOUR_LABELS,
} from "./presetTours";

const STORAGE_KEY = "Orivory_tours_completed";

interface TourStatus {
  tourId: string;
  completed: boolean;
  startedAt?: string;
  completedAt?: string;
}

/**
 * Hook to manage onboarding tours
 */
export function useOnboardingTour() {
  const { state, startTour, isStepCompleted } = useOnboarding();

  // Load completed tours from localStorage
  const loadCompletedTours = useCallback((): Set<string> => {
    if (typeof window === "undefined") return new Set();
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        return new Set(data.completedTours || []);
      }
    } catch {
      // Ignore localStorage errors
    }
    return new Set();
  }, []);

  // Save completed tour to localStorage
  const markTourCompleted = useCallback((tourId: string) => {
    try {
      const completed = loadCompletedTours();
      completed.add(tourId);
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ completedTours: Array.from(completed) })
      );
    } catch {
      // Ignore localStorage errors
    }
  }, [loadCompletedTours]);

  // Check if a tour is completed
  const isTourCompleted = useCallback(
    (tourId: string) => {
      return loadCompletedTours().has(tourId);
    },
    [loadCompletedTours]
  );

  // Check if all steps of current tour are completed
  const isAllStepsCompleted = useCallback(() => {
    if (!state.isActive) return false;
    
    const steps = ALL_TOURS[state.currentStep as unknown as string];
    if (!steps) return true; // Unknown tour, consider completed
    
    return steps.every((step: OnboardingStep) => isStepCompleted(step.id));
  }, [state, isStepCompleted]);

  // Start a specific tour
  const startSpecificTour = useCallback(
    (tourId: string) => {
      const steps = ALL_TOURS[tourId];
      if (steps) {
        startTour(tourId, steps);
      }
    },
    [startTour]
  );

  // Start dashboard tour if not completed
  const startDashboardTourIfNeeded = useCallback(() => {
    if (!isTourCompleted(DASHBOARD_TOUR_ID)) {
      startTour(DASHBOARD_TOUR_ID, ALL_TOURS[DASHBOARD_TOUR_ID]);
    }
  }, [isTourCompleted, startTour]);

  // Get list of incomplete tours
  const getIncompleteTours = useCallback(() => {
    const completed = loadCompletedTours();
    return Object.keys(ALL_TOURS).filter((id) => !completed.has(id));
  }, [loadCompletedTours]);

  // Get progress for all tours
  const getTourProgress = useCallback(() => {
    const completed = loadCompletedTours();
    const progress: Record<string, { total: number; completed: number; percentage: number }> = {};
    
    for (const [tourId, steps] of Object.entries(ALL_TOURS)) {
      const completedSteps = steps.filter((s) => isStepCompleted(s.id)).length;
      progress[tourId] = {
        total: steps.length,
        completed: completedSteps,
        percentage: Math.round((completedSteps / steps.length) * 100),
      };
    }
    
    return progress;
  }, [isStepCompleted]);

  return {
    // State
    isActive: state.isActive,
    currentStep: state.currentStep,
    totalSteps: state.totalSteps,
    
    // Actions
    startTour: startSpecificTour,
    startDashboardTourIfNeeded,
    markTourCompleted,
    
    // Checks
    isTourCompleted,
    isStepCompleted,
    isAllStepsCompleted,
    
    // Utilities
    getIncompleteTours,
    getTourProgress,
    tourLabels: TOUR_LABELS,
    availableTours: Object.keys(ALL_TOURS),
  };
}

/**
 * Auto-start dashboard tour for new users
 * Call this in your app's root component
 */
export function useAutoStartTour() {
  const { startDashboardTourIfNeeded, isTourCompleted } = useOnboardingTour();

  useEffect(() => {
    // Check if this is a new user (no tours completed)
    const hasCompletedTours = Object.values({
      dashboard: isTourCompleted("dashboard"),
      discovery: isTourCompleted("discovery"),
      insights: isTourCompleted("insights"),
      workspaces: isTourCompleted("workspaces"),
      sources: isTourCompleted("sources"),
    }).some(Boolean);

    // If no tours completed and user has seen the app for a few seconds
    if (!hasCompletedTours) {
      const timer = setTimeout(() => {
        startDashboardTourIfNeeded();
      }, 1500); // Delay to let the app load

      return () => clearTimeout(timer);
    }
  }, [isTourCompleted, startDashboardTourIfNeeded]);
}
