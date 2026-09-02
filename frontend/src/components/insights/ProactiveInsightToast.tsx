"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Lightbulb, Sparkles, GitBranch, Clock, X, ChevronRight, Loader2 } from "lucide-react";
import type { InsightResponse } from "@/types/insights";

interface ProactiveInsightToastProps {
  className?: string;
  autoCheckInterval?: number;
  maxToShow?: number;
  onShow?: (insights: InsightResponse[]) => void;
}

const INSIGHT_COLORS: Record<string, { bg: string; border: string; icon: string }> = {
  connection: { bg: "bg-violet-500/10", border: "border-violet-500/30", icon: "text-violet-400" },
  pattern: { bg: "bg-amber-500/10", border: "border-amber-500/30", icon: "text-amber-400" },
  resurfacing: { bg: "bg-emerald-500/10", border: "border-emerald-500/30", icon: "text-emerald-400" },
  contradiction: { bg: "bg-red-500/10", border: "border-red-500/30", icon: "text-red-400" },
  recommendation: { bg: "bg-blue-500/10", border: "border-blue-500/30", icon: "text-blue-400" },
  default: { bg: "bg-white/5", border: "border-white/10", icon: "text-white/60" },
};

function InsightIcon({ type, className }: { type: string; className?: string }) {
  const icons: Record<string, React.ReactNode> = {
    connection: <GitBranch className={className} />,
    pattern: <Sparkles className={className} />,
    resurfacing: <Clock className={className} />,
    contradiction: (
      <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    ),
    recommendation: <Lightbulb className={className} />,
  };
  return <>{icons[type] || icons.pattern}</>;
}

export function ProactiveInsightToast({
  className,
  autoCheckInterval = 0,
  maxToShow = 3,
  onShow,
}: ProactiveInsightToastProps) {
  const [insights, setInsights] = useState<InsightResponse[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  const [queuedInsights, setQueuedInsights] = useState<InsightResponse[]>([]);
  const toastTimerRef = useRef<NodeJS.Timeout | null>(null);

  const fetchInsights = useCallback(async () => {
    if (isLoading) return;
    setIsLoading(true);
    try {
      const response = await fetch("/api/v1/insights?status=new&limit=10", {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        const newInsights = (data.items || []).filter(
          (i: InsightResponse) => !dismissed.has(i.id as string)
        );
        const filtered = newInsights.slice(0, maxToShow);
        if (filtered.length > 0) {
          setInsights(filtered);
          setCurrentIndex(0);
          setIsVisible(true);
          onShow?.(filtered);
        }
      }
    } catch (err) {
      console.error("Failed to fetch insights:", err);
    } finally {
      setIsLoading(false);
    }
  }, [dismissed, maxToShow, onShow, isLoading]);

  const showNext = useCallback(() => {
    if (currentIndex < insights.length - 1) {
      setCurrentIndex((i) => i + 1);
    } else {
      setIsVisible(false);
    }
  }, [currentIndex, insights.length]);

  const dismiss = useCallback((id: string) => {
    setDismissed((prev) => new Set([...Array.from(prev), id]));
    if (insights.length <= 1) {
      setIsVisible(false);
    } else {
      showNext();
    }
  }, [insights.length, showNext]);

  const handleSave = async (id: string) => {
    try {
      await fetch(`/api/v1/insights/${id}/save`, {
        method: "POST",
        credentials: "include",
      });
      dismiss(id);
    } catch (err) {
      console.error("Failed to save insight:", err);
    }
  };

  // Auto-check for new insights
  useEffect(() => {
    if (autoCheckInterval <= 0) return;
    fetchInsights();
    const interval = setInterval(fetchInsights, autoCheckInterval);
    return () => clearInterval(interval);
  }, [autoCheckInterval, fetchInsights]);

  // Expose trigger function
  useEffect(() => {
    (window as any).__triggerProactiveInsight = () => {
      fetchInsights();
    };
    return () => {
      delete (window as any).__triggerProactiveInsight;
    };
  }, [fetchInsights]);

  const currentInsight = insights[currentIndex];
  const colors = currentInsight
    ? INSIGHT_COLORS[currentInsight.insight_type] || INSIGHT_COLORS.default
    : INSIGHT_COLORS.default;

  if (!isVisible && !isLoading) return null;

  return (
    <div className={cn("fixed bottom-4 right-4 z-50 max-w-sm", className)}>
      <AnimatePresence mode="wait">
        {isLoading && insights.length === 0 ? (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className={cn(
              "flex items-center gap-3 px-4 py-3 rounded-xl",
              "bg-black/80 border border-white/10 backdrop-blur-xl shadow-2xl"
            )}
          >
            <Loader2 className="w-4 h-4 animate-spin text-white/40" />
            <span className="text-sm text-white/40">Checking insights...</span>
          </motion.div>
        ) : currentInsight ? (
          <motion.div
            key={currentInsight.id}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className={cn(
              "relative overflow-hidden rounded-2xl border backdrop-blur-xl shadow-2xl",
              "bg-black/80",
              colors.border
            )}
          >
            <div className={cn("absolute inset-0 opacity-20", colors.bg)} />

            <div className="relative p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center", colors.bg)}>
                    <InsightIcon type={currentInsight.insight_type} className={cn("w-4 h-4", colors.icon)} />
                  </div>
                  <span className="text-xs text-white/40 uppercase tracking-wider">
                    {currentInsight.insight_type}
                  </span>
                </div>
                <button
                  onClick={() => dismiss(currentInsight.id)}
                  className="p-1 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <X className="w-4 h-4 text-white/40" />
                </button>
              </div>

              <h4 className="font-medium text-white mb-2 pr-6">{currentInsight.title}</h4>
              <p className="text-sm text-white/60 line-clamp-2 mb-3">{currentInsight.summary}</p>

              {currentInsight.source_count > 0 && (
                <div className="flex items-center gap-1 text-xs text-white/40 mb-3">
                  <span>{currentInsight.source_count} source{currentInsight.source_count > 1 ? "s" : ""}</span>
                  <span>•</span>
                  <span>{Math.round((currentInsight.confidence || 0) * 100)}% confidence</span>
                </div>
              )}

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleSave(currentInsight.id)}
                  className={cn(
                    "flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                    "bg-white/10 hover:bg-white/20 text-white"
                  )}
                >
                  Save
                </button>
                <button
                  onClick={showNext}
                  className={cn(
                    "flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                    "border border-white/10 hover:bg-white/5 text-white/60"
                  )}
                >
                  Next
                  <ChevronRight className="w-3 h-3" />
                </button>
              </div>

              {insights.length > 1 && (
                <div className="flex justify-center gap-1 mt-3">
                  {insights.map((_, i) => (
                    <button
                      key={i}
                      onClick={() => setCurrentIndex(i)}
                      className={cn(
                        "h-1.5 rounded-full transition-all",
                        i === currentIndex ? "bg-violet-400 w-4" : "bg-white/20 hover:bg-white/40 w-1.5"
                      )}
                    />
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}

// Hook to trigger proactive insight toast from anywhere
export function useProactiveInsightToast() {
  const trigger = useCallback(() => {
    const fn = (window as any).__triggerProactiveInsight;
    if (fn) fn();
  }, []);

  return { trigger };
}
