"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Sparkles, Lightbulb, GitBranch, Clock, Loader2, Bell, BellOff, CheckCircle } from "lucide-react";

interface ProactiveInsightsWidgetProps {
  className?: string;
  onTrigger?: () => void;
}

const INSIGHT_TRIGGERS = [
  { id: "connection", label: "New Connection", description: "Find unexpected relationships", icon: GitBranch, color: "violet" },
  { id: "pattern", label: "Pattern Detected", description: "Discover recurring themes", icon: Sparkles, color: "amber" },
  { id: "resurfacing", label: "Memory Resurfacing", description: "Rediscover past insights", icon: Clock, color: "emerald" },
  { id: "recommendation", label: "Recommendation", description: "Get AI suggestions", icon: Lightbulb, color: "blue" },
];

const COLOR_CLASSES: Record<string, { bg: string; border: string; icon: string; hover: string }> = {
  violet: { bg: "bg-violet-500/10", border: "border-violet-500/20", icon: "text-violet-400", hover: "hover:bg-violet-500/20" },
  amber: { bg: "bg-amber-500/10", border: "border-amber-500/20", icon: "text-amber-400", hover: "hover:bg-amber-500/20" },
  emerald: { bg: "bg-emerald-500/10", border: "border-emerald-500/20", icon: "text-emerald-400", hover: "hover:bg-emerald-500/20" },
  blue: { bg: "bg-blue-500/10", border: "border-blue-500/20", icon: "text-blue-400", hover: "hover:bg-blue-500/20" },
};

export function ProactiveInsightsWidget({ className, onTrigger }: ProactiveInsightsWidgetProps) {
  const [loading, setLoading] = useState<string | null>(null);
  const [triggered, setTriggered] = useState<string | null>(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);

  const handleTrigger = useCallback(async (id: string) => {
    setLoading(id);
    try {
      const response = await fetch("/api/v1/insights/generate", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ max_insights: 3 }),
      });
      if (response.ok) {
        setTriggered(id);
        setTimeout(() => setTriggered(null), 2000);
        onTrigger?.();
      }
    } catch (err) {
      console.error("Failed to generate insights:", err);
    } finally {
      setLoading(null);
    }
  }, [onTrigger]);

  const toggleNotifications = useCallback(() => {
    setNotificationsEnabled(!notificationsEnabled);
    if (!notificationsEnabled && "Notification" in window) {
      Notification.requestPermission();
    }
  }, [notificationsEnabled]);

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium">Proactive Insights</span>
        </div>
        <button
          onClick={toggleNotifications}
          className={cn(
            "p-2 rounded-lg transition-colors",
            notificationsEnabled ? "bg-primary/20 text-primary" : "bg-white/5 text-white/40 hover:text-white/60 hover:bg-white/10"
          )}
        >
          {notificationsEnabled ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
        </button>
      </div>

      <p className="text-xs text-muted-foreground">
        Get AI-powered insights delivered proactively. Click below or enable notifications.
      </p>

      <div className="grid grid-cols-2 gap-2">
        {INSIGHT_TRIGGERS.map((trigger) => {
          const colors = COLOR_CLASSES[trigger.color];
          const isLoading = loading === trigger.id;
          const isTriggered = triggered === trigger.id;
          const Icon = trigger.icon;

          return (
            <motion.button
              key={trigger.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handleTrigger(trigger.id)}
              disabled={isLoading}
              className={cn("relative p-3 rounded-xl border text-left transition-all overflow-hidden", colors.bg, colors.border, colors.hover)}
            >
              <div className="flex items-center gap-2 mb-2">
                {isLoading ? (
                  <Loader2 className={cn("w-4 h-4 animate-spin", colors.icon)} />
                ) : isTriggered ? (
                  <CheckCircle className={cn("w-4 h-4", colors.icon)} />
                ) : (
                  <Icon className={cn("w-4 h-4", colors.icon)} />
                )}
                <span className={cn("text-xs font-medium", colors.icon)}>{trigger.label}</span>
              </div>
              <p className="text-xs text-white/40">{trigger.description}</p>
              {isTriggered && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="absolute inset-0 bg-emerald-500/20 flex items-center justify-center">
                  <span className="text-xs text-emerald-400 font-medium">Done!</span>
                </motion.div>
              )}
            </motion.button>
          );
        })}
      </div>

      {notificationsEnabled && (
        <div className="flex items-center gap-2 text-xs text-white/40">
          <Bell className="w-3 h-3" />
          <span>You'll be notified when new insights are found</span>
        </div>
      )}
    </div>
  );
}
