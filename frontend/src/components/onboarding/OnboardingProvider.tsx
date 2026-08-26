"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

export type OnboardingStep = {
  id: string;
  target: string; // CSS selector or element reference
  title: string;
  description: string;
  placement?: "top" | "bottom" | "left" | "right";
};

interface OnboardingState {
  isActive: boolean;
  currentStep: number;
  completedSteps: Set<string>;
  totalSteps: number;
}

interface OnboardingContextValue {
  state: OnboardingState;
  startTour: (tourId: string, steps: OnboardingStep[]) => void;
  nextStep: () => void;
  prevStep: () => void;
  skipTour: () => void;
  completeTour: () => void;
  isStepCompleted: (stepId: string) => boolean;
  markStepCompleted: (stepId: string) => void;
  getCurrentStep: () => OnboardingStep | null;
  getTourSteps: () => OnboardingStep[];
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null);

// Local storage keys
const STORAGE_KEY = "Orivory_onboarding";

function loadState(): Partial<OnboardingState> {
  if (typeof window === "undefined") return {};
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      return {
        completedSteps: new Set(parsed.completedSteps || []),
      };
    }
  } catch {
    // Ignore localStorage errors
  }
  return {};
}

function saveState(state: Partial<OnboardingState>) {
  if (typeof window === "undefined") return;
  try {
    const data = {
      completedSteps: Array.from(state.completedSteps || new Set()),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    // Ignore localStorage errors
  }
}

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const [tourSteps, setTourSteps] = useState<OnboardingStep[]>([]);
  const [activeTourId, setActiveTourId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(() => {
    const loaded = loadState();
    return loaded.completedSteps || new Set();
  });

  const state: OnboardingState = {
    isActive: activeTourId !== null,
    currentStep,
    completedSteps,
    totalSteps: tourSteps.length,
  };

  const startTour = useCallback((tourId: string, steps: OnboardingStep[]) => {
    setTourSteps(steps);
    setActiveTourId(tourId);
    setCurrentStep(0);
  }, []);

  const nextStep = useCallback(() => {
    const currentStepId = tourSteps[currentStep]?.id;
    if (currentStepId) {
      const newCompleted = new Set(completedSteps);
      newCompleted.add(currentStepId);
      setCompletedSteps(newCompleted);
      saveState({ completedSteps: newCompleted });
    }
    
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep((s) => s + 1);
    } else {
      // Tour complete
      setActiveTourId(null);
    }
  }, [currentStep, tourSteps, completedSteps]);

  const prevStep = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep((s) => s - 1);
    }
  }, [currentStep]);

  const skipTour = useCallback(() => {
    // Mark all steps as completed
    const newCompleted = new Set(completedSteps);
    tourSteps.forEach((step) => newCompleted.add(step.id));
    setCompletedSteps(newCompleted);
    saveState({ completedSteps: newCompleted });
    setActiveTourId(null);
  }, [tourSteps, completedSteps]);

  const completeTour = useCallback(() => {
    // Mark all steps as completed
    const newCompleted = new Set(completedSteps);
    tourSteps.forEach((step) => newCompleted.add(step.id));
    setCompletedSteps(newCompleted);
    saveState({ completedSteps: newCompleted });
    setActiveTourId(null);
  }, [tourSteps, completedSteps]);

  const isStepCompleted = useCallback(
    (stepId: string) => completedSteps.has(stepId),
    [completedSteps]
  );

  const markStepCompleted = useCallback(
    (stepId: string) => {
      const newCompleted = new Set(completedSteps);
      newCompleted.add(stepId);
      setCompletedSteps(newCompleted);
      saveState({ completedSteps: newCompleted });
    },
    [completedSteps]
  );

  const getCurrentStep = useCallback(() => {
    return tourSteps[currentStep] || null;
  }, [tourSteps, currentStep]);

  const getTourSteps = useCallback(() => tourSteps, [tourSteps]);

  return (
    <OnboardingContext.Provider
      value={{
        state,
        startTour,
        nextStep,
        prevStep,
        skipTour,
        completeTour,
        isStepCompleted,
        markStepCompleted,
        getCurrentStep,
        getTourSteps,
      }}
    >
      {children}
    </OnboardingContext.Provider>
  );
}

export function useOnboarding() {
  const context = useContext(OnboardingContext);
  if (!context) {
    throw new Error("useOnboarding must be used within OnboardingProvider");
  }
  return context;
}
