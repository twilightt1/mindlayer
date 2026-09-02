"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/components/auth/AuthProvider";
import { useToast } from "@/components/ui/Toast";
import {
  Brain,
  FileText,
  MessageSquare,
  Sparkles,
  Upload,
  ArrowRight,
  ArrowLeft,
  X,
  Check,
  Lightbulb,
  Zap,
  Shield
} from "lucide-react";
import { cn } from "@/lib/utils";
import { DemoSelector } from "./DemoSelector";

// ============================================================================
// TYPES
// ============================================================================

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  icon: React.ElementType;
  action?: {
    label: string;
    href?: string;
  };
}

const STEPS: OnboardingStep[] = [
  {
    id: "welcome",
    title: "Welcome to Orivory!",
    description: "Your AI-powered second brain that transforms scattered information into unified knowledge.",
    icon: Brain,
  },
  {
    id: "documents",
    title: "Upload Your Documents",
    description: "Connect your notes, PDFs, articles, and more. We'll extract and organize the key information.",
    icon: FileText,
    action: { label: "Upload Documents", href: "/documents" },
  },
  {
    id: "chat",
    title: "Ask Anything",
    description: "Chat with your knowledge base using natural language. Get instant, cited answers.",
    icon: MessageSquare,
    action: { label: "Start Chatting", href: "/chat" },
  },
  {
    id: "memories",
    title: "Discover Connections",
    description: "Watch as AI reveals hidden relationships between your ideas and documents.",
    icon: Sparkles,
    action: { label: "Explore Memories", href: "/memories" },
  },
  {
    id: "ready",
    title: "You're All Set!",
    description: "Start exploring and let your second brain grow with you.",
    icon: Zap,
  },
];

// ============================================================================
// COMPONENT
// ============================================================================

export function FirstTimeOnboarding() {
  const { user, completeOnboarding } = useAuth();
  const { success } = useToast();
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [completing, setCompleting] = useState(false);
  const [showDemoSelector, setShowDemoSelector] = useState(false);

  // Check if user has completed onboarding
  useEffect(() => {
    const hasSeenOnboarding = localStorage.getItem("orivory_onboarding_completed");
    const needsOnboarding = user && !user.onboarding_done && !hasSeenOnboarding;

    if (needsOnboarding) {
      setIsOpen(true);
      // Show demo selector first instead of steps
      setShowDemoSelector(true);
    }
  }, [user]);

  const handleComplete = async () => {
    setCompleting(true);
    try {
      // Backend gates all authenticated endpoints behind onboarding_done —
      // complete it server-side and swap in the full-scope tokens.
      await completeOnboarding(user?.display_name || user?.email?.split("@")[0] || "User");
      localStorage.setItem("orivory_onboarding_completed", "true");
      setIsOpen(false);
      success("You're all set! Let's build your second brain.");
    } catch (error) {
      console.error("Onboarding completion failed:", error);
      // Keep the modal open so the user can retry instead of hitting 403s.
    } finally {
      setCompleting(false);
    }
  };

  const handleSkip = async () => {
    // Skipping still must complete setup server-side, or every API call
    // returns 403 "Please complete account setup."
    try {
      await completeOnboarding(user?.display_name || user?.email?.split("@")[0] || "User");
    } catch {
      // Surface setup state next load if it failed
    }
    localStorage.setItem("orivory_onboarding_completed", "true");
    setIsOpen(false);
  };

  const currentStepData = STEPS[currentStep];
  const Icon = currentStepData.icon;
  const isLastStep = currentStep === STEPS.length - 1;
  const isFirstStep = currentStep === 0;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Demo Selector Modal */}
          {showDemoSelector && (
            <DemoSelector
              onComplete={() => {
                setShowDemoSelector(false);
                // Don't complete onboarding yet - let them explore steps
              }}
              onSkip={() => {
                setShowDemoSelector(false);
              }}
            />
          )}

          {/* Steps Modal */}
          {!showDemoSelector && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            >
              {/* Backdrop */}
              <div className="absolute inset-0" onClick={handleSkip} />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative w-full max-w-lg mx-4"
          >
            <div className="bg-background/95 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="relative px-8 pt-8 pb-6">
                {/* Progress dots */}
                <div className="flex justify-center gap-2 mb-8">
                  {STEPS.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentStep(index)}
                      className={cn(
                        "w-2 h-2 rounded-full transition-all duration-300",
                        index === currentStep
                          ? "w-8 bg-violet-500"
                          : index < currentStep
                          ? "bg-violet-500/50"
                          : "bg-white/20"
                      )}
                    />
                  ))}
                </div>

                {/* Skip button */}
                <button
                  onClick={handleSkip}
                  className="absolute top-4 right-4 p-2 rounded-lg text-white/40 hover:text-white hover:bg-white/5 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>

                {/* Icon */}
                <motion.div
                  key={currentStep}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-violet-500/30 flex items-center justify-center"
                >
                  <Icon className="w-10 h-10 text-violet-400" />
                </motion.div>

                {/* Content */}
                <motion.div
                  key={`title-${currentStep}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="text-center"
                >
                  <h2 className="text-2xl font-bold text-white mb-3">
                    {currentStepData.title}
                  </h2>
                  <p className="text-white/60 leading-relaxed">
                    {currentStepData.description}
                  </p>
                </motion.div>
              </div>

              {/* Footer */}
              <div className="px-8 pb-8 pt-4 border-t border-white/5">
                <div className="flex items-center justify-between">
                  {/* Back */}
                  <button
                    onClick={() => setCurrentStep((s) => Math.max(0, s - 1))}
                    disabled={isFirstStep}
                    className={cn(
                      "flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all",
                      isFirstStep
                        ? "text-white/30 cursor-not-allowed"
                        : "text-white/70 hover:text-white hover:bg-white/5"
                    )}
                  >
                    <ArrowLeft className="w-4 h-4" />
                    Back
                  </button>

                  {/* Progress */}
                  <span className="text-sm text-white/40">
                    {currentStep + 1} of {STEPS.length}
                  </span>

                  {/* Next / Complete */}
                  {isLastStep ? (
                    <motion.button
                      initial={{ scale: 0.95 }}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleComplete}
                      disabled={completing}
                      className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 text-white text-sm font-medium shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 transition-all disabled:opacity-60"
                    >
                      {completing ? "Setting up..." : (
                        <>
                          <Check className="w-4 h-4" />
                          Get Started
                        </>
                      )}
                    </motion.button>
                  ) : (
                    <motion.button
                      initial={{ scale: 0.95 }}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setCurrentStep((s) => s + 1)}
                      className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-white text-sm font-medium transition-all"
                    >
                      Next
                      <ArrowRight className="w-4 h-4" />
                    </motion.button>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
          )}
        </>
      )}
    </AnimatePresence>
  );
}

export default FirstTimeOnboarding;
